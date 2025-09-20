import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path to handle imports correctly
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
sys.path.insert(0, project_root)

try:
    from IPython.display import display, Image
    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False
    print("IPython not available - will save images to files instead")

# Import using absolute path
from app.api.src.agents.routing import LegalAgentSystem

def test_graph_visualization():
    """Test and visualize the legal agent system graphs."""
    
    print("🧪 Testing Legal Agent System Graph Visualization")
    print("=" * 60)
    
    try:
        # Initialize the system
        print("📝 Initializing legal system...")
        a = LegalAgentSystem(model_name="openai:gpt-4o-mini")
        print("✅ Legal system initialized")
        
        # Test prebuilt supervisor graph
        print("\n🔍 Testing prebuilt supervisor graph...")
        try:
            supervisor = a._build_prebuilt_supervisor_graph()  # Note: added ()
            print("✅ Prebuilt supervisor graph created")
            
            # Try to visualize
            try:
                graph_data = supervisor.get_graph()
                print(f"📊 Graph nodes: {len(graph_data.nodes)}")
                print(f"📊 Graph edges: {len(graph_data.edges)}")
                
                # Print graph structure instead of image
                print("\n📋 Graph Structure:")
                print("Nodes:")
                for node in graph_data.nodes:
                    print(f"  - {node}")
                print("Edges:")
                for edge in graph_data.edges:
                    print(f"  - {edge}")
                
                # Try to generate mermaid diagram as fallback
                try:
                    mermaid_png = graph_data.draw_mermaid_png()
                    
                    if IPYTHON_AVAILABLE:
                        display(Image(mermaid_png))
                    else:
                        # Save to file
                        with open("prebuilt_supervisor_graph.png", "wb") as f:
                            f.write(mermaid_png)
                        print("📁 Prebuilt supervisor graph saved to: prebuilt_supervisor_graph.png")
                except Exception as viz_error:
                    print(f"⚠️ Could not generate prebuilt graph visualization: {viz_error}")
                
            except Exception as e:
                print(f"⚠️ Could not analyze prebuilt graph: {e}")
                
        except Exception as e:
            print(f"❌ Error with prebuilt supervisor: {e}")
        
        # Test custom supervisor graph
        print("\n🔍 Testing custom supervisor graph...")
        try:
            supervisor2 = a._build_custom_supervisor_graph()  # Note: added ()
            print("✅ Custom supervisor graph created")
            
            # Try to visualize
            try:
                graph_data2 = supervisor2.get_graph()
                print(f"📊 Graph nodes: {len(graph_data2.nodes)}")
                print(f"📊 Graph edges: {len(graph_data2.edges)}")
                
                # Generate mermaid diagram
                mermaid_png2 = graph_data2.draw_mermaid_png()
                
                if IPYTHON_AVAILABLE:
                    display(Image(mermaid_png2))
                else:
                    # Save to file
                    with open("custom_supervisor_graph.png", "wb") as f:
                        f.write(mermaid_png2)
                    print("📁 Custom supervisor graph saved to: custom_supervisor_graph.png")
                    
            except Exception as e:
                print(f"⚠️ Could not generate custom graph visualization: {e}")
                
        except Exception as e:
            print(f"❌ Error with custom supervisor: {e}")
        
        # Compare the two approaches
        print("\n📊 Comparison:")
        print("- Prebuilt supervisor: Uses langgraph-supervisor package")
        print("- Custom supervisor: Uses manual StateGraph construction")
        print("- Both should handle multi-agent coordination")
        
        # Test which one is actually being used
        print(f"\n🎯 Currently active graph type: {type(a.graph)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_graph_visualization()