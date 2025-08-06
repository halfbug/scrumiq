import os
import time
# from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import Pinecone
from pinecone import ServerlessSpec, PodSpec
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
# from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from rich.console import Console

console = Console()
# OPENAI_API_KEY = "<YOUR_OPENAI_API_KEY>"
# PINECONE_API_KEY = "<YOUR_PINECONE_API_KEY>"
# INDEX_NAME = "langchain-retrieval-augmentation-fast"
# os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
class PineconeVectorStoreHandler:
    def __init__(self, use_serverless=True, dimension=1536, cloud="aws", region="us-east-1"):
        """
        Initialize the PineconeVectorStoreHandler.

        Args:
            api_key (str): Pinecone API key.
            index_name (str): Name of the Pinecone index.
            use_serverless (bool): Whether to use serverless deployment. Default is True.
            dimension (int): Dimensionality of the embeddings. Default is 1536.
            cloud (str): Cloud provider for serverless spec. Default is 'aws'.
            region (str): Region for serverless spec. Default is 'us-east-1'.
        """
        try:
            print("index_name", os.environ['PINECONE_INDEX_NAME'])
            self.index_name = os.environ['PINECONE_INDEX_NAME']
            self.dimension = dimension
            self.use_serverless = use_serverless
            self.pc = Pinecone(api_key=os.environ['PINECONE_API_KEY'])
            self.spec = ServerlessSpec(cloud=cloud, region=region) if use_serverless else PodSpec()
            self.index = None
            self._initialize_index()
        except KeyError as e:
            raise ValueError(f"Missing environment variable: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to initialize Pinecone: {str(e)}")

    def _initialize_index(self):
        """Create or reset the Pinecone index."""
        try:
            print("...Initialize the Pinecone index")
            if not self.pc.has_index(self.index_name):
                self.pc.create_index(
                    self.index_name,
                    dimension=self.dimension,
                    metric="dotproduct",
                    spec=self.spec
                )
            while not self.pc.describe_index(self.index_name).status['ready']:
                time.sleep(1)
            self.index = self.pc.Index(self.index_name)
        except Exception as e:
            print(f"Error initializing index: {str(e)}")
            raise
    
    def is_index_exists(self):
        try:
            return self.pc.has_index(self.index_name)
        except Exception as e:
            print(f"Error checking index existence: {str(e)}")
            raise
    
    def reset_index(self):
        try:
            with console.status("[cyan]Deleting...[/cyan]", spinner="monkey"):
                self.pc.delete_index(self.index_name)
            with console.status("[cyan]Creating...[/cyan]", spinner="monkey"):
                self._initialize_index()
        except Exception as e:
            print(f"Error deleting & reinitializing index: {str(e)}")
            raise

    def get_vector_store(self, documents=[]):
        """
        Create a PineconeVectorStore and upsert documents in batches of 100.

        Args:
            documents (list): List of document chunks to upsert.

        Returns:
            PineconeVectorStore: Configured vector store.
        """
        try:
            embeddings = OpenAIEmbeddings()
            vector_store = PineconeVectorStore(index_name=self.index_name, embedding=embeddings)
            if len(documents) > 0:
                batch_size = 100
                MAX_REQUESTS_PER_MIN = 120
                MAX_TOKENS_PER_MIN = 150000
                tokens_per_doc = 800  # estimate or compute for a doc
                start_time = time.time()
                requests_sent = 0
                tokens_sent = 0
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    batch_tokens = len(batch) * tokens_per_doc # rough estimate; 
                    # Throttle by requests per minute
                    if requests_sent >= MAX_REQUESTS_PER_MIN or tokens_sent + batch_tokens > MAX_TOKENS_PER_MIN:
                        elapsed = time.time() - start_time
                        if elapsed < 60:
                            time.sleep(60 - elapsed)
                        # Reset counters after each minute
                        start_time = time.time()
                        requests_sent = 0
                        tokens_sent = 0
                    vector_store.add_documents(batch)
                    requests_sent += 1
                    tokens_sent += batch_tokens
            return vector_store
        except Exception as e:
            print(f"Error creating vector store: {str(e)}")
            raise

    def add_texts(self, texts: list, metadatas: list = None, namespace: str = None):
        """
        Add texts with metadata to the vector store with rate limiting.
        
        Args:
            texts (list): List of text strings to add
            metadatas (list, optional): List of metadata dicts for each text
        """
        try:
            embeddings = OpenAIEmbeddings()
            vector_store = PineconeVectorStore(index_name=self.index_name, embedding=embeddings)
            
            if len(texts) > 0:
                batch_size = 100
                MAX_REQUESTS_PER_MIN = 120
                MAX_TOKENS_PER_MIN = 150000
                tokens_per_doc = 800  # estimate per document
                
                start_time = time.time()
                requests_sent = 0
                tokens_sent = 0
                
                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i:i + batch_size]
                    batch_metadata = metadatas[i:i + batch_size] if metadatas else None
                    batch_tokens = len(batch_texts) * tokens_per_doc
                    
                    # Apply rate limiting
                    if requests_sent >= MAX_REQUESTS_PER_MIN or tokens_sent + batch_tokens > MAX_TOKENS_PER_MIN:
                        elapsed = time.time() - start_time
                        if elapsed < 60:
                            time.sleep(60 - elapsed)
                        start_time = time.time()
                        requests_sent = 0
                        tokens_sent = 0
                    
                    vector_store.add_texts(
                        texts=batch_texts,
                        metadatas=batch_metadata if batch_metadata else None,
                        namespace=namespace
                    )
                    
                    requests_sent += 1
                    tokens_sent += batch_tokens
                    
                    if requests_sent % 10 == 0:  # Log progress every 10 batches
                        console.print(f"[cyan]Processed {i + len(batch_texts)} documents...[/cyan]")
                        
            return vector_store
            
        except Exception as e:
            console.print(f"[red]Error adding texts to vector store: {str(e)}[/red]")
            raise


# # Example usage
# if __name__ == "__main__":
#     # Configure your API keys and index name
    

#     os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

#     # Initialize handler
#     handler = PineconeVectorStoreHandler()

#     # Example: Load and split documents
#     dataset_folder = "./dataset"
#     all_documents = []
#     for filename in os.listdir(dataset_folder):
#         file_path = os.path.join(dataset_folder, filename)
#         if filename.endswith(".txt") and os.path.isfile(file_path):
#             loader = TextLoader(file_path)
#             documents = loader.load()
#             text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
#             all_documents.extend(text_splitter.split_documents(documents))

#     # Add documents to the vector store
#     vector_store = handler.get_vector_store(all_documents)

#     print(f"Vector store created with {len(all_documents)} documents.")
