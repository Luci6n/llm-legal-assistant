from retrieval.vdb_retriever import VDBRetriever

class VectorSearch:
    def __init__(self, vdb_retriever: VDBRetriever):
        self.vdb_retriever = vdb_retriever

    def run_search(self, query: str, top_k: int = 5) -> str:
        results = self.vdb_retriever.get_relevant_documents(query, top_k=top_k)
        return "\n".join([doc.page_content for doc in results])