"""
Test script for the combined legal tools integration.
Tests the tools manager and LangChain compatibility.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Load environment variables
load_dotenv()

def test_tools_manager():
    """Test the basic tools manager functionality"""
    print("=== Testing Tools Manager ===\n")
    
    try:
        from app.api.src.tools.tools_manager import LegalToolsManager, create_legal_tools
        
        # Test tools manager creation
        print("📦 Creating tools manager...")
        manager = LegalToolsManager()
        
        # Test tool retrieval
        print("🔧 Getting tools...")
        tools = manager.get_tools(include_web_search=True)
        
        print(f"✅ Created {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description[:60]}...")
        
        # Test collection stats
        print("\n📊 Collection statistics:")
        stats = manager.get_collection_stats()
        for collection, info in stats.items():
            print(f"   {collection}: {info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tools manager test failed: {e}")
        return False

def test_vector_search_tool():
    """Test the vector search tool individually"""
    print("\n=== Testing Vector Search Tool ===\n")
    
    try:
        from app.api.src.tools.tools_manager import create_vector_search_tool
        
        # Create vector search tool
        print("🔍 Creating vector search tool...")
        tool = create_vector_search_tool()
        
        # Test with a simple query
        print("🔎 Testing search query...")
        query = "contract law"
        result = tool._run(
            query=query,
            collections="all",
            top_k=3,
            retriever_type="hybrid"
        )
        
        print(f"✅ Search completed. Result length: {len(result)} characters")
        print(f"📝 Sample result: {result[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector search tool test failed: {e}")
        return False

def test_web_search_tool():
    """Test the web search tool individually"""
    print("\n=== Testing Web Search Tool ===\n")
    
    try:
        from app.api.src.tools.web_search import WebSearch
        
        # Check if SERPER_API_KEY is available
        if not os.getenv("SERPER_API_KEY"):
            print("⚠️ SERPER_API_KEY not found, skipping web search test")
            return True
        
        # Create web search tool
        print("🌐 Creating web search tool...")
        tool = WebSearch()
        
        # Test with a simple query
        print("🔎 Testing web search query...")
        query = "legal research 2024"
        result = tool._run(query=query)
        
        print(f"✅ Web search completed. Result length: {len(result)} characters")
        print(f"📝 Sample result: {result[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Web search tool test failed: {e}")
        return False

async def test_combined_tool():
    """Test the combined search tool"""
    print("\n=== Testing Combined Search Tool ===\n")
    
    try:
        from app.api.src.tools.tools_manager import LegalToolsManager
        
        # Create tools manager
        print("🔄 Creating combined search tool...")
        manager = LegalToolsManager()
        
        if not manager.combined_tool:
            print("⚠️ Combined tool not available (likely missing SERPER_API_KEY)")
            return True
        
        # Test combined search
        print("🔎 Testing combined search...")
        result = await manager.combined_tool._arun(
            query="artificial intelligence law",
            include_vector_search=True,
            include_web_search=True,
            top_k=2
        )
        
        print(f"✅ Combined search completed. Result length: {len(result)} characters")
        print(f"📝 Sample result: {result[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Combined tool test failed: {e}")
        return False

def test_langchain_compatibility():
    """Test LangChain compatibility"""
    print("\n=== Testing LangChain Compatibility ===\n")
    
    try:
        from app.api.src.tools.tools_manager import create_legal_tools
        from langchain_core.tools import BaseTool
        
        # Create tools
        print("🔗 Creating LangChain-compatible tools...")
        tools = create_legal_tools(include_web_search=False)  # Vector only for testing
        
        # Verify they are BaseTool instances
        for tool in tools:
            assert isinstance(tool, BaseTool), f"Tool {tool.name} is not a BaseTool instance"
            print(f"   ✅ {tool.name} is LangChain compatible")
        
        # Test tool invocation
        if tools:
            print("🔎 Testing tool invocation...")
            first_tool = tools[0]
            
            # Test the tool interface
            result = first_tool.invoke({"query": "test query", "top_k": 2})
            print(f"✅ Tool invocation successful. Result type: {type(result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ LangChain compatibility test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("🧪 Legal Tools Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Tools Manager", test_tools_manager),
        ("Vector Search Tool", test_vector_search_tool),
        ("Web Search Tool", test_web_search_tool),
        ("Combined Tool", test_combined_tool),
        ("LangChain Compatibility", test_langchain_compatibility),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running {test_name} test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                success = await test_func()
            else:
                success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Tools are ready for use.")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")
    
    return passed_tests == total_tests

def main():
    """Main test function"""
    try:
        # Run async tests
        success = asyncio.run(run_all_tests())
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test runner crashed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
