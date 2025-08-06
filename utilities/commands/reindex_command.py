import os
import logging
import typer
from utilities.vectorstore import PineconeVectorStoreHandler
from utilities.textloader import load_documents_from_folder
from rich.console import Console
from rich.progress import track
from .base_command import BaseCommand

console = Console()

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def execute_reindex(dataset_folder: str = "./dataset"):
    """
    Execute reindexing of all documents with detailed logging.
    
    Args:
        dataset_folder (str): Path to the dataset folder
    
    Returns:
        dict: Status of the reindexing operation
    """
    setup_logging()
    console.print("[bold blue]Starting reindexing process...[/bold blue]")
    
    try:
        # Initialize vectorstore
        console.print("[yellow]Initializing Pinecone vector store...[/yellow]")
        vstorehandler = PineconeVectorStoreHandler()
        
        # Reset index
        console.print("[yellow]Resetting existing index...[/yellow]")
        vstorehandler.reset_index()
        
        # Load and process documents
        console.print(f"[yellow]Loading documents from {dataset_folder}...[/yellow]")
        docs = load_documents_from_folder(dataset_folder)
        
        console.print(f"[green]Successfully loaded {len(docs)} document chunks[/green]")
        
        # Create vector store
        console.print("[yellow]Creating vector store and uploading documents in batches...[/yellow]")
        total_batches = (len(docs) + 99) // 100  # Calculate total number of batches
        with console.status(f"[cyan]Uploading {len(docs)} documents in {total_batches} batches...[/cyan]", spinner="dots"):
            vectorstore = vstorehandler.get_vector_store(docs)
        
        console.print("[bold green]✓ Reindexing completed successfully![/bold green]")
        return {
            "status": "success",
            "message": "Data reindexed successfully",
            "chunks_processed": len(docs)
        }
        
    except Exception as e:
        print(e)
        error_msg = f"Failed to reindex data: {str(e)}"
        console.print(f"[bold red]Error: {error_msg}[/bold red]")
        logging.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

# @BaseCommand.command(app=typer.get_app())
class ReindexCommand(BaseCommand):
    """Command to reindex documents in the vector store"""
    
    def register(self, app: typer.Typer) -> None:
        @app.command()
        def reindex(
            dataset_folder: str = typer.Option("./dataset", help="Path to the dataset folder"),
            verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
        ):
            """Reindex all documents in the database"""
            result = execute_reindex(dataset_folder)
            if result["status"] == "error":
                raise typer.Exit(code=1)
            return result