import logging
import os
from langchain_core.tools import tool
from utilities.database.models.search_index import SearchIndex
from utilities.vectorstore import PineconeVectorStoreHandler
import json

@tool
def content_search(query: str, publication_ids_array: list[str], additional_filter_criteria: dict = None) -> dict:
    """
    Search for relevant documents within the user's publications using hybrid search (semantic + keyword).

    Args:
        query: The search query in natural language.
        top_k: Number of results to return (default: 3).
        publication_ids_array: List of publication IDs (as strings) to filter the search.
        additional_filter_criteria: Optional dict of additional filter criteria to merge into the search filter.

    Returns:
        Formatted context string from relevant documents.
    """
    print(f"content_search invoked with query: {query}, publication_ids_array: {publication_ids_array}, additional_filter_criteria: {additional_filter_criteria}")
    try:
       
        print("publication_ids_array", publication_ids_array)
        # Apply multi-publication filter
        filter_criteria = {
            "publication_id": {"$in": publication_ids_array}
        } if publication_ids_array else {}
        # Merge in any additional filter criteria
        if additional_filter_criteria:
            for key, value in additional_filter_criteria.items():
                filter_criteria[key] = value
        print(f"Filter criteria applied: {filter_criteria}")
        handler = PineconeVectorStoreHandler()
        vectorstore = handler.get_vector_store()

        # Semantic search
        semantic_results = vectorstore.similarity_search(
            query,
            k=3,
            filter=filter_criteria
        )
        print(f"Semantic search results: {len(semantic_results)} documents found.") 
       
        formatted_context = format_docs(semantic_results)

        search_index_id = None
        try:
            search_index = SearchIndex(
                query=query,
                sources=formatted_context,
    
            )
            search_index.save()
            search_index_id = str(search_index.id)
            # formatted_context["metadata"]["internal_source_url"] = f"{os.environ['SEARCH_URL']}/{search_index_id}"
        except Exception as e:
            logging.error(f"Failed to save to SearchIndex: {e}")

        return {"text" : formatted_context, "internal_source_url": f"{os.environ['SEARCH_URL']}/{search_index_id}"} if search_index_id else formatted_context

    except Exception as e:
        return f"Error searching content: {str(e)}"


def format_docs(docs) -> str:
    """Format search results into JSON context for the LLM"""
    if not docs:
        return json.dumps([])

    formatted = []
    for doc in docs:
        metadata = doc.metadata
        # pub_id = metadata.get('publication_id', 'Unknown')
        # pdf_url = metadata.get('pdf_url', 'N/A')
        # doc_type = metadata.get('type', 'document')
        formatted.append({
            "metadata": metadata,
            "content": doc.page_content
        })

    return json.dumps(formatted)

def merge_and_rerank(semantic_results, keyword_results, top_k):
    """
    Merge semantic and keyword search results, remove duplicates, and rerank.
    Documents appearing in both are prioritized.
    """
    # Use doc id or page_content as unique key
    def doc_id(doc):
        # Prefer a unique id if available, else fallback to content hash
        return getattr(doc, "id", None) or hash(doc.page_content)

    seen = {}
    # Assign a score: +2 if in both, +1 if only in one
    for doc in semantic_results:
        key = doc_id(doc)
        seen[key] = {"doc": doc, "score": 1}
    for doc in keyword_results:
        key = doc_id(doc)
        if key in seen:
            seen[key]["score"] += 1  # boost if in both
        else:
            seen[key] = {"doc": doc, "score": 1}
    # Sort by score descending, then by original order
    sorted_docs = sorted(seen.values(), key=lambda x: -x["score"])
    # Return only the doc objects, up to top_k
    return [item["doc"] for item in sorted_docs[:top_k]]