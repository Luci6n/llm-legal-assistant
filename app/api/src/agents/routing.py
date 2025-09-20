"""
Multi-Agent Legal Assistant Routing System

This module implements a LangGraph-based supervisor system with specialized legal agents:
1. Legal Research Agent - Handles research tasks for Malaysian Civil Law
2. Legal Summarization Agent - Summarizes legal documents and cases  
3. Legal Case/Scenario Outcome Prediction Agent - Predicts case outcomes
4. Supervisor Agent - Routes tasks to appropriate specialist agents

Uses LangGraph's create_react_agent and supervisor patterns for robust multi-agent coordination.
"""

import logging
import os
import base64
import threading
from typing import Dict, Any, List, Literal, Union
from typing_extensions import TypedDict

# Set CUDA memory allocation configuration to avoid fragmentation
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Core LangGraph and LangChain imports
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

# Try to import langgraph-supervisor for prebuilt supervisor functionality
try:
    from langgraph_supervisor import create_supervisor
    SUPERVISOR_AVAILABLE = True
    logger.info("langgraph-supervisor available")
except ImportError:
    logger.warning("langgraph-supervisor not available - using custom supervisor")
    SUPERVISOR_AVAILABLE = False

# Import our local modules
from ..llm.api_based_model import LegalBasedModel
from ..memory.memory import MemoryManager
from ..tools.tools_manager import LegalToolsManager

# Global tools manager instance to prevent multiple model loading
_global_tools_manager = None
_tools_manager_lock = threading.Lock()

def get_shared_tools_manager():
    """Get or create a shared tools manager instance to avoid CUDA memory issues."""
    global _global_tools_manager
    
    with _tools_manager_lock:
        if _global_tools_manager is None:
            try:
                # Try with fallback options to avoid memory issues
                _global_tools_manager = LegalToolsManager()
                logger.info("Created global shared tools manager")
            except Exception as e:
                logger.error(f"Failed to create shared tools manager: {e}")
                # Create a minimal tools manager without vector search if needed
                try:
                    logger.info("Attempting to create minimal tools manager...")
                    _global_tools_manager = LegalToolsManager(force_new_instance=True)
                    logger.info("Created minimal tools manager")
                except Exception as e2:
                    logger.error(f"Failed to create even minimal tools manager: {e2}")
                    _global_tools_manager = None
        
        return _global_tools_manager

def load_prompt_template(filename: str) -> str:
    """Load prompt template from file."""
    try:
        prompt_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "prompt_templates", 
            filename
        )
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load prompt template {filename}: {e}")
        return ""

# Load all prompt templates
LEGAL_RESEARCH_PROMPT = load_prompt_template("legal_research_prompt.md")
LEGAL_SUMMARIZATION_PROMPT = load_prompt_template("legal_summarization_prompt.md")
LEGAL_PREDICTION_PROMPT = load_prompt_template("legal_case_prediction_prompt.md")
SUPERVISOR_PROMPT = load_prompt_template("legal_router.md")

class LegalAgentState(MessagesState):
    """Extended state for legal agents with additional context and multimodal support."""
    user_id: str = "default_user"
    session_id: str = "default_session"
    current_agent: str = "supervisor"
    context: Dict[str, Any] = {}
    uploaded_files: List[Dict[str, Any]] = []  # Store file metadata and content

