"""
Gradio ChatInterface for Multi-Agent Legal Assistant

This module provides a modern chat-based interface using Gradio's ChatInterface 
for the Malaysian Civil Law Legal Assistant system with multi-agent capabilities.
Supports file uploads (PDF, DOCX, TXT, images) and real-time streaming responses.
"""

import gradio as gr
import os
import sys
import uuid
import time
import asyncio
import tempfile
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
import logging
from dotenv import load_dotenv

load_dotenv()

# Add the API source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import the legal agent system
from app.api.src.agents.routing import create_legal_agent_system, LegalAgentSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for the legal system
legal_system = None
current_model = "gpt-4.1"
# Session management for memory persistence
user_sessions = {}  # user_id -> session_id mapping

def initialize_legal_system(model_name: str) -> str:
    """Initialize the legal system with specified model."""
    global legal_system, current_model
    try:
        logger.info(f"Initializing legal system with model: {model_name}")
        legal_system = create_legal_agent_system(model_name=model_name)
        current_model = model_name
        return f"✅ Legal Assistant System initialized with {model_name}"
    except Exception as e:
        error_msg = f"❌ Failed to initialize system: {str(e)}"
        logger.error(error_msg)
        return error_msg

def process_uploaded_files(files: List) -> str:
    """Process uploaded files and extract text content."""
    if not files:
        return ""
    
    extracted_content = []
    
    for file in files:
        try:
            file_path = file.name if hasattr(file, 'name') else str(file)
            file_ext = os.path.splitext(file_path)[1].lower()
            
            logger.info(f"Processing uploaded file: {file_path}")
            
            if file_ext == '.pdf':
                # Handle PDF files
                from langchain_pymupdf4llm import PyMuPDF4LLMLoader
                loader = PyMuPDF4LLMLoader(file_path)
                docs = loader.load()
                content = "\n".join([doc.page_content for doc in docs])
                extracted_content.append(f"**PDF Content from {os.path.basename(file_path)}:**\n{content}")
                
            elif file_ext == '.docx':
                # Handle DOCX files with multiple fallback approaches
                try:
                    # First try python-docx (more reliable)
                    from docx import Document
                    doc = Document(file_path)
                    full_text = []
                    for paragraph in doc.paragraphs:
                        full_text.append(paragraph.text)
                    content = '\n'.join(full_text)
                    extracted_content.append(f"**DOCX Content from {os.path.basename(file_path)}:**\n{content}")
                except ImportError:
                    try:
                        # Fallback to Unstructured
                        from langchain_community.document_loaders import UnstructuredWordDocumentLoader
                        loader = UnstructuredWordDocumentLoader(file_path)
                        docs = loader.load()
                        content = "\n".join([doc.page_content for doc in docs])
                        extracted_content.append(f"**DOCX Content from {os.path.basename(file_path)}:**\n{content}")
                    except ImportError:
                        extracted_content.append(f"❌ Error: Neither python-docx nor Unstructured available for DOCX processing: {os.path.basename(file_path)}")
                except Exception as e:
                    extracted_content.append(f"❌ Error processing DOCX {os.path.basename(file_path)}: {str(e)}")
                
            elif file_ext == '.txt':
                # Handle TXT files
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                extracted_content.append(f"**Text Content from {os.path.basename(file_path)}:**\n{content}")
                
            elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                # Handle image files (OCR would need additional implementation)
                extracted_content.append(f"**Image file uploaded: {os.path.basename(file_path)}** (Image processing not yet implemented)")
                
            else:
                extracted_content.append(f"**Unsupported file type: {os.path.basename(file_path)}**")
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            extracted_content.append(f"**Error processing {os.path.basename(file_path)}: {str(e)}**")
    
    return "\n\n".join(extracted_content)

def reset_session():
    """Reset the current user session for a fresh conversation."""
    global user_sessions
    user_id = "chat_user"
    if user_id in user_sessions:
        old_session = user_sessions[user_id]
        user_sessions[user_id] = str(uuid.uuid4())
        logger.info(f"Session reset for user {user_id}: {old_session} -> {user_sessions[user_id]}")
        return f"✅ Session reset. Starting fresh conversation."
    else:
        user_sessions[user_id] = str(uuid.uuid4())
        return f"✅ New session created."

