# Malaysian Civil Law Legal Assistant - Web Interface

A professional Gradio-based web interface for the multi-agent legal assistant system specializing in Malaysian Civil Law.

## 🌟 Features

### Multi-Agent Architecture
- **🔬 Legal Research Agent**: Specialized in Malaysian Civil Law research and case law analysis
- **📄 Summarization Agent**: Expert in legal document summarization and key point extraction
- **⚖️ Case Prediction Agent**: Analyzes scenarios and predicts legal outcomes
- **🎯 Supervisor Agent**: Intelligently routes queries to the most appropriate specialist

### User Interface Features
- **💬 Interactive Chat Interface**: Clean, professional chat interface for legal queries
- **🔄 Real-time Processing**: Optional streaming mode to see agent processing in real-time
- **📚 Session Management**: Persistent conversation history per user session
- **⚙️ Model Selection**: Support for multiple AI models (OpenAI, Anthropic)
- **📱 Responsive Design**: Works on desktop, tablet, and mobile devices

### Legal Specializations
- Contract Law analysis and formation requirements
- Negligence and tort law elements
- Legal document summarization
- Case outcome prediction
- Malaysian Civil Law research

## 🚀 Quick Start

### Prerequisites
1. Python 3.10 or higher
2. Required environment variables:
   - `OPENAI_API_KEY` (for OpenAI models)
   - `ANTHROPIC_API_KEY` (for Anthropic models, optional)

### Installation

1. **Install Web Interface Dependencies**:
   ```bash
   cd app/web
   pip install -r requirements.txt
   ```

2. **Launch the Interface**:
   ```bash
   python launch.py
   ```

3. **Access the Interface**:
   Open your browser and navigate to: `http://127.0.0.1:7860`

## 📖 Usage Guide

### Getting Started

1. **Initialize the System**:
   - Select your preferred AI model from the dropdown
   - Click "🚀 Initialize System"
   - Wait for the success message

2. **Ask Legal Questions**:
   - Enter your User ID (optional, for session tracking)
   - Type your legal question in the query box
   - Click "📨 Submit Query" or press Enter

3. **View Responses**:
   - The system will automatically route your query to the appropriate specialist
   - Responses appear in the main response area
   - Enable streaming to see real-time processing updates

### Example Queries

#### Legal Research
```
What are the requirements for establishing a valid contract under Malaysian law?
```

#### Document Summarization
```
Please summarize this judgment: [paste legal text here]
```

#### Case Prediction
```
What's the likelihood of success in a negligence claim with these facts:
- Driver was texting while driving
- Accident occurred during heavy rain
- Plaintiff suffered minor injuries
- No traffic violations recorded
```

### Session Management

- **View History**: Click "📖 Show Conversation History" to see past conversations
- **Clear Session**: Click "🗑️ Clear Conversation" to start fresh
- **User Sessions**: Each User ID maintains separate conversation history

## 🔧 Configuration

### Model Options
- `openai:gpt-4o-mini` (Default, fast and cost-effective)
- `openai:gpt-4o` (Most capable OpenAI model)
- `openai:gpt-4` (Previous generation, reliable)
- `openai:gpt-3.5-turbo` (Legacy, budget option)
- `anthropic:claude-3-5-sonnet-latest` (Anthropic's most capable)
- `anthropic:claude-3-5-haiku-latest` (Anthropic's fast model)

### Environment Variables
```bash
# Required for OpenAI models
export OPENAI_API_KEY="your-openai-api-key"

# Optional for Anthropic models
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Optional: Custom database URL for persistent memory
export DATABASE_URL="postgresql://user:pass@localhost/legal_assistant"
```

### Launch Options

#### Development Mode (Default)
```python
launch_interface(
    server_name="127.0.0.1",  # Local only
    server_port=7860,
    share=False,              # No public URL
    debug=True               # Debug mode enabled
)
```

#### Production Mode
```python
launch_interface(
    server_name="0.0.0.0",    # Accept external connections
    server_port=7860,
    share=True,               # Create public Gradio URL
    debug=False              # Production mode
)
```

## 🏗️ Architecture

### Interface Components

1. **LegalAssistantInterface**: Main wrapper class
   - Manages the legal agent system lifecycle
   - Handles user sessions and conversation history
   - Processes queries and formats responses

2. **Gradio Interface**: Web UI components
   - System configuration panel
   - Chat interface with query input/response display
   - Session management controls
   - Example queries and documentation

### Integration Points

- **routing.py**: Multi-agent system integration via `create_legal_agent_system()`
- **Memory Management**: Automatic session tracking and conversation persistence
- **Error Handling**: Comprehensive error catching and user-friendly error messages

## 🛠️ Development

### File Structure
```
app/web/
├── gradio_interface.py    # Main interface implementation
├── launch.py             # Simple launcher script
├── requirements.txt      # Web interface dependencies
└── README.md            # This documentation
```

### Customization

#### Adding New Model Providers
```python
self.model_options = [
    "openai:gpt-4o-mini",
    "anthropic:claude-3-5-sonnet-latest",
    "your-provider:your-model"  # Add here
]
```

#### Custom CSS Styling
Modify the `custom_css` variable in `create_interface()` method to customize appearance.

#### Additional Features
- Add new buttons/controls in the Gradio interface
- Extend the `LegalAssistantInterface` class with new methods
- Integrate additional tools or APIs

## 🔍 Troubleshooting

### Common Issues

1. **System Not Initializing**
   - Check your API keys are set correctly
   - Verify the selected model is available
   - Check internet connectivity

2. **Import Errors**
   - Ensure you're running from the correct directory
   - Verify all dependencies are installed
   - Check Python path configuration

3. **No Response from Agents**
   - Verify the legal agent system is properly initialized
   - Check for errors in the system status
   - Try reinitializing with a different model

### Debug Mode
Enable debug mode by setting `debug=True` in `launch_interface()` for detailed logging.

### Logs
Check the console output for detailed error messages and system status updates.

## 📝 Legal Disclaimer

This system is designed to assist with legal research and analysis but should not be considered as legal advice. Always consult with qualified legal professionals for specific legal matters.

## 🤝 Contributing

To contribute to the web interface:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the LLM Legal Assistant system. See the main repository for license information.