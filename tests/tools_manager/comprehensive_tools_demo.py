"""
Comprehensive demo showing how to use the Legal Tools with LangChain
This demonstrates the complete integration between VectorSearch and WebSearch tools.
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Load environment variables
load_dotenv()

def demo_tools_without_llm():
    """Demo the tools directly without LangChain agent"""
    print("=== Direct Tools Demo ===\n")
    
    from app.api.src.tools.tools_manager import LegalToolsManager
    
    # Create tools manager
    manager = LegalToolsManager()
    
    # Get all tools
    tools = manager.get_tools(include_web_search=True)
    
    print(f"📦 Available tools: {len(tools)}")
    for tool in tools:
        print(f"   - {tool.name}: {tool.description[:60]}...")
    print()
    
    # Test vector search tool directly
    print("🔍 Testing Legal Vector Search:")
    vector_tool = manager.legal_vector_tool
    
    vector_result = vector_tool.invoke({
        "query": "contract law principles",
        "collections": "all", 
        "top_k": 3,
        "retriever_type": "hybrid"
    })
    
    print(f"Result: {vector_result}")
    print()
    
    # Test web search tool (if available)
    if manager.web_search_tool and os.getenv("SERPER_API_KEY"):
        print("🌐 Testing Web Search:")
        web_result = manager.web_search_tool.invoke({
            "query": "latest contract law developments 2024"
        })
        print(f"Result: {web_result[:300]}...")
        print()
        
        # Test combined search
        if manager.combined_tool:
            print("🔄 Testing Combined Search:")
            combined_result = manager.combined_tool.invoke({
                "query": "AI liability legal framework",
                "include_vector_search": True,
                "include_web_search": True,
                "top_k": 2
            })
            print(f"Result: {combined_result[:400]}...")
    else:
        print("ℹ️ Web search not available (SERPER_API_KEY not set)")
    
    return tools

def demo_with_mock_llm():
    """Demo with a mock LLM-like interface"""
    print("\n=== Mock LLM Agent Demo ===\n")
    
    from app.api.src.tools.tools_manager import create_legal_tools
    
    # Create tools
    tools = create_legal_tools(include_web_search=True)
    
    # Simulate an LLM agent choosing tools for different queries
    scenarios = [
        {
            "query": "What are the key elements of a valid contract?",
            "recommended_tool": "legal_vector_search",
            "reasoning": "This asks for established legal principles, best found in legal documents"
        },
        {
            "query": "Recent changes in GDPR enforcement 2024",
            "recommended_tool": "combined_search", 
            "reasoning": "Needs both legal foundation and recent developments"
        },
        {
            "query": "Current status of AI regulation bill",
            "recommended_tool": "WebSearch",
            "reasoning": "Asks for very recent information not in legal database"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"🤖 Scenario {i}: {scenario['query']}")
        print(f"💭 Agent reasoning: {scenario['reasoning']}")
        print(f"🔧 Recommended tool: {scenario['recommended_tool']}")
        
        # Find the recommended tool
        selected_tool = None
        for tool in tools:
            if tool.name == scenario['recommended_tool']:
                selected_tool = tool
                break
        
        if selected_tool:
            try:
                # Execute tool with appropriate parameters
                if selected_tool.name == "legal_vector_search":
                    result = selected_tool.invoke({
                        "query": scenario['query'],
                        "collections": "all",
                        "top_k": 2
                    })
                elif selected_tool.name == "WebSearch":
                    result = selected_tool.invoke({
                        "query": scenario['query']
                    })
                elif selected_tool.name == "combined_search":
                    result = selected_tool.invoke({
                        "query": scenario['query'],
                        "include_vector_search": True,
                        "include_web_search": True,
                        "top_k": 2
                    })
                
                print(f"📋 Result: {result[:200]}...")
                
            except Exception as e:
                print(f"❌ Tool execution failed: {e}")
        
        print("-" * 60)

def demo_langchain_agent():
    """Demo with actual LangChain agent (requires OpenAI API key)"""
    print("\n=== LangChain Agent Demo ===\n")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_key:
        print("ℹ️ OpenAI API key not found, skipping LangChain agent demo")
        print("   Set OPENAI_API_KEY in your .env file to enable this demo")
        return
    
    try:
        from langchain_agent_example import create_simple_legal_agent
        
        print("🤖 Creating legal research agent...")
        agent = create_simple_legal_agent(
            include_web_search=True,
            model_name="gpt-3.5-turbo"
        )
        
        # Test query
        query = "What are the main defenses to a breach of contract claim?"
        
        print(f"🔍 Agent query: {query}")
        print("🤔 Agent thinking...")
        
        result = agent.research(query)
        
        if result["success"]:
            print("✅ Agent response:")
            print(result["answer"])
            
            print("\n🔧 Tools used:")
            for step in result["intermediate_steps"]:
                tool_input = step[0]
                print(f"   - {tool_input.tool}: {tool_input.tool_input}")
        else:
            print(f"❌ Agent failed: {result['error']}")
        
    except ImportError as e:
        print(f"❌ LangChain dependencies not available: {e}")
    except Exception as e:
        print(f"❌ Agent demo failed: {e}")

def show_usage_summary():
    """Show a summary of how to use the tools"""
    print("\n" + "="*60)
    print("📚 USAGE SUMMARY")
    print("="*60)
    
    print("""
🔧 Quick Setup:
   from app.api.src.tools.tools_manager import create_legal_tools
   tools = create_legal_tools(include_web_search=True)

🔍 Direct Tool Usage:
   # Vector search only
   vector_tool = tools[0]  # legal_vector_search
   result = vector_tool.invoke({
       "query": "contract law",
       "collections": "all",
       "top_k": 5
   })
   
   # Web search
   web_tool = tools[1]  # WebSearch 
   result = web_tool.invoke({"query": "recent legal news"})
   
   # Combined search
   combined_tool = tools[2]  # combined_search
   result = combined_tool.invoke({
       "query": "AI legal liability",
       "include_vector_search": True,
       "include_web_search": True,
       "top_k": 3
   })

🤖 LangChain Agent Usage:
   from langchain_agent_example import create_simple_legal_agent
   agent = create_simple_legal_agent(include_web_search=True)
   result = agent.research("Your legal question here")
   print(result["answer"])

📋 Available Collections:
   - legal_cases: Court cases and legal precedents
   - legislation: Laws, statutes, and regulations
   - all: Search both collections

🔍 Search Types:
   - hybrid: Vector similarity + BM25 (recommended)
   - vector: Semantic similarity only
   - bm25: Keyword matching only

⚙️ Environment Variables:
   - SERPER_API_KEY: For web search (optional)
   - OPENAI_API_KEY: For LangChain agents (optional)
""")

def main():
    """Run all demos"""
    print("🏛️ Legal Tools Comprehensive Demo")
    print("=" * 50)
    
    try:
        # Demo tools directly
        tools = demo_tools_without_llm()
        
        # Demo with mock LLM reasoning
        demo_with_mock_llm()
        
        # Demo with actual LangChain agent
        demo_langchain_agent()
        
        # Show usage summary
        show_usage_summary()
        
        print("\n🎉 Demo completed successfully!")
        print(f"✅ {len(tools)} tools are ready for use with your LLM")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
