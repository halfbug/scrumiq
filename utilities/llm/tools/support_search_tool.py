from langchain_core.tools import tool
from utilities.vectorstore import PineconeVectorStoreHandler
import json

@tool
def support_search(query: str) -> str:
    """
    Search for relevant support documents using semantic search in the 'support' namespace.

    Args:
        query: The search query in natural language.

    Returns:
        Formatted context string from relevant support documents.
    """
    print(f"support_search invoked with query: {query}")
    try:
        handler = PineconeVectorStoreHandler()
        vectorstore = handler.get_vector_store()
        results = vectorstore.similarity_search(query, k=3, namespace="support")
        print(f"Support search results: {len(results)} documents found.")
        formatted_context = format_docs(results)
        return formatted_context
    except Exception as e:
        return f"Error searching support content: {str(e)}"


def format_docs(docs) -> str:
    """Format search results into JSON context for the LLM"""
    if not docs:
        return json.dumps([])

    formatted = []
    for doc in docs:
        metadata = doc.metadata
        formatted.append({
            "metadata": metadata,
            "content": doc.page_content
        })

    return json.dumps(formatted)