class LegalAgentSystem:
    """
    Multi-agent legal assistant system with supervisor coordination.
    
    Implements the supervisor pattern where a central agent routes tasks
    to specialized worker agents based on the type of legal query.
    """
    
    def __init__(self, model_name: str = "openai:gpt-4o-mini"):
        """
        Initialize the multi-agent legal system.
        
        Args:
            model_name: The model to use for all agents
        """
        self.model_name = model_name
        
        # Initialize base model
        self.model_manager = LegalBasedModel(model_name=model_name)
        self.base_model = self.model_manager.get_model()
        
        # Initialize memory manager
        self.memory_manager = MemoryManager(self.base_model)
        
        # Use shared tools manager to avoid CUDA memory issues
        self.tools_manager = get_shared_tools_manager()
        if self.tools_manager is None:
            logger.warning("Tools manager could not be initialized - agents will have limited functionality")
        
        # Initialize checkpointer for conversation memory
        self.checkpointer = InMemorySaver()
        
        # Create specialized agents
        self.research_agent = self._create_research_agent()
        self.summarization_agent = self._create_summarization_agent()
        self.prediction_agent = self._create_prediction_agent()
        
        # Create supervisor agent
        self.supervisor_agent = self._create_supervisor_agent()
        
        # Build the multi-agent graph
        self.graph = self._build_graph()
        
        logger.info("Legal Agent System initialized successfully")
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """Encode image file to base64 string."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
            return ""
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type for file."""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"
    
    def _process_multimodal_content(self, query_data: Dict[str, Any]) -> List[Union[str, Dict[str, Any]]]:
        """
        Process multimodal content including text, images, and documents.
        
        Args:
            query_data: Dictionary containing text, files, and other content
            
        Returns:
            List of content items suitable for LangChain models
        """
        content = []
        
        # Add text content
        text_content = query_data.get('text', query_data.get('question', ''))
        if text_content:
            content.append({"type": "text", "text": text_content})
        
        # Process uploaded files
        files = query_data.get('files', [])
        for file_info in files:
            try:
                file_path = file_info.get('path') or file_info.get('name', '')
                if not file_path or not os.path.exists(file_path):
                    continue
                
                mime_type = self._get_mime_type(file_path)
                
                # Handle images
                if mime_type.startswith('image/'):
                    base64_image = self._encode_image_to_base64(file_path)
                    if base64_image:
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        })
                        logger.info(f"Added image content from {file_path}")
                
                # Handle text documents (PDF, DOCX, TXT)
                elif mime_type in ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']:
                    # Extract text content from documents
                    extracted_text = self._extract_document_text(file_path, mime_type)
                    if extracted_text:
                        content.append({
                            "type": "text", 
                            "text": f"\n\n--- Content from {os.path.basename(file_path)} ---\n{extracted_text}\n--- End of document ---\n"
                        })
                        logger.info(f"Added document content from {file_path}")
                
            except Exception as e:
                logger.error(f"Error processing file {file_info}: {e}")
                content.append({
                    "type": "text",
                    "text": f"\n[Error processing file: {e}]\n"
                })
        
        # Fallback to simple text if no content was processed
        if not content:
            content = [{"type": "text", "text": text_content or "No content provided"}]
        
        return content
    
    def _extract_document_text(self, file_path: str, mime_type: str) -> str:
        """Extract text content from various document types."""
        try:
            if mime_type == 'application/pdf':
                # Use PyMuPDF for PDF extraction
                try:
                    from langchain_pymupdf4llm import PyMuPDF4LLMLoader
                    loader = PyMuPDF4LLMLoader(file_path)
                    docs = loader.load()
                    return "\n".join([doc.page_content for doc in docs])
                except ImportError:
                    logger.warning("PyMuPDF4LLM not available for PDF processing")
                    return f"[PDF file uploaded: {os.path.basename(file_path)}]"
            
            elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                # Try multiple approaches for DOCX extraction
                try:
                    # First try python-docx (more reliable)
                    from docx import Document
                    doc = Document(file_path)
                    full_text = []
                    for paragraph in doc.paragraphs:
                        full_text.append(paragraph.text)
                    return '\n'.join(full_text)
                except ImportError:
                    try:
                        # Fallback to Unstructured
                        from langchain_community.document_loaders import UnstructuredWordDocumentLoader
                        loader = UnstructuredWordDocumentLoader(file_path)
                        docs = loader.load()
                        return "\n".join([doc.page_content for doc in docs])
                    except ImportError:
                        logger.warning("Neither python-docx nor Unstructured available for DOCX processing")
                        return f"[DOCX file uploaded: {os.path.basename(file_path)}]"
                except Exception as e:
                    logger.error(f"Error processing DOCX file: {str(e)}")
                    return f"[Error processing DOCX file: {os.path.basename(file_path)}]"
            
            elif mime_type == 'text/plain':
                # Read plain text files
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            else:
                return f"[File uploaded: {os.path.basename(file_path)} - Type: {mime_type}]"
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return f"[Error reading file: {os.path.basename(file_path)}]"
    
    def _create_research_agent(self):
        """Create the legal research specialist agent."""
        memory_tools = self.memory_manager.get_memory_tools()
        
        # Add research tools if available
        if self.tools_manager:
            try:
                research_tools = self.tools_manager.get_tools()
                all_tools = memory_tools + research_tools
                logger.info(f"Research agent initialized with {len(all_tools)} tools")
            except Exception as e:
                logger.warning(f"Failed to get research tools: {e}")
                all_tools = memory_tools
        else:
            all_tools = memory_tools
            logger.warning("Research agent initialized without search tools")
        
        return create_react_agent(
            model=self.base_model,
            tools=all_tools,
            prompt=LEGAL_RESEARCH_PROMPT,
            name="legal_research_agent",
            checkpointer=self.checkpointer,
            store=self.memory_manager.get_store()
        )
    
    def _create_summarization_agent(self):
        """Create the legal document summarization specialist agent."""
        memory_tools = self.memory_manager.get_memory_tools()
        
        # Add research tools if available
        if self.tools_manager:
            try:
                research_tools = self.tools_manager.get_tools()
                all_tools = memory_tools + research_tools
            except Exception as e:
                logger.warning(f"Failed to get research tools for summarization: {e}")
                all_tools = memory_tools
        else:
            all_tools = memory_tools
        
        return create_react_agent(
            model=self.base_model,
            tools=all_tools,
            prompt=LEGAL_SUMMARIZATION_PROMPT,
            name="legal_summarization_agent", 
            checkpointer=self.checkpointer,
            store=self.memory_manager.get_store()
        )
    
    def _create_prediction_agent(self):
        """Create the legal case outcome prediction specialist agent."""
        memory_tools = self.memory_manager.get_memory_tools()
        
        # Add research tools if available
        if self.tools_manager:
            try:
                research_tools = self.tools_manager.get_tools()
                all_tools = memory_tools + research_tools
            except Exception as e:
                logger.warning(f"Failed to get research tools for prediction: {e}")
                all_tools = memory_tools
        else:
            all_tools = memory_tools
        
        return create_react_agent(
            model=self.base_model,
            tools=all_tools,
            prompt=LEGAL_PREDICTION_PROMPT,
            name="legal_prediction_agent",
            checkpointer=self.checkpointer,
            store=self.memory_manager.get_store()
        )
    
    def _create_handoff_tool(self, agent_name: str, description: str):
        """Create a handoff tool for routing to a specific agent."""
        from langchain_core.tools import tool
        from langchain_core.tools import InjectedToolCallId
        from langgraph.prebuilt import InjectedState
        from typing import Annotated
        
        @tool(f"transfer_to_{agent_name}", description=description)
        def handoff_tool(
            state: Annotated[LegalAgentState, InjectedState],
            tool_call_id: Annotated[str, InjectedToolCallId],
        ) -> Command:
            tool_message = {
                "role": "tool",
                "content": f"Successfully transferred to {agent_name}",
                "name": f"transfer_to_{agent_name}",
                "tool_call_id": tool_call_id,
            }
            return Command(
                goto=agent_name,
                update={**state, "messages": state["messages"] + [tool_message], "current_agent": agent_name},
                graph=Command.PARENT,
            )
        
        return handoff_tool
    
    def _create_supervisor_agent(self):
        """Create the supervisor agent that routes tasks to specialists."""
        # Create handoff tools for each specialist agent
        handoff_tools = [
            self._create_handoff_tool(
                "legal_research_agent",
                "Route query to legal research specialist for Malaysian Civil Law research tasks"
            ),
            self._create_handoff_tool(
                "legal_summarization_agent", 
                "Route query to legal document summarization specialist"
            ),
            self._create_handoff_tool(
                "legal_prediction_agent",
                "Route query to legal case outcome prediction specialist"
            )
        ]
        
        return create_react_agent(
            model=self.base_model,
            tools=handoff_tools,
            prompt=SUPERVISOR_PROMPT,
            name="supervisor_agent",
            checkpointer=self.checkpointer,
            store=self.memory_manager.get_store()
        )
    
    def _build_graph(self):
        """Build the multi-agent supervisor graph."""
        if SUPERVISOR_AVAILABLE:
            return self._build_prebuilt_supervisor_graph()
        else:
            return self._build_custom_supervisor_graph()
    
    def _build_prebuilt_supervisor_graph(self):
        """Build graph using prebuilt langgraph-supervisor, using SUPERVISOR_PROMPT."""
        try:
            # Use SUPERVISOR_PROMPT loaded from file
            supervisor = create_supervisor(
                model=self.base_model,
                agents=[
                    self.research_agent,
                    self.summarization_agent, 
                    self.prediction_agent
                ],
                prompt=SUPERVISOR_PROMPT,
                add_handoff_back_messages=True,
                output_mode="full_history",
            ).compile(
                checkpointer=self.checkpointer,
                store=self.memory_manager.get_store()
            )
            logger.info("Using prebuilt supervisor from langgraph-supervisor with SUPERVISOR_PROMPT")
            return supervisor
        except Exception as e:
            logger.warning(f"Failed to create prebuilt supervisor: {e}")
            logger.info("Falling back to custom supervisor implementation")
            return self._build_custom_supervisor_graph()
    
    def _build_custom_supervisor_graph(self):
        """Build the custom multi-agent supervisor graph."""
        # Create the state graph
        workflow = StateGraph(LegalAgentState)
        
        # Add all agents as nodes
        workflow.add_node("supervisor", self.supervisor_agent)
        workflow.add_node("legal_research_agent", self.research_agent)
        workflow.add_node("legal_summarization_agent", self.summarization_agent)
        workflow.add_node("legal_prediction_agent", self.prediction_agent)
        
        # Set entry point to supervisor
        workflow.add_edge(START, "supervisor")
        
        # All agents route back to supervisor (can be customized)
        workflow.add_edge("legal_research_agent", "supervisor")
        workflow.add_edge("legal_summarization_agent", "supervisor")
        workflow.add_edge("legal_prediction_agent", "supervisor")
        
        # Compile the graph with checkpointer for memory
        compiled_graph = workflow.compile(
            checkpointer=self.checkpointer,
            store=self.memory_manager.get_store()
        )
        
        logger.info("Using custom supervisor implementation")
        return compiled_graph
    
    def invoke(self, query: Dict[str, Any], user_id: str = "default_user", session_id: str = "default_session") -> Dict[str, Any]:
        """
        Process a legal query through the multi-agent system.
        
        Args:
            query: Dictionary containing the user's query (can include 'question', 'text', 'files', etc.)
            user_id: Unique identifier for the user
            session_id: Unique identifier for the conversation session
            
        Returns:
            The system's response
        """
        try:
            # Process multimodal content
            multimodal_content = self._process_multimodal_content(query)
            
            # Create HumanMessage with multimodal content
            human_message = HumanMessage(content=multimodal_content)
            
            # Prepare input state
            input_state = {
                "messages": [human_message],
                "user_id": user_id,
                "session_id": session_id,
                "current_agent": "supervisor",
                "context": {},
                "uploaded_files": query.get('files', [])
            }
            
            # Configure execution with proper thread_id for memory
            config = {
                "configurable": {
                    "thread_id": f"{user_id}_{session_id}",
                    "user_id": user_id
                }
            }
            
            # Execute the graph
            result = self.graph.invoke(input_state, config=config)
            
            logger.info(f"Successfully processed query for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "messages": [{"role": "assistant", "content": f"I apologize, but I encountered an error while processing your request: {str(e)}"}],
                "error": str(e)
            }
    
    async def ainvoke(self, query: Dict[str, Any], user_id: str = "default_user", session_id: str = "default_session") -> Dict[str, Any]:
        """
        Async version of invoke for processing a legal query through the multi-agent system.
        
        Args:
            query: Dictionary containing the user's query (can include 'question', 'text', 'files', etc.)
            user_id: Unique identifier for the user
            session_id: Unique identifier for the conversation session
            
        Returns:
            The system's response
        """
        try:
            # Process multimodal content
            multimodal_content = self._process_multimodal_content(query)
            
            # Create HumanMessage with multimodal content
            human_message = HumanMessage(content=multimodal_content)
            
            # Prepare input state
            input_state = {
                "messages": [human_message],
                "user_id": user_id,
                "session_id": session_id,
                "current_agent": "supervisor",
                "context": {},
                "uploaded_files": query.get('files', [])
            }
            
            # Configure execution with proper thread_id for memory
            config = {
                "configurable": {
                    "thread_id": f"{user_id}_{session_id}",
                    "user_id": user_id
                }
            }
            
            # Execute the graph asynchronously
            result = await self.graph.ainvoke(input_state, config=config)
            
            logger.info(f"Successfully processed query for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "messages": [{"role": "assistant", "content": f"I apologize, but I encountered an error while processing your request: {str(e)}"}],
                "error": str(e)
            }
    
    def stream(self, query: Dict[str, Any], user_id: str = "default_user", session_id: str = "default_session"):
        """
        Stream the processing of a legal query through the multi-agent system.
        
        Args:
            query: Dictionary containing the user's query (can include 'question', 'text', 'files', etc.)
            user_id: Unique identifier for the user
            session_id: Unique identifier for the conversation session
            
        Yields:
            Streaming updates from the system
        """
        try:
            # Process multimodal content
            multimodal_content = self._process_multimodal_content(query)
            
            # Create HumanMessage with multimodal content
            human_message = HumanMessage(content=multimodal_content)
            
            # Prepare input state
            input_state = {
                "messages": [human_message],
                "user_id": user_id,
                "session_id": session_id,
                "current_agent": "supervisor",
                "context": {},
                "uploaded_files": query.get('files', [])
            }
            
            # Configure execution with proper thread_id for memory
            config = {
                "configurable": {
                    "thread_id": f"{user_id}_{session_id}",
                    "user_id": user_id
                }
            }
            
            # Stream the graph execution
            for chunk in self.graph.stream(input_state, config=config, stream_mode="values"):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error streaming query: {e}")
            yield {
                "supervisor": {
                    "messages": [{"role": "assistant", "content": f"I apologize, but I encountered an error: {str(e)}"}]
                }
            }
    
    async def astream(self, query: Dict[str, Any], user_id: str = "default_user", session_id: str = "default_session"):
        """
        Async stream the processing of a legal query through the multi-agent system.
        
        Args:
            query: Dictionary containing the user's query (can include 'question', 'text', 'files', etc.)
            user_id: Unique identifier for the user
            session_id: Unique identifier for the conversation session
            
        Yields:
            Streaming updates from the system
        """
        try:
            # Process multimodal content
            multimodal_content = self._process_multimodal_content(query)
            
            # Create HumanMessage with multimodal content
            human_message = HumanMessage(content=multimodal_content)
            
            # Prepare input state
            input_state = {
                "messages": [human_message],
                "user_id": user_id,
                "session_id": session_id,
                "current_agent": "supervisor",
                "context": {},
                "uploaded_files": query.get('files', [])
            }
            
            # Configure execution with proper thread_id for memory
            config = {
                "configurable": {
                    "thread_id": f"{user_id}_{session_id}",
                    "user_id": user_id
                }
            }
            
            # Stream the graph execution asynchronously
            async for chunk in self.graph.astream(input_state, config=config, stream_mode="values"):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error streaming query: {e}")
            yield {
                "supervisor": {
                    "messages": [{"role": "assistant", "content": f"I apologize, but I encountered an error: {str(e)}"}]
                }
            }
            
    async def astream_events(self, query: Dict[str, Any], user_id: str = "default_user", session_id: str = "default_session"):
        """
        Stream events from the legal query processing with detailed agent progress.
        
        This method provides fine-grained streaming of agent activities including:
        - Tool calls and results
        - Agent switches and handoffs
        - Intermediate reasoning steps
        - Token-level streaming from language models
        
        Args:
            query: Dictionary containing the user's query (can include 'question', 'files', etc.)
            user_id: Unique identifier for the user
            session_id: Unique identifier for the conversation session
            
        Yields:
            Event dictionaries with detailed agent progress information
        """
        try:
            # Process multimodal content
            multimodal_content = self._process_multimodal_content(query)
            
            # Create HumanMessage with multimodal content
            human_message = HumanMessage(content=multimodal_content)
            
            # Prepare input state
            input_state = {
                "messages": [human_message],
                "user_id": user_id,
                "session_id": session_id,
                "current_agent": "supervisor",
                "context": {},
                "uploaded_files": query.get('files', [])
            }
            
            # Configure execution with proper thread_id for memory
            config = {
                "configurable": {
                    "thread_id": f"{user_id}_{session_id}",
                    "user_id": user_id
                }
            }
            
            # Stream events with detailed progress tracking
            async for event in self.graph.astream_events(
                input_state, 
                config=config,
                version="v2"  # Use v2 for better event structure
            ):
                yield event
                
        except Exception as e:
            logger.error(f"Error streaming events: {e}")
            yield {
                "event": "on_error",
                "data": {
                    "error": str(e),
                    "message": "An error occurred while processing your request"
                }
            }
    
    async def astream_with_progress(self, query: Dict[str, Any], user_id: str = "default_user", session_id: str = "default_session"):
        """
        Stream responses with progress updates optimized for chat interfaces.
        
        This method processes events and yields user-friendly progress updates
        suitable for displaying in chat interfaces.
        
        Args:
            query: Dictionary containing the user's query
            user_id: Unique identifier for the user
            session_id: Unique identifier for the conversation session
            
        Yields:
            Progress updates and final responses formatted for chat display
        """
        try:
            current_agent = None
            final_response = ""
            has_streamed_tokens = False
            response_complete = False  # Single flag to track completion
            
            async for event in self.astream_events(query, user_id, session_id):
                # Skip all processing once response is complete
                if response_complete:
                    break
                    
                event_type = event.get("event", "")
                event_name = event.get("name", "")
                event_data = event.get("data", {})
                
                # Track agent switches
                if event_type == "on_chain_start" and "agent" in event_name:
                    agent_name = event_name.replace("_agent", "").replace("_", " ").title()
                    if current_agent != agent_name:
                        current_agent = agent_name
                        yield {
                            "type": "agent_switch",
                            "agent": agent_name,
                            "message": f"🤖 {agent_name} is now handling your request..."
                        }
                
                # Track tool usage
                elif event_type == "on_tool_start":
                    tool_name = event_name.replace("_", " ").title()
                    yield {
                        "type": "tool_start",
                        "tool": tool_name,
                        "message": f"🔧 Using {tool_name}..."
                    }
                
                # Stream LLM tokens - only from actual agent responses, not routing
                elif event_type == "on_chat_model_stream" and not response_complete:
                    chunk = event_data.get("chunk", {})
                    if hasattr(chunk, 'content') and chunk.content:
                        content = chunk.content
                        
                        # Filter out routing/supervisor messages and empty content
                        if (content.strip() and 
                            not content.strip().startswith('route:') and
                            not content.strip().startswith('transfer_to') and
                            'transfer_to_' not in content):
                            
                            # Clean up formatting issues in content
                            cleaned_content = content
                            
                            # Fix common formatting concatenation issues
                            accumulated_so_far = final_response + content
                            
                            # Fix missing line breaks between sections
                            if '###' in content and not content.startswith('\n') and not final_response.endswith('\n'):
                                if final_response and not final_response.endswith('\n'):
                                    cleaned_content = '\n\n' + content
                            
                            # Fix specific prediction formatting issues
                            fixes = [
                                ('Legal Case Outcome Analysis###', 'Legal Case Outcome Analysis\n\n###'),
                                ('Key Legal Issues-', 'Key Legal Issues\n-'),
                                ('Predicted OutcomeDisposition:', 'Predicted Outcome\n\n**Disposition:**'),
                                ('Judgment Type:-', 'Judgment Type:\n-'),
                                ('Remedy:-', 'Remedy:\n-'),
                                ('Limitations:-', 'Limitations:\n-'),
                            ]
                            
                            for old, new in fixes:
                                if old in accumulated_so_far:
                                    # Apply fix to the accumulated response
                                    final_response = final_response.replace(old, new)
                                    # Don't add this content since we already fixed it in final_response
                                    cleaned_content = ""
                                    break
                            
                            if cleaned_content:  # Only add if we didn't already fix it above
                                final_response += cleaned_content
                                has_streamed_tokens = True
                                yield {
                                    "type": "token",
                                    "content": cleaned_content,
                                    "accumulated": final_response
                                }
                
                # Handle completion events - mark as complete and exit immediately
                elif event_type == "on_chain_end":
                    # Any chain completion means we're done
                    if has_streamed_tokens:
                        response_complete = True
                        logger.info(f"Chain completed ({event_name}) - ending stream")
                        return
                    elif event_name == "supervisor":
                        # If supervisor completes without streaming, there might be a final message
                        response_complete = True
                        logger.info("Supervisor completed without streaming - checking for final response")
                        # Don't return yet, let it check for final messages
                
                # Capture any final output if no streaming occurred
                elif event_type == "on_chain_end" and not has_streamed_tokens and not response_complete:
                    output = event_data.get("output", {})
                    if isinstance(output, dict) and "messages" in output:
                        messages = output["messages"]
                        if messages and len(messages) > 0:
                            last_message = messages[-1]
                            if hasattr(last_message, 'content') and last_message.content:
                                yield {
                                    "type": "final_response",
                                    "content": last_message.content
                                }
                                response_complete = True
                                return
                    
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in progress streaming: {e}")
            
            # Check for rate limiting errors
            if "rate_limit_exceeded" in error_message or "429" in error_message:
                yield {
                    "type": "error",
                    "message": "API rate limit exceeded. Please wait a moment and try again."
                }
            else:
                yield {
                    "type": "error",
                    "message": f"An error occurred: {error_message}"
                }
    
    def get_conversation_history(self, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        """
        Get the conversation history for a specific user session.
        
        Args:
            user_id: Unique identifier for the user
            session_id: Unique identifier for the conversation session
            
        Returns:
            List of messages in the conversation
        """
        try:
            config = {
                "configurable": {
                    "thread_id": f"{user_id}_{session_id}"
                }
            }
            
            state = self.graph.get_state(config)
            return state.values.get("messages", [])
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []

# Factory function for easy initialization
def create_legal_agent_system(model_name: str = "openai:gpt-4o-mini") -> LegalAgentSystem:
    """
    Factory function to create a legal agent system.
    
    Args:
        model_name: The model to use for all agents
        
    Returns:
        Initialized LegalAgentSystem
    """
    return LegalAgentSystem(model_name=model_name)

# Example usage for testing
if __name__ == "__main__":
    # Initialize the system
    legal_system = create_legal_agent_system()
    
    # Example query
    query = "What are the key elements required to establish negligence under Malaysian civil law?"
    
    # Process the query
    result = legal_system.invoke(query)
    print("System Response:", result)
