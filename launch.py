"""
Modern launcher script for the Legal Assistant ChatInterface
"""

import os
import sys

from app.web.gradio_interface import launch_interface

if __name__ == "__main__":
    print("🏛️ Starting Malaysian Civil Law Legal Assistant - Simplified Interface...")
    print("📡 Interface will be available at: http://127.0.0.1:7862")
    print("💬 Basic chat interface with file upload support")
    print("📎 Supports: PDF, DOCX, TXT files and images")
    print("⚡ Real-time streaming responses enabled")
    print("🔧 Debug mode enabled for development")
    print("⚠️  Make sure your environment variables (OPENAI_API_KEY, etc.) are set")
    print()
    
    try:
        launch_interface(
            server_name="127.0.0.1",
            server_port=7860,
            share=False,  #Set to true to enable sharing via Gradio
            debug=False  #Set to true to enable debug mode
        )
    except KeyboardInterrupt:
        print("\n👋 Chat interface stopped by user")
    except Exception as e:
        print(f"❌ Error starting chat interface: {e}")
        sys.exit(1)