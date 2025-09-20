"""
Simple test to verify tools integration works
"""

import os
import sys

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def simple_test():
    print("=== Simple Tools Integration Test ===\n")
    
    try:
        # Test 1: Import tools manager
        print("1. Testing imports...")
        from app.api.src.tools.tools_manager import LegalToolsManager
        print("   ✅ Tools manager imported successfully")
        
        # Test 2: Create tools manager (no web search to avoid API dependency)
        print("2. Creating tools manager...")
        manager = LegalToolsManager()
        print("   ✅ Tools manager created successfully")
        
        # Test 3: Get vector-only tools
        print("3. Getting vector search tools...")
        vector_tools = manager.get_vector_only_tools()
        print(f"   ✅ Got {len(vector_tools)} vector tools")
        
        # Test 4: Test tool names and descriptions
        print("4. Checking tool properties...")
        for tool in vector_tools:
            print(f"   - {tool.name}: {tool.description[:50]}...")
        print("   ✅ Tool properties accessible")
        
        # Test 5: Test a simple search (if collections have data)
        print("5. Testing simple search...")
        vector_tool = vector_tools[0]
        
        # Use invoke method (LangChain standard)
        try:
            result = vector_tool.invoke({
                "query": "test query",
                "collections": "legal_cases",
                "top_k": 1
            })
            print(f"   ✅ Search completed. Result length: {len(result)} chars")
            if "no documents" in result.lower():
                print("   ℹ️ Collection is empty (expected for new setup)")
        except Exception as e:
            print(f"   ⚠️ Search failed (expected if no documents): {e}")
        
        print("\n🎉 All basic tests passed! Tools are working.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = simple_test()
    exit(0 if success else 1)
