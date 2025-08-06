from typing import Optional, Dict, Any
from langchain.tools import Tool
from utilities.vectorstore import PineconeVectorStoreHandler

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

class ArticleRetrievalTool:
    def __init__(self):
        self.handler = PineconeVectorStoreHandler()
        self.tool = Tool(
            name="article_retrieval",
            description="Retrieves relevant articles based on query and publication ID",
            func=self.retrieve_articles
        )

    def retrieve_articles(self, query: str, publication_id: Optional[str] = None) -> str:
        """Retrieve relevant articles from vector store"""
        vectorstore = self.handler.get_vector_store()
        filter_criteria = {"publication_id": publication_id} if publication_id else {}
        
        context = vectorstore.similarity_search(
            query,
            k=3,
            filter=filter_criteria
        )
        return format_docs(context)
