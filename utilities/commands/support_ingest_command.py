import typer
import csv
from pathlib import Path
from .base_command import BaseCommand
from utilities.vectorstore import PineconeVectorStoreHandler
from rich.console import Console

console = Console()

class SupportIngestCommand(BaseCommand):
    def __init__(self):
        self.csv_path = Path("utilities/swo_support.csv")

    def process_support_csv(self):
        chunks = []
        with open(self.csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                text = f"{row.get('meta_description', '')}\n{row.get('cleaned_markdown', '')}".strip()
                metadata = {
                    "type": row.get("type", ""),
                    "url": row.get("url", ""),
                    "title": row.get("title", ""),
                    "category_name": row.get("category_name", ""),
                    "section_name": row.get("section_name", "")
                }
                chunks.append({"text": text, "metadata": metadata})
                # console.print(f"Processed article:[cyan] {metadata['title']} [/cyan]")
        return chunks

    def ingest_support(self, verbose: bool = False):
        self.vector_store = PineconeVectorStoreHandler()
        if verbose:
            console.print("[bold blue]Starting support articles ingestion...[/bold blue]")
        
        chunks = self.process_support_csv()
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        total_batches = 1  # All docs in one batch for now
        with console.status(f"[cyan]Uploading {len(chunks)} documents in {total_batches} batches...[/cyan]", spinner="dots"):
            self.vector_store.add_texts(texts, metadatas=metadatas, namespace="support")
        if verbose:
            console.print(f"[bold green]Ingested {len(chunks)} support articles into Pinecone.[/bold green]")

    def register(self, app: typer.Typer) -> None:
        @app.command()
        def ingest_support(
            verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
        ):
            """Ingest support articles from swo_support.csv into Pinecone vector store."""
            self.ingest_support(verbose)
