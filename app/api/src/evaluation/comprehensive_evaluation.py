"""
Comprehensive Legal AI Evaluation System

This module combines both evaluation approaches:
1. LLM-as-a-Judge for qualitative assessment (GPT-4.1)
2. Traditional NLP/ML metrics for quantitative analysis
3. Processes all test datasets and generates unified reports
4. Outputs both JSON and Markdown comprehensive reports
"""

import os
import sys
import json
import asyncio
import csv
import re
import base64
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set, Tuple
from datetime import datetime
from dotenv import load_dotenv
from collections import Counter

# OpenAI imports
from openai import AsyncOpenAI

# Add the API source directory to the path to import agents
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from app.api.src.agents.routing import create_legal_agent_system
from app.api.src.tools.vector_search import VectorSearch
from app.api.src.tools.web_search import WebSearch

# Load environment variables
load_dotenv()

# Try to import optional dependencies for advanced metrics
try:
    from rouge_score import rouge_scorer
    ROUGE_AVAILABLE = True
except ImportError:
    print("⚠️ rouge-score not available. Install with: pip install rouge-score")
    ROUGE_AVAILABLE = False

try:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    import nltk
    # Download required NLTK data
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    BLEU_AVAILABLE = True
except ImportError:
    print("⚠️ NLTK not available. Install with: pip install nltk")
    BLEU_AVAILABLE = False

