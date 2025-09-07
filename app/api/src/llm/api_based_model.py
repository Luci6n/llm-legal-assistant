from prompt_templates import legal_task_prompts
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate

class LegalBasedModel:
    def __init__(self, task_prompt, model_name="gpt-4.1", temperature=0.3, max_tokens=5000):
        """
        Initialize the legal assistant model with optimized parameters for legal tasks.
        
        Args:
            model_name: The OpenAI model to use (default: gpt-4 for better reasoning)
            temperature: Lower temperature for more consistent legal advice (default: 0.3)
            max_tokens: Maximum tokens for comprehensive legal responses (default: 5000)
        """
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout=60,
            max_retries=3
        )
        
        # Define available task types
        self.available_tasks = {
            "legal_research": legal_task_prompts.LEGAL_RESEARCH_PROMPT,
            "case_summary": legal_task_prompts.CASE_SUMMARY_PROMPT,
            "outcome_prediction": legal_task_prompts.OUTCOME_PREDICTION_PROMPT,
            "legal_router": legal_task_prompts.LEGAL_ROUTER_PROMPT
        }
        
        # Create default prompt template for general legal tasks
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", task_prompt),
            ("human", "{user_query}")
        ])
        
        # Create the default chain
        self.chain = self.prompt_template | self.llm
    
    def generate_response(self, user_query: str) -> str:
        """
        Generate a response for a legal query using the default system prompt.
        
        Args:
            user_query: The user's legal question or request
            
        Returns:
            The model's response as a string
        """
        response = self.chain.invoke({"user_query": user_query})
        return response.content
    
    def generate_structured_response(self, task_type: str, user_query: str) -> str:
        """
        Generate a response using a specific legal task prompt.
        
        Args:
            task_type: One of: legal_research, case_summary, outcome_prediction, legal_router
            user_query: The user's legal question or request
            
        Returns:
            The model's response as a string
        """
        if task_type in self.available_tasks:
            specific_prompt = self.available_tasks[task_type]
            messages = [
                SystemMessage(content=specific_prompt),
                HumanMessage(content=user_query)
            ]
            response = self.llm.invoke(messages)
            return response.content
        else:
            raise ValueError(f"Unknown task type: {task_type}. Available types: {list(self.available_tasks.keys())}")
    
    def get_available_tasks(self) -> list:
        """
        Get list of available task types.
        
        Returns:
            List of available task type names
        """
        return list(self.available_tasks.keys())