import os
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.config import config
from utilities.fileprocess import filter_html_and_save, get_file_content

# Set API keys
os.environ['OPENAI_API_KEY'] = config.OPENAI_API_KEY
os.environ['PINECONE_API_KEY'] = config.PINECONE_KEY

# Define Pinecone index name
index_name = config.PINECONE_INDEX_NAME

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings()

def load_documents_from_folder(folder_path, chunk_size=1000, chunk_overlap=100):
    """
    Loads and splits text documents from a folder.
    
    Args:
        folder_path (str): Path to the folder containing text files.
        chunk_size (int): Size of each chunk after splitting.
        chunk_overlap (int): Overlap size between chunks.

    Returns:
        list: A list of document chunks.
    """
    try:
        all_documents: list[str] = []
        # Iterate over all files and folders in the folder_path
        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                if filename.endswith(".txt") and os.path.isfile(file_path):  # Load only .txt files
                    print("---------->", file_path)
                    filter_html_and_save(file_path)
                    loader = TextLoader(file_path, autodetect_encoding=True)
                    documents = loader.load()
                    # print("loader done")
                    # Add publication_id to metadata
                    for doc in documents:
                        doc.metadata["publication_id"] = os.path.basename(root)  # Renamed from publish_id
                    all_documents.extend(documents)
        # Split documents into chunks using multiple separators
        text_splitter = RecursiveCharacterTextSplitter(
            separators=[
                ". ", "." ,        # Regular sentence boundary
                "\n\n", "\n",    # Line breaks (though not present in sample)
                ", ", ","          # Phrase separator
                " ",            # Word separator
                ""              # Character separator as fallback
            ],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        docs = text_splitter.split_documents(all_documents)
        return docs
    except Exception as e:
        print(e)
        print(f"Error loading and splitting documents: {e}")
        return []

# # Example usage
# dataset_folder = "./dataset"
# docs = load_documents_from_folder(dataset_folder)

# # Display the number of chunks loaded
# print(f"Loaded and split {len(docs)} chunks from files in '{dataset_folder}'.")