class LegalAIJudge:
    """LLM-as-a-Judge implementation using GPT-4.1 for qualitative evaluation"""
    
    def __init__(self, model: str = "gpt-4.1", judge_type: str = "general"):
        # Remove openai: prefix if present
        if model.startswith("openai:"):
            model = model.replace("openai:", "")
            
        self.model = model
        self.judge_type = judge_type
        
        # Set temperature for judge evaluation
        judge_temps = {
            "research": 0.0,
            "summarization": 0.0, 
            "prediction": 0.0,
            "general": 0.1
        }
        self.temperature = judge_temps.get(judge_type, 0.1)
            
        self.client = AsyncOpenAI()
    
    async def evaluate_legal_research(
        self, 
        query: str, 
        answer: str, 
        retrieved_docs: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """LLM-as-a-Judge for legal research quality"""
        
        template = """You are evaluating a legal research output.

The model output must include:
1. A disclaimer in the first paragraph.
2. Structured findings (statutes first, then case law principles).
3. References to the provided or retrieved context.

Evaluate:
- Schema compliance: Does it follow the disclaimer + findings structure?
- Completeness: Does it cover the main legal principles from the retrieved context?
- Relevance: Do the findings directly answer the query?
- Support: Are references clearly linked to the provided documents or context?

Query: {{input}}
Model response: {{output}}
Retrieved documents: {{retrieved_docs}}

Return your evaluation as valid JSON:
{
  "score": <integer 1–5>,
  "reasoning": "<short explanation>",
  "strengths": "<key strengths>",
  "weaknesses": "<areas for improvement>"
}
"""
        
        prompt = (
            template.replace("{{input}}", query)
                    .replace("{{output}}", answer)
                    .replace("{{retrieved_docs}}", str(retrieved_docs[:3] if retrieved_docs else []))
        )

        try:
            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            # Only add temperature if it's not None (GPT-5 doesn't support custom temperature)
            if self.temperature is not None:
                api_params["temperature"] = self.temperature
                
            response = await self.client.chat.completions.create(**api_params)
            
            response_text = response.choices[0].message.content.strip()
            try:
                parsed = json.loads(response_text)
                score = parsed["score"]
                reasoning = parsed.get("reasoning", "")
                strengths = parsed.get("strengths", "")
                weaknesses = parsed.get("weaknesses", "")
                comment = f"Reasoning: {reasoning} | Strengths: {strengths} | Weaknesses: {weaknesses}"
            except:
                # Fallback: extract numeric score
                match = re.search(r"[1-5]", response_text)
                score = float(match.group()) if match else 0.0
                comment = f"Raw response: {response_text}"
            
            return {
                "name": "legal_research_quality",
                "value": float(score),
                "comment": comment
            }
            
        except Exception as e:
            return {
                "name": "legal_research_quality",
                "value": 0.0,
                "comment": f"Evaluation failed: {str(e)}"
            }
    
    async def evaluate_legal_summarization(
        self, 
        document: str, 
        summary: str, 
        reference_summary: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """LLM-as-a-Judge for legal document summarization"""
        
        template = """You are evaluating a legal summarization output.

The model output must include:
1. A **Summarized Document** (~200–300 words).
2. **Key Points** (bullet list).

Evaluate on:
- Schema compliance: Are both required sections present in the model output?
- Clarity: Is the summary easy to read?
- Completeness: Does the output cover the same main ideas as the ground truth?
- Faithfulness: Does the summary align with the ground truth and source case text?

Case text: {{input}}
Model summary: {{output}}
Reference summary: {{expected_output}}

Return your evaluation as valid JSON:
{
  "score": <integer 1–5>,
  "reasoning": "<short explanation>",
  "missing_elements": "<what's missing>",
  "improvements": "<specific suggestions>"
}
"""
        
        prompt = (
            template.replace("{{input}}", document[:1000] + "..." if len(document) > 1000 else document)
                    .replace("{{output}}", summary)
                    .replace("{{expected_output}}", json.dumps(reference_summary, indent=2) if reference_summary else "")
        )

        try:
            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            # Only add temperature if it's not None (GPT-5 doesn't support custom temperature)
            if self.temperature is not None:
                api_params["temperature"] = self.temperature
                
            response = await self.client.chat.completions.create(**api_params)
            
            response_text = response.choices[0].message.content.strip()
            try:
                parsed = json.loads(response_text)
                score = parsed["score"]
                reasoning = parsed.get("reasoning", "")
                missing = parsed.get("missing_elements", "")
                improvements = parsed.get("improvements", "")
                comment = f"Reasoning: {reasoning} | Missing: {missing} | Improvements: {improvements}"
            except:
                match = re.search(r"[1-5]", response_text)
                score = float(match.group()) if match else 0.0
                comment = f"Raw response: {response_text}"
            
            return {
                "name": "legal_summarization_quality",
                "value": float(score),
                "comment": comment
            }
            
        except Exception as e:
            return {
                "name": "legal_summarization_quality",
                "value": 0.0,
                "comment": f"Evaluation failed: {str(e)}"
            }
    
    async def evaluate_legal_prediction(
        self, 
        case_scenario: str, 
        prediction: Dict[str, Any], 
        ground_truth: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """LLM-as-a-Judge for legal case outcome prediction"""
        
        template = """You are evaluating a legal prediction output.

The model output should include sections:
1. Disclaimer
2. Case Scenario Summary
3. Key Legal Issues
4. Predicted Outcome (Disposition, Judgment Type, Remedy, etc.)

Evaluate:
- Schema compliance: Are all required sections included?
- Correctness: Do the predictions match the ground truth outcomes?
- Plausibility: Are the predictions legally reasonable based on the facts?

Case facts: {{input}}
Model prediction: {{output}}
Ground truth: {{expected_output}}

Return your evaluation as valid JSON:
{
  "score": <integer 1–5>,
  "reasoning": "<short explanation>"
}
"""
        
        prompt = (
            template.replace("{{input}}", case_scenario)
                    .replace("{{output}}", json.dumps(prediction, indent=2) if isinstance(prediction, dict) else str(prediction))
                    .replace("{{expected_output}}", json.dumps(ground_truth, indent=2) if ground_truth else "")
        )

        try:
            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            # Only add temperature if it's not None (GPT-5 doesn't support custom temperature)
            if self.temperature is not None:
                api_params["temperature"] = self.temperature
                
            response = await self.client.chat.completions.create(**api_params)
            
            response_text = response.choices[0].message.content.strip()
            try:
                parsed = json.loads(response_text)
                score = parsed["score"]
                reasoning = parsed.get("reasoning", "")
                comment = f"Reasoning: {reasoning}"
            except:
                match = re.search(r"[1-5]", response_text)
                score = float(match.group()) if match else 0.0
                comment = f"Raw response: {response_text}"
            
            return {
                "name": "legal_prediction_quality",
                "value": float(score),
                "comment": comment
            }
            
        except Exception as e:
            return {
                "name": "legal_prediction_quality",
                "value": 0.0,
                "comment": f"Evaluation failed: {str(e)}"
            }

class TraditionalMetrics:
    """Traditional NLP/ML metrics for quantitative evaluation"""
    
    @staticmethod
    def extract_legal_entities(text: str) -> Set[str]:
        """Extract legal entities using comprehensive Malaysian legal patterns"""
        entities = set()
        
        # Enhanced case number patterns
        case_number_patterns = [
            r"GUAMAN\s*NO\s*:?\s*([\w\(\)\-\/\s]+)",
            r"RAYUAN SIVIL NO\.?\s*:?\s*([\w\(\)\-\/\s]+)",  
            r"GUAMAN SIVIL NO\.?\s*:?\s*([\w\(\)\-\/\s]+)",  
            r"CIVIL SUIT NO\.?\s*:?\s*([\w\(\)\-\/\s]+)",
            r"SUIT NO\.?\s*:?\s*([\w\(\)\-\/\s]+)",                  
            r"CIVIL APPEAL NO\.?\s*:?\s*([\w\(\)\-\/\s]+)",
            r"APPEAL NO\.?\s*:?\s*([\w\(\)\-\/\s]+)",
            r'\b\d+[A-Z]+-\d+-\d+\b',
            r'\[\d{4}\]\s+\d+\s+[A-Z]+\s+\d+',
        ]
        
        for pattern in case_number_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.update([match.strip() for match in matches if len(match.strip()) > 2])
        
        # Enhanced court name patterns
        court_patterns = [
            r"DALAM\s+(MAHKAMAH\s+[A-Z\s]+?)(?:\s+DI\s+[A-Z\s]+|\s+DALAM\s+NEGERI|\n|$)",
            r"IN THE\s+((?:FEDERAL COURT|HIGH COURT|COURT OF APPEAL|SESSIONS COURT|MAGISTRATES?[\'\s]*COURT)[^\n]*?)(?:\s+AT\s+[A-Z\s]+)?(?:\n|$)",
            r"IN THE\s+(.*?COURT.*?)(?:\s+AT\s+|\n|$)",
        ]
        
        for pattern in court_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                court_text = match.strip()
                if "COURT" in court_text.upper() or "MAHKAMAH" in court_text.upper():
                    entities.add(court_text)
        
        # Enhanced statutory references
        statute_patterns = [
            r'\bsection\s*\d+(?:\([a-z]\))?(?:\s*of\s*the\s*)?[\w\s]*act\s*\d*\b',
            r'\bs\.\s*\d+(?:\([a-z]\))?(?:\s*of\s*the\s*)?[\w\s]*act\s*\d*\b',
            r'\b(?:article|art\.)\s*\d+\b',
            r'\bcontracts?\s+act\s*\d*\b',
            r'\bevidence\s+act\s*\d*\b',
            r'\bcivil\s+law\s+act\s*\d*\b',
            r'\bcompanies\s+act\s*\d*\b',
            r'\bnational\s+land\s+code\b',
        ]
        
        for pattern in statute_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.update([match.strip() for match in matches])
        
        # More flexible legal concepts
        concept_patterns = [
            r'\b(?:agreement|offer|acceptance|consideration|consent|contract|breach|damages)\b',
            r'\b(?:capacity|competent|lawful\s+object|certainty|performance)\b',
            r'\bfree\s+consent\b',
            r'\blawful\s+(?:consideration|object)\b',
            r'\bvalid\s+contract\b',
            r'\bburden\s+of\s+proof\b',
            r'\bbalance\s+of\s+probabilities\b',
            r'\breasonable\s+doubt\b',
            r'\bprima\s+facie\b',
            r'\bcivil\s+appeal\b',
            r'\bappeal\s+dismissed\b',
            r'\brayuan\s+sivil\b',
        ]
        
        for pattern in concept_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.update([match.strip().lower() for match in matches])
        
        # Filter out serial numbers
        filtered_entities = set()
        for entity in entities:
            if not re.search(r"(?:SIN|S/N)\s+[a-zA-Z0-9]{15,25}", entity, re.IGNORECASE):
                if len(entity) > 2 and entity.lower() not in ['and', 'the', 'of', 'in', 'to', 'a', 'is', 'are']:
                    filtered_entities.add(entity)
        
        return filtered_entities
    
    @staticmethod
    def evaluate_research_retrieval(answer: str, retrieved_docs: List[str], ground_truth: str = "") -> Dict[str, float]:
        """Evaluate research quality using Precision@k and Recall@k"""
        
        answer_entities = TraditionalMetrics.extract_legal_entities(answer)
        retrieved_content = " ".join(retrieved_docs)
        retrieved_entities = TraditionalMetrics.extract_legal_entities(retrieved_content)
        
        # Calculate metrics
        metrics = {}
        for k in [1, 3, 5, 10]:
            retrieved_k = set(list(retrieved_entities)[:k])
            
            if retrieved_k:
                relevant_retrieved = retrieved_k.intersection(answer_entities)
                precision = len(relevant_retrieved) / len(retrieved_k)
                metrics[f"precision_at_{k}"] = precision
            else:
                metrics[f"precision_at_{k}"] = 0.0
            
            if answer_entities:
                relevant_retrieved = retrieved_k.intersection(answer_entities)
                recall = len(relevant_retrieved) / len(answer_entities)
                metrics[f"recall_at_{k}"] = recall
            else:
                metrics[f"recall_at_{k}"] = 0.0
        
        # Additional metrics
        metrics["total_retrieved_entities"] = len(retrieved_entities)
        metrics["total_entities_found"] = len(answer_entities)
        
        if answer_entities and retrieved_entities:
            overlap = answer_entities.intersection(retrieved_entities)
            metrics["entity_overlap_ratio"] = len(overlap) / len(answer_entities.union(retrieved_entities))
        else:
            metrics["entity_overlap_ratio"] = 0.0
        
        return metrics
    
    @staticmethod
    def evaluate_summarization_quality(summary: str, reference_summary: str) -> Dict[str, float]:
        """Evaluate summarization using ROUGE and BLEU scores"""
        metrics = {}
        
        if ROUGE_AVAILABLE and reference_summary:
            try:
                scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
                scores = scorer.score(reference_summary, summary)
                
                metrics["rouge1_f1"] = scores['rouge1'].fmeasure
                metrics["rouge1_precision"] = scores['rouge1'].precision
                metrics["rouge1_recall"] = scores['rouge1'].recall
                metrics["rouge2_f1"] = scores['rouge2'].fmeasure
                metrics["rouge2_precision"] = scores['rouge2'].precision
                metrics["rouge2_recall"] = scores['rouge2'].recall
                metrics["rougeL_f1"] = scores['rougeL'].fmeasure
                metrics["rougeL_precision"] = scores['rougeL'].precision
                metrics["rougeL_recall"] = scores['rougeL'].recall
            except Exception as e:
                print(f"⚠️ ROUGE calculation failed: {e}")
        
        if BLEU_AVAILABLE and reference_summary:
            try:
                # Simple BLEU calculation
                reference_tokens = reference_summary.split()
                candidate_tokens = summary.split()
                
                if reference_tokens and candidate_tokens:
                    smoothing = SmoothingFunction().method1
                    
                    for n in [1, 2, 3, 4]:
                        try:
                            bleu_score = sentence_bleu([reference_tokens], candidate_tokens, 
                                                     weights=tuple([1/n]*n + [0]*(4-n)), 
                                                     smoothing_function=smoothing)
                            metrics[f"bleu_{n}"] = bleu_score
                        except:
                            metrics[f"bleu_{n}"] = 0.0
            except Exception as e:
                print(f"⚠️ BLEU calculation failed: {e}")
        
        return metrics
    
    @staticmethod
    def normalize_disposition(disposition: str) -> str:
        """Normalize disposition values for comparison"""
        disposition_lower = disposition.lower().strip()
        
        # Malaysian terms
        if any(term in disposition_lower for term in ['perayu menang', 'rayuan dibenarkan', 'plaintiff menang']):
            return 'plaintiff_wins'
        elif any(term in disposition_lower for term in ['perayu kalah', 'rayuan ditolak', 'defendant menang']):
            return 'defendant_wins'
        elif any(term in disposition_lower for term in ['appeal dismissed', 'rayuan ditolak']):
            return 'appeal_dismissed'
        elif any(term in disposition_lower for term in ['case dismissed', 'kes ditolak']):
            return 'case_dismissed'
        
        # English terms
        if 'plaintiff wins' in disposition_lower or 'plaintiff successful' in disposition_lower:
            return 'plaintiff_wins'
        elif 'defendant wins' in disposition_lower or 'defendant successful' in disposition_lower:
            return 'defendant_wins'
        elif 'dismissed' in disposition_lower:
            return 'case_dismissed'
        
        return disposition_lower
    
    @staticmethod
    def extract_damages_amount(text: str) -> Optional[float]:
        """Extract damages amount with context-awareness"""
        # Primary patterns for total damages/awards
        primary_patterns = [
            r'(?:total\s+)?damages?\s+(?:awarded|granted|of)\s+rm\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(?:total\s+)?(?:award|sum)\s+of\s+rm\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'compensation\s+of\s+rm\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(?:court\s+)?(?:awarded|grants?)\s+rm\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        ]
        
        # Secondary patterns for general amounts
        secondary_patterns = [
            r'rm\s*(\d+(?:,\d+)*(?:\.\d+)?)',
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*ringgit',
        ]
        
        # Exclusion patterns for rates/fees
        exclusion_patterns = [
            r'(?:daily|monthly|yearly|per\s+day|per\s+month)\s+.*?rm\s*\d+',
            r'rm\s*\d+.*?(?:per\s+day|daily|monthly)',
            r'(?:rental|rent)\s+.*?rm\s*\d+.*?(?:per|daily|monthly)',
        ]
        
        text_lower = text.lower()
        
        # Check for exclusion patterns first
        for pattern in exclusion_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                # If the text only mentions rates/fees, return None
                primary_found = any(re.search(p, text_lower, re.IGNORECASE) for p in primary_patterns)
                if not primary_found:
                    return None
        
        # Try primary patterns first
        for pattern in primary_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                try:
                    amount = float(matches[0].replace(',', ''))
                    return amount
                except:
                    continue
        
        # Try secondary patterns if no primary matches
        for pattern in secondary_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                try:
                    amount = float(matches[0].replace(',', ''))
                    # Only return if it's a significant amount
                    if amount >= 1000:
                        return amount
                except:
                    continue
        
        return None
    
    @staticmethod
    def evaluate_prediction_accuracy(prediction: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate prediction accuracy using classification and regression metrics"""
        metrics = {}
        
        # Disposition accuracy
        if "disposition" in prediction and "disposition" in ground_truth:
            pred_disp = TraditionalMetrics.normalize_disposition(str(prediction["disposition"]))
            true_disp = TraditionalMetrics.normalize_disposition(str(ground_truth["disposition"]))
            metrics["disposition_accuracy"] = 1.0 if pred_disp == true_disp else 0.0
        
        # Judgment type accuracy
        if "judgment_type" in prediction and "judgment_type" in ground_truth:
            pred_judgment = str(prediction["judgment_type"]).lower().strip()
            true_judgment = str(ground_truth["judgment_type"]).lower().strip()
            metrics["judgment_accuracy"] = 1.0 if pred_judgment == true_judgment else 0.0
        
        # Damages MAE
        if "damages_amount" in ground_truth:
            true_damages = ground_truth["damages_amount"]
            if true_damages is not None:
                pred_damages = prediction.get("damages_amount")
                if pred_damages is None and "raw_prediction" in prediction:
                    # Try to extract from raw text
                    pred_damages = TraditionalMetrics.extract_damages_amount(prediction["raw_prediction"])
                
                if pred_damages is not None:
                    try:
                        mae = abs(float(pred_damages) - float(true_damages))
                        metrics["damages_mae"] = mae
                        metrics["damages_percentage_error"] = (mae / float(true_damages)) * 100 if float(true_damages) > 0 else 0
                    except:
                        metrics["damages_mae"] = float('inf')
                        metrics["damages_percentage_error"] = 100.0
                else:
                    metrics["damages_mae"] = float('inf')
                    metrics["damages_percentage_error"] = 100.0
        
        return metrics

class ComprehensiveEvaluationRunner:
    """Unified evaluation runner with both LLM-as-a-Judge and traditional metrics"""
    
    def __init__(self, model_name: str = "gpt-4o"):
        # Remove openai: prefix if present
        if model_name.startswith("openai:"):
            model_name = model_name.replace("openai:", "")
            
        self.model_name = model_name
        
        # Initialize judge-specific instances for different evaluation tasks
        self.research_judge = LegalAIJudge(model="gpt-4.1", judge_type="research")
        self.summarization_judge = LegalAIJudge(model="gpt-4.1", judge_type="summarization") 
        self.prediction_judge = LegalAIJudge(model="gpt-4.1", judge_type="prediction")
        
        self.metrics = TraditionalMetrics()
        self.legal_system = None
        
        # Initialize legal agent system with GPT-4.1
        try:
            self.legal_system = create_legal_agent_system(model_name=model_name)
            print(f"✅ Legal agent system initialized with {model_name}")
        except Exception as e:
            print(f"❌ Failed to initialize legal agent system: {e}")
            
        self.vector = VectorSearch()
        self.web_search = WebSearch()
    
    def load_dataset_from_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """Load dataset from Langfuse-compatible CSV format"""
        dataset = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                item = {}
                for key, value in row.items():
                    try:
                        item[key] = json.loads(value)
                    except json.JSONDecodeError:
                        item[key] = value
                dataset.append(item)
        return dataset
    
    async def legal_research_task(self, *, item: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Task function for legal research evaluation"""
        try:
            question = item["input"]["question"]
            
            query_data = {"text": question}
            result = self.legal_system.invoke(
                query_data,
                user_id="evaluator",
                session_id=f"research_eval_{int(datetime.now().timestamp())}"
            )
            
            answer = ""
            if 'messages' in result and result['messages']:
                last_message = result['messages'][-1]
                if hasattr(last_message, 'content'):
                    answer = last_message.content.strip()
                elif isinstance(last_message, dict) and 'content' in last_message:
                    answer = last_message['content'].strip()
            
            # Collect retrieval results
            retrieved_docs = []
            
            # Vector DB search
            try:
                search_results = self.vector.run_search(
                    query=question,
                    collections="all",
                    top_k=50
                )
                for r in search_results.get("legal_cases", []):
                    retrieved_docs.append(f"[CASE] {r.content[:300]}... (score={r.score:.2f})")
                for r in search_results.get("legislation", []):
                    retrieved_docs.append(f"[LAW] {r.content[:300]}... (score={r.score:.2f})")
            except Exception as e:
                retrieved_docs.append(f"[ERROR] Vector search failed: {str(e)}")

            # Web search
            try:
                web_results = self.web_search.get_structured_results(query=question)
                if web_results and "organic" in web_results:
                    for r in web_results["organic"]:
                        snippet = r.get("snippet") or r.get("title") or ""
                        retrieved_docs.append(f"[WEB] {snippet[:300]}... (source={r.get('link','unknown')})")
                else:
                    retrieved_docs.append("[WEB] No web results found")
            except Exception as e:
                retrieved_docs.append(f"[ERROR] Web search failed: {str(e)}")
                
            return {
                "query": question,
                "answer": answer or "Failed to generate research response",
                "retrieved_docs": retrieved_docs
            }
            
        except Exception as e:
            return {
                "query": item.get("input", {}).get("question", "Unknown"),
                "answer": f"Error: {str(e)}",
                "retrieved_docs": []
            }
    
    async def legal_summarization_task(self, *, item: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Task function for legal summarization evaluation"""
        try:
            case_facts = item["input"]["case_facts"]
            
            # Extract case number
            case_match = re.search(r'case ([A-Z0-9\-\/]+)', case_facts)
            case_number = case_match.group(1) if case_match else None
            
            pdf_data = None
            pdf_filename = None
            if case_number:
                pdf_data = await self._read_pdf_file(case_number)
                if pdf_data:
                    pdf_filename = f"{case_number}_(Mahkamah_Tinggi).pdf"
            
            # Prepare query
            if pdf_data:
                query_data = {
                    "text": case_facts,
                    "files": [
                        {
                            "type": "file",
                            "source_type": "base64", 
                            "data": pdf_data,
                            "mime_type": "application/pdf",
                            "filename": pdf_filename
                        }
                    ]
                }
            else:
                query_data = {"text": case_facts}
            
            result = self.legal_system.invoke(
                query_data,
                user_id="evaluator",
                session_id=f"summary_eval_{int(datetime.now().timestamp())}"
            )
            
            summary = ""
            if 'messages' in result and result['messages']:
                last_message = result['messages'][-1]
                if hasattr(last_message, 'content'):
                    summary = last_message.content.strip()
                elif isinstance(last_message, dict) and 'content' in last_message:
                    summary = last_message['content'].strip()
            
            return {
                "document": case_facts,
                "summary": summary or "Failed to generate summary",
                "reference_summary": item.get("expected_output", {}).get("summarized_documents", ""),
                "pdf_used": pdf_data is not None,
                "case_number": case_number
            }
            
        except Exception as e:
            return {
                "document": item.get("input", {}).get("case_facts", "Unknown"),
                "summary": f"Error: {str(e)}",
                "reference_summary": "",
                "pdf_used": False,
                "case_number": None
            }
    
    async def _read_pdf_file(self, case_number: str) -> Optional[str]:
        """Read PDF file as base64"""
        try:
            test_pdf_dir = Path(__file__).parent / "test_dataset" / "test_pdf_file"
            
            possible_filenames = [
                f"{case_number}_(Mahkamah_Tinggi).pdf",
                f"{case_number}_(Mahkamah_Sesyen).pdf",
                f"{case_number}_(Mahkamah_Rayuan).pdf",
                f"{case_number}_(Mahkamah_Persekutuan).pdf",
                f"{case_number}_(Mahkamah_Majistret).pdf",
            ]
            
            for filename in possible_filenames:
                pdf_path = test_pdf_dir / filename
                if pdf_path.exists():
                    with open(pdf_path, 'rb') as f:
                        pdf_data = base64.b64encode(f.read()).decode('utf-8')
                    return pdf_data
            
            # Try partial matching
            for pdf_file in test_pdf_dir.glob("*.pdf"):
                if case_number in pdf_file.name:
                    with open(pdf_file, 'rb') as f:
                        pdf_data = base64.b64encode(f.read()).decode('utf-8')
                    return pdf_data
                    
            return None
            
        except Exception as e:
            print(f"❌ Error reading PDF for case {case_number}: {str(e)}")
            return None
    
    async def legal_prediction_task(self, *, item: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Task function for legal prediction evaluation"""
        try:
            case_facts = item["input"]["case_facts"]
            
            query_data = {
                "text": f"Based on this legal case scenario, predict the likely outcome including case disposition, damages amount, judgment type, and costs award. Be specific: {case_facts}"
            }
            result = self.legal_system.invoke(
                query_data,
                user_id="evaluator",
                session_id=f"prediction_eval_{int(datetime.now().timestamp())}"
            )
            
            prediction_text = ""
            if 'messages' in result and result['messages']:
                last_message = result['messages'][-1]
                if hasattr(last_message, 'content'):
                    prediction_text = last_message.content.strip()
                elif isinstance(last_message, dict) and 'content' in last_message:
                    prediction_text = last_message['content'].strip()
            
            # Parse structured prediction with enhanced regex patterns
            import re
            prediction = {
                "raw_prediction": prediction_text,
                "disposition": "Case dismissed",  # Default fallback instead of "Unknown"
                "damages_amount": None,
                "judgment_type": "Trial Judgment"  # Default fallback instead of "Unknown"
            }
            
            # Enhanced disposition parsing with regex patterns
            disposition_patterns = [
                (r'\*\*disposition:\*\*\s*([^\n<]+)', 'structured'),
                (r'disposition:\s*([^\n<]+)', 'simple'),
                (r'plaintiff\s+wins?', 'Plaintiff wins'),
                (r'defendant\s+wins?', 'Defendant wins'), 
                (r'partially\s+in\s+favour\s+of\s+plaintiff', 'Partially in favour of Plaintiff'),
                (r'partially\s+in\s+favour\s+of\s+defendant', 'Partially in favour of Defendant'),
                (r'case\s+dismissed', 'Case dismissed'),
                (r'appeal\s+dismissed', 'Case dismissed'),
                (r'withdrawn', 'Withdrawn'),
                (r'settled\s+out\s+of\s+court', 'Settled out of court'),
                (r'struck\s+out', 'Struck out')
            ]
            
            text_lower = prediction_text.lower()
            for pattern, result in disposition_patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    if result in ['structured', 'simple']:
                        # Extract the actual value from structured format
                        extracted = match.group(1).strip().strip('*').strip()
                        # Clean up common formatting
                        if extracted.lower().startswith('plaintiff'):
                            prediction["disposition"] = "Plaintiff wins"
                        elif extracted.lower().startswith('defendant'):
                            prediction["disposition"] = "Defendant wins"
                        elif 'partially' in extracted.lower() and 'plaintiff' in extracted.lower():
                            prediction["disposition"] = "Partially in favour of Plaintiff"
                        elif 'partially' in extracted.lower() and 'defendant' in extracted.lower():
                            prediction["disposition"] = "Partially in favour of Defendant"
                        elif 'dismissed' in extracted.lower():
                            prediction["disposition"] = "Case dismissed"
                        else:
                            prediction["disposition"] = extracted.title()
                    else:
                        prediction["disposition"] = result
                    break
            
            # Enhanced judgment type parsing
            judgment_patterns = [
                (r'\*\*judgment\s+type:\*\*\s*([^\n<]+)', 'structured'),
                (r'judgment\s+type:\s*([^\n<]+)', 'simple'),
                (r'appeal\s+dismissed', 'Appeal Dismissed'),
                (r'appeal\s+allowed', 'Appeal Allowed'),
                (r'summary\s+judgment', 'Summary Judgment'),
                (r'default\s+judgment', 'Default Judgment'),
                (r'consent\s+judgment', 'Consent Judgment'),
                (r'trial\s+judgment', 'Trial Judgment')
            ]
            
            for pattern, result in judgment_patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    if result in ['structured', 'simple']:
                        extracted = match.group(1).strip().strip('*').strip()
                        prediction["judgment_type"] = extracted.title()
                    else:
                        prediction["judgment_type"] = result
                    break
            
            # Extract damages using enhanced method
            damages_amount = self.metrics.extract_damages_amount(prediction_text)
            if damages_amount:
                prediction["damages_amount"] = damages_amount
            
            return {
                "case_scenario": case_facts,
                "prediction": prediction,
                "ground_truth": item.get("expected_output", {})
            }
            
        except Exception as e:
            return {
                "case_scenario": item.get("input", {}).get("case_facts", "Unknown"),
                "prediction": {"error": str(e)},
                "ground_truth": {}
            }
    
    async def comprehensive_evaluator(self, task_output: Dict[str, Any], task_type: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Run both LLM-as-a-Judge and traditional metrics evaluation"""
        
        # LLM-as-a-Judge evaluation with task-specific judges
        if task_type == "legal_research":
            llm_eval = await self.research_judge.evaluate_legal_research(
                query=task_output.get("query", ""),
                answer=task_output.get("answer", ""),
                retrieved_docs=task_output.get("retrieved_docs", [])
            )
            traditional_eval = self.metrics.evaluate_research_retrieval(
                answer=task_output.get("answer", ""),
                retrieved_docs=task_output.get("retrieved_docs", [])
            )
        elif task_type == "legal_summarization":
            llm_eval = await self.summarization_judge.evaluate_legal_summarization(
                document=task_output.get("document", ""),
                summary=task_output.get("summary", ""),
                reference_summary=task_output.get("reference_summary", "")
            )
            traditional_eval = self.metrics.evaluate_summarization_quality(
                summary=task_output.get("summary", ""),
                reference_summary=task_output.get("reference_summary", "")
            )
        elif task_type == "legal_prediction":
            llm_eval = await self.prediction_judge.evaluate_legal_prediction(
                case_scenario=task_output.get("case_scenario", ""),
                prediction=task_output.get("prediction", {}),
                ground_truth=task_output.get("ground_truth", {})
            )
            traditional_eval = self.metrics.evaluate_prediction_accuracy(
                prediction=task_output.get("prediction", {}),
                ground_truth=task_output.get("ground_truth", {})
            )
        else:
            llm_eval = {"name": "unknown", "value": 0.0, "comment": "Unknown task type"}
            traditional_eval = {}
        
        return {
            "llm_judge": llm_eval,
            "traditional_metrics": traditional_eval
        }
    
    async def run_comprehensive_evaluation(self, test_dataset_dir: str, max_items: int = None) -> Dict[str, Any]:
        """Run comprehensive evaluation on all test datasets"""
        print("🏛️ Starting Comprehensive Legal AI Evaluation")
        print("🔥 Using GPT-4.1 for LLM-as-a-Judge and GPT-4o for Legal Agents")
        print("=" * 80)
        
        if not self.legal_system:
            print("❌ Legal agent system not available. Cannot run evaluation.")
            return {}
        
        all_results = {
            "evaluation_info": {
                "timestamp": datetime.now().isoformat(),
                "judge_model": "gpt-4.1",
                "agent_model": self.model_name,
                "evaluation_type": "comprehensive",
                "total_datasets": 0,
                "datasets_processed": []
            },
            "results": {
                "research": [],
                "summarization": [],
                "prediction": []
            },
            "aggregate_summary": {}
        }
        
        # Task configurations
        tasks = [
            {
                "name": "Legal Research",
                "type": "legal_research", 
                "file_pattern": "research_eval_dataset_langfuse.csv",
                "task_func": self.legal_research_task
            },
            {
                "name": "Legal Summarization", 
                "type": "legal_summarization",
                "file_pattern": "summarization_eval_dataset_langfuse.csv", 
                "task_func": self.legal_summarization_task
            },
            {
                "name": "Legal Prediction",
                "type": "legal_prediction", 
                "file_pattern": "prediction_eval_dataset_langfuse.csv",
                "task_func": self.legal_prediction_task
            }
        ]
        
        dataset_dir = Path(test_dataset_dir)
        
        for task_config in tasks:
            print(f"\n🔍 Processing {task_config['name']} Evaluation...")
            
            # Find dataset file
            dataset_path = dataset_dir / task_config["file_pattern"]
            if not dataset_path.exists():
                print(f"⚠️ Dataset not found: {dataset_path}")
                continue
            
            # Load dataset
            dataset = self.load_dataset_from_csv(str(dataset_path))
            if max_items:
                dataset = dataset[:max_items]
            
            print(f"📊 Loaded {len(dataset)} items for {task_config['name']}")
            all_results["evaluation_info"]["total_datasets"] += 1
            all_results["evaluation_info"]["datasets_processed"].append({
                "task_type": task_config["type"],
                "dataset_path": str(dataset_path),
                "items_count": len(dataset)
            })
            
            task_results = []
            
            for i, item in enumerate(dataset):
                print(f"  📋 Processing item {i+1}/{len(dataset)}...")
                
                try:
                    # Run task
                    task_output = await task_config["task_func"](item=item)
                    
                    # Run comprehensive evaluation
                    evaluation = await self.comprehensive_evaluator(
                        task_output=task_output,
                        task_type=task_config["type"],
                        item=item
                    )
                    
                    # Collect result
                    result_item = {
                        "item_id": i + 1,
                        "input": item["input"],
                        "expected_output": item.get("expected_output", {}),
                        "task_output": task_output,
                        "evaluation": evaluation,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    task_results.append(result_item)
                    
                    # Show progress
                    llm_score = evaluation["llm_judge"]["value"]
                    print(f"    ✅ LLM Judge Score: {llm_score}/5")
                    
                except Exception as e:
                    print(f"    ❌ Error processing item {i+1}: {str(e)}")
                    error_result = {
                        "item_id": i + 1,
                        "input": item["input"],
                        "expected_output": item.get("expected_output", {}),
                        "task_output": {"error": str(e)},
                        "evaluation": {
                            "llm_judge": {"name": "error", "value": 0.0, "comment": f"Error: {str(e)}"},
                            "traditional_metrics": {}
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    task_results.append(error_result)
            
            # Store results for this task
            all_results["results"][task_config["type"].replace("legal_", "")] = task_results
            
            print(f"✅ {task_config['name']} completed with {len(task_results)} results!")
        
        # Calculate aggregate summary
        all_results["aggregate_summary"] = self._calculate_aggregate_summary(all_results["results"])
        
        # Save comprehensive JSON results
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        
        json_filename = f"comprehensive_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_path = results_dir / json_filename
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Comprehensive results saved to: {json_path}")
        
        # Generate markdown report
        markdown_path = await self._generate_markdown_report(all_results, results_dir)
        print(f"📄 Markdown report saved to: {markdown_path}")
        
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE EVALUATION COMPLETED")
        print("=" * 80)
        
        return all_results
    
    def _calculate_aggregate_summary(self, results: Dict[str, List]) -> Dict[str, Any]:
        """Calculate aggregate statistics across all tasks"""
        summary = {}
        
        for task_type, task_results in results.items():
            if not task_results:
                continue
                
            task_summary = {
                "total_items": len(task_results),
                "llm_judge": {
                    "mean_score": 0.0,
                    "std_score": 0.0,
                    "min_score": 0.0,
                    "max_score": 0.0
                },
                "traditional_metrics": {}
            }
            
            # LLM Judge statistics
            llm_scores = [r["evaluation"]["llm_judge"]["value"] for r in task_results 
                         if "evaluation" in r and "llm_judge" in r["evaluation"]]
            
            if llm_scores:
                import statistics
                task_summary["llm_judge"]["mean_score"] = statistics.mean(llm_scores)
                task_summary["llm_judge"]["std_score"] = statistics.stdev(llm_scores) if len(llm_scores) > 1 else 0.0
                task_summary["llm_judge"]["min_score"] = min(llm_scores)
                task_summary["llm_judge"]["max_score"] = max(llm_scores)
            
            # Traditional metrics statistics
            all_metrics = {}
            for result in task_results:
                if "evaluation" in result and "traditional_metrics" in result["evaluation"]:
                    metrics = result["evaluation"]["traditional_metrics"]
                    for metric_name, value in metrics.items():
                        if metric_name not in all_metrics:
                            all_metrics[metric_name] = []
                        all_metrics[metric_name].append(value)
            
            for metric_name, values in all_metrics.items():
                if values:
                    import statistics
                    task_summary["traditional_metrics"][f"mean_{metric_name}"] = statistics.mean(values)
                    task_summary["traditional_metrics"][f"std_{metric_name}"] = statistics.stdev(values) if len(values) > 1 else 0.0
            
            summary[task_type] = task_summary
        
        return summary
    
    async def _generate_markdown_report(self, results: Dict[str, Any], results_dir: Path) -> Path:
        """Generate comprehensive markdown report"""
        
        markdown_filename = f"comprehensive_evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        markdown_path = results_dir / markdown_filename
        
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write("# Comprehensive Legal AI Evaluation Report\n\n")
            
            # Evaluation info
            eval_info = results["evaluation_info"]
            f.write("## Evaluation Overview\n\n")
            f.write(f"- **Timestamp**: {eval_info['timestamp']}\n")
            f.write(f"- **Judge Model**: {eval_info['judge_model']}\n")
            f.write(f"- **Agent Model**: {eval_info['agent_model']}\n")
            f.write(f"- **Total Datasets**: {eval_info['total_datasets']}\n\n")
            
            # Dataset summary
            f.write("### Datasets Processed\n\n")
            for dataset in eval_info["datasets_processed"]:
                f.write(f"- **{dataset['task_type']}**: {dataset['items_count']} items\n")
            f.write("\n")
            
            # Aggregate summary
            f.write("## Aggregate Results Summary\n\n")
            for task_type, summary in results["aggregate_summary"].items():
                f.write(f"### {task_type.replace('_', ' ').title()}\n\n")
                f.write(f"- **Total Items**: {summary['total_items']}\n")
                
                # LLM Judge results
                llm_judge = summary["llm_judge"]
                f.write(f"- **LLM Judge Mean Score**: {llm_judge['mean_score']:.3f}/5.0\n")
                f.write(f"- **LLM Judge Score Range**: {llm_judge['min_score']:.3f} - {llm_judge['max_score']:.3f}\n")
                f.write(f"- **LLM Judge Std Dev**: {llm_judge['std_score']:.3f}\n\n")
                
                # Traditional metrics
                if summary["traditional_metrics"]:
                    f.write("#### Traditional Metrics\n\n")
                    for metric_name, value in summary["traditional_metrics"].items():
                        if metric_name.startswith("mean_"):
                            display_name = metric_name.replace("mean_", "").replace("_", " ").title()
                            f.write(f"- **{display_name}**: {value:.3f}\n")
                f.write("\n")
            
            # Detailed results
            f.write("## Detailed Results\n\n")
            
            for task_type, task_results in results["results"].items():
                if not task_results:
                    continue
                    
                f.write(f"### {task_type.replace('_', ' ').title()} Results\n\n")
                
                # Results table
                f.write("| Item | LLM Judge Score | Traditional Metrics Summary |\n")
                f.write("|------|-----------------|-----------------------------|\n")
                
                for result in task_results:
                    item_id = result["item_id"]
                    llm_score = result["evaluation"]["llm_judge"]["value"]
                    
                    # Summarize traditional metrics
                    traditional = result["evaluation"]["traditional_metrics"]
                    if traditional:
                        # Show key metrics for each task type
                        if task_type == "research":
                            key_metrics = ["precision_at_5", "recall_at_5", "entity_overlap_ratio"]
                        elif task_type == "summarization":
                            key_metrics = ["rouge1_f1", "rouge2_f1", "bleu_1"]
                        elif task_type == "prediction":
                            key_metrics = ["disposition_accuracy", "damages_mae"]
                        else:
                            key_metrics = list(traditional.keys())[:3]
                        
                        metrics_summary = []
                        for metric in key_metrics:
                            if metric in traditional:
                                value = traditional[metric]
                                if isinstance(value, float):
                                    if value == float('inf'):
                                        metrics_summary.append(f"{metric}: ∞")
                                    else:
                                        metrics_summary.append(f"{metric}: {value:.3f}")
                                else:
                                    metrics_summary.append(f"{metric}: {value}")
                        
                        traditional_summary = ", ".join(metrics_summary)
                    else:
                        traditional_summary = "No metrics"
                    
                    f.write(f"| {item_id} | {llm_score:.1f}/5.0 | {traditional_summary} |\n")
                
                f.write("\n")
                
                # Sample outputs (first 2 items)
                f.write(f"#### Sample {task_type.replace('_', ' ').title()} Outputs\n\n")
                for i, result in enumerate(task_results[:2]):
                    f.write(f"**Item {result['item_id']}**\n\n")
                    
                    # Input
                    if task_type == "research":
                        f.write(f"*Question*: {result['input'].get('question', 'N/A')}\n\n")
                    elif task_type in ["summarization", "prediction"]:
                        case_facts = result['input'].get('case_facts', 'N/A')
                        f.write(f"*Case Facts*: {case_facts[:200]}{'...' if len(case_facts) > 200 else ''}\n\n")
                    
                    # Output summary
                    task_output = result["task_output"]
                    if task_type == "research":
                        answer = task_output.get("answer", "N/A")
                        f.write(f"*Answer*: {answer[:300]}{'...' if len(answer) > 300 else ''}\n\n")
                    elif task_type == "summarization":
                        summary = task_output.get("summary", "N/A")
                        f.write(f"*Summary*: {summary[:300]}{'...' if len(summary) > 300 else ''}\n\n")
                    elif task_type == "prediction":
                        prediction = task_output.get("prediction", {})
                        f.write(f"*Prediction*: {prediction.get('disposition', 'N/A')}\n\n")
                    
                    # Evaluation
                    llm_eval = result["evaluation"]["llm_judge"]
                    f.write(f"*LLM Judge*: {llm_eval['value']}/5.0 - Reasoning: {llm_eval['comment']}\n\n")
                    
                    f.write("---\n\n")
            
            # Conclusion
            f.write("## Conclusion\n\n")
            f.write("This comprehensive evaluation combines qualitative assessment from GPT-4.1 as an LLM Judge ")
            f.write("with quantitative traditional NLP/ML metrics to provide a holistic view of the legal AI system's performance. ")
            f.write("The results demonstrate the system's capabilities across research, summarization, and prediction tasks ")
            f.write("in the Malaysian legal domain.\n\n")
            
            f.write("For detailed analysis of individual results, please refer to the corresponding JSON file ")
            f.write("which contains complete evaluation data including full outputs and metric calculations.\n")
        
        return markdown_path

# CLI interface
async def main():
    """Main entry point for comprehensive evaluation"""
    parser = argparse.ArgumentParser(description="Comprehensive Legal AI Evaluation")
    parser.add_argument("--dataset-dir", default="./test_dataset", 
                       help="Directory containing evaluation datasets")
    parser.add_argument("--model", default="gpt-4.1", 
                       help="Model to use for legal AI system")
    parser.add_argument("--max-items", type=int, default=None,
                       help="Maximum number of items to evaluate per task (for testing)")
    
    args = parser.parse_args()
    
    # Initialize comprehensive evaluation runner
    runner = ComprehensiveEvaluationRunner(model_name=args.model)
    
    if not runner.legal_system:
        print("❌ Legal agent system not available. Cannot run evaluation.")
        return
    
    # Run comprehensive evaluation
    results = await runner.run_comprehensive_evaluation(args.dataset_dir, args.max_items)
    
    print(f"🎉 Comprehensive evaluation completed!")
    print(f"📄 JSON and Markdown reports saved in ./results/ directory.")

if __name__ == "__main__":
    asyncio.run(main())