async def legal_chat_handler(message: dict, history: List, model_name: str):
    """
    Async handle chat messages for the legal assistant with multimodal support.
    
    Args:
        message: Dictionary containing 'text' and optionally 'files'
        history: Chat history 
        model_name: Selected AI model
        
    Yields:
        Response chunks for streaming
    """
    global legal_system, current_model
    
    # Initialize system if needed or model changed
    if legal_system is None or current_model != model_name:
        init_result = initialize_legal_system(model_name)
        if "❌" in init_result:
            yield f"System initialization failed: {init_result}"
            return
    
    # Extract query text and files
    query_text = message.get("text", "").strip() if isinstance(message, dict) else str(message).strip()
    
    if not query_text:
        yield "⚠️ Please enter a legal question or query."
        return
    
    # Prepare multimodal query data
    files = message.get("files", []) if isinstance(message, dict) else []
    
    # Convert file objects to paths for processing
    file_paths = []
    if files:
        for file_obj in files:
            if hasattr(file_obj, 'name'):
                file_paths.append({'path': file_obj.name, 'name': os.path.basename(file_obj.name)})
            else:
                file_paths.append({'path': str(file_obj), 'name': os.path.basename(str(file_obj))})
    
    query_data = {
        "text": query_text,
        "files": file_paths
    }
    
    try:
        user_id = "chat_user"
        
        # Use persistent session for memory continuity
        global user_sessions
        if user_id not in user_sessions:
            user_sessions[user_id] = str(uuid.uuid4())
        session_id = user_sessions[user_id]
        
        logger.info(f"Processing chat query: '{query_text[:50]}...' with {len(file_paths)} files (session: {session_id})")
        
        # Use async streaming with progress updates (always enabled)
        try:
            has_streamed_content = False
            
            async for progress_update in legal_system.astream_with_progress(query_data, user_id=user_id, session_id=session_id):
                update_type = progress_update.get("type", "")
                
                if update_type == "agent_switch":
                    # Show agent switch message briefly
                    temp_message = f"🤖 {progress_update.get('agent', 'Agent')} is handling your request..."
                    yield temp_message
                        
                elif update_type == "tool_start":
                    # Show tool usage
                    temp_message = f"🔧 {progress_update.get('message', 'Using tool...')}"
                    yield temp_message
                        
                elif update_type == "token":
                    # Stream individual tokens - this is the main content
                    current_response = progress_update.get("accumulated", "")
                    if current_response:
                        yield current_response
                        has_streamed_content = True
                        
                elif update_type == "final_response":
                    # Only use final response if no content was streamed
                    final_response = progress_update.get("content", "")
                    if final_response and not has_streamed_content:
                        yield final_response
                    # Exit immediately to prevent any further processing
                    return
                        
                elif update_type == "error":
                    error_message = progress_update.get('message', 'An error occurred')
                    if 'rate_limit_exceeded' in error_message or '429' in error_message:
                        yield f"⏱️ API rate limit reached. Please wait a moment and try again."
                    else:
                        yield f"❌ {error_message}"
                    return
            
            # The streaming should complete naturally without needing this fallback
            # But keep it just in case something goes wrong
            if not has_streamed_content:
                yield "❌ No response generated from streaming. Please try again."
                    
        except Exception as e:
            logger.error(f"Async streaming failed: {e}")
            yield f"❌ Streaming failed: {str(e)}. Please try again."
            
    except Exception as e:
        error_msg = f"❌ Error in chat handler: {str(e)}"
        logger.error(error_msg)
        yield error_msg
        
def create_legal_chat_interface():
    """Create the modern ChatInterface for the legal assistant."""
    
    # Model options - corrected to use actual model names
    model_options = [
        "gpt-4.1",
        "gpt-4.1-mini", 
        "gpt-4.1-nano",
    ]
    
    # Custom CSS for better styling
    custom_css = """
    .gradio-container {
        max-width: 1400px !important;
        margin: auto !important;
    }
    .legal-header {
        text-align: center;
        background: linear-gradient(135deg, #1e3a8a, #3b82f6);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .chat-container {
        height: 600px !important;
    }
    """
    
    with gr.Blocks(
        title="Malaysian Civil Law Legal Assistant",
        css=custom_css
    ) as interface:
        
        # Header
        gr.HTML("""
        <div class="legal-header">
            <h1>🏛️ Malaysian Civil Law Legal Assistant</h1>
            <p>Modern Chat Interface with Multi-Agent AI System</p>
            <p><em>Supports Legal Research, Document Summarization & Case Prediction</em></p>
            <p><strong>📎 Upload PDF, DOCX, TXT files or Images for analysis</strong></p>
        </div>
        """)
        
        # Configuration Row
        with gr.Row():
            with gr.Column(scale=1):
                model_dropdown = gr.Dropdown(
                    choices=model_options,
                    value="gpt-4.1",
                    label="🤖 AI Model",
                    info="Select the model for all agents"
                )
            
            with gr.Column(scale=1):
                reset_button = gr.Button(
                    "🔄 Reset Session",
                    variant="secondary",
                    size="sm"
                )

        # Main Chat Interface
        chat_interface = gr.ChatInterface(
            type="messages",
            fn=legal_chat_handler,
            title="ILA - Intelligent Legal Assistant of Malaysia",
            description="Ask me anything about legal stuff!",
            theme="citrus",
            multimodal=True,
            additional_inputs=[model_dropdown],
            textbox=gr.MultimodalTextbox(
                file_count="multiple",
                file_types=[".pdf", ".docx", ".txt", ".jpg", ".jpeg", ".png", ".gif", ".bmp"],
                placeholder="Ask your legal query or upload documents (PDF, DOCX, TXT, images)...",
                show_label=True
            ),
            chatbot=gr.Chatbot(
                type="messages",
                height=500,
                show_copy_button=True,
                bubble_full_width=False
            ),
            save_history=True,
        )
        
        # Information Section
        with gr.Row():
            with gr.Column():
                gr.Markdown("""
                ### 🤖 Available Specialist Agents
                
                - **🔬 Research Agent**: Malaysian Civil Law research and case law analysis
                - **📄 Summarization Agent**: Legal document summarization and key point extraction  
                - **⚖️ Prediction Agent**: Case outcome prediction and legal scenario analysis
                - **🎯 Supervisor Agent**: Intelligent routing to appropriate specialists
                
                ### 📎 Supported File Types
                
                - **PDF**: Legal documents, cases, contracts
                - **DOCX**: Word documents, legal drafts
                - **TXT**: Plain text legal content
                - **Images**: Screenshots of legal documents or any images
                
                ### 💡 Example Queries
                
                **Legal Research:**
                - "What are the requirements for establishing a valid contract under Malaysian law?"
                - "Explain the doctrine of consideration in Malaysian contract law"
                
                **Document Analysis:**
                - Upload a legal document and ask: "Summarize the key points in this contract"
                - "What are the potential legal issues in this uploaded judgment?"
                
                **Case Prediction:**
                - "What's the likelihood of success in a negligence claim with these facts: [describe scenario]"
                - "Predict the outcome if a contractor fails to complete work on time"
                """)
        
        # Initialize system on startup
        interface.load(
            fn=lambda: initialize_legal_system("gpt-4.1"),
            outputs=None
        )
        
        # Connect reset button
        reset_button.click(
            fn=reset_session,
            outputs=None
        )
    
    return interface

def launch_interface(
    server_name: str = "0.0.0.0",
    server_port: int = 7860,
    share: bool = False,
    debug: bool = False
):
    """Launch the Gradio ChatInterface."""
    
    # Create the interface
    interface = create_legal_chat_interface()
    
    # Launch with configuration
    interface.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        debug=debug,
        show_api=False,
        quiet=not debug,
        favicon_path=None,
        ssl_keyfile=None,
        ssl_certfile=None,
        ssl_keyfile_password=None,
        inbrowser=True
    )

if __name__ == "__main__":
    # Configure and launch the interface
    launch_interface(
        server_name="127.0.0.1",  # Local only for development
        server_port=7860,
        share=False,  # Set to True to create public link
        debug=True   # Enable debug mode for development
    )