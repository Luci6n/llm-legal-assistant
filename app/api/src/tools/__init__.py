from .vector_search import VectorSearch, SearchResult

# Note: Import WebSearch only if the module exists
try:
    from .web_search import WebSearch
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WebSearch = None
    WEB_SEARCH_AVAILABLE = False

# Import tools manager
try:
    from .tools_manager import (
        LegalToolsManager,
        LegalVectorSearchTool,
        CombinedSearchTool,
        create_legal_tools,
        create_vector_search_tool
    )
    TOOLS_MANAGER_AVAILABLE = True
except ImportError:
    TOOLS_MANAGER_AVAILABLE = False

# Define what gets exported
__all__ = ["VectorSearch", "SearchResult"]

if WEB_SEARCH_AVAILABLE:
    __all__.append("WebSearch")

if TOOLS_MANAGER_AVAILABLE:
    __all__.extend([
        "LegalToolsManager",
        "LegalVectorSearchTool", 
        "CombinedSearchTool",
        "create_legal_tools",
        "create_vector_search_tool"
    ])