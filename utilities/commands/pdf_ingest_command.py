import os
import typer
import requests
import fitz  # PyMuPDF
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from .base_command import BaseCommand
from core.mongo_connect import MongoConnect
from utilities.vectorstore import PineconeVectorStoreHandler
from rich.console import Console
from rich.progress import track
import logging
from urllib.parse import quote

console = Console()

class PDFIngestCommand(BaseCommand):
    def __init__(self):
        self.temp_dir = Path("temp_pdfs")
        self.temp_dir.mkdir(exist_ok=True)
        self.mongo_collection = MongoConnect.get_collection('pdf_index')
        
        
    def download_pdf(self, url: str, file_path: Path) -> bool:
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            console.print(f"[red]Download failed for {url}[/red]: {str(e)}")
            return False

    def extract_text_from_pdf(self, file_path: Path) -> str:
        try:
            text_content = []
            with fitz.open(file_path) as doc:
                for page in doc:
                    text_content.append(page.get_text())
            return "\n".join(text_content)
        except Exception as e:
            logging.error(f"PDF parsing failed for {file_path}: {str(e)}")
            raise

    def chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        try:
            # Use similar chunking logic as in reindex_command
            chunks = []
            # Implement your chunking logic here
            # For example, split by paragraphs and combine until reaching desired length
            current_chunk = ""
            for paragraph in text.split("\n\n"):
                if len(current_chunk) + len(paragraph) < 800:
                    current_chunk += paragraph + "\n\n"
                else:
                    if current_chunk:
                        chunks.append({
                            "text": current_chunk.strip(),
                            "metadata": metadata
                        })
                    current_chunk = paragraph + "\n\n"
            
            if current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "metadata": metadata
                })
                
            return chunks
        except Exception as e:
            logging.error(f"Chunking failed: {str(e)}")
            raise

    def process_pending_documents(self, batch_size: int = 10):
        try:
            self.vector_store = PineconeVectorStoreHandler()
            pending_docs = list(self.mongo_collection.find({"status": "pending"}).limit(batch_size))
            if not pending_docs:
                print("No pending documents found. Retrying documents with error status...")
                pending_docs = list(self.mongo_collection.find({"status": "error"}).limit(batch_size))
                if pending_docs:
                    print("No pending documents found. Retrying documents with error status...")
            if pending_docs:
                console.print("[cyan]Processing pending documents...[/cyan]")

                for doc in pending_docs:
                    pdf_path = self.temp_dir / f"{doc['_id']}.pdf"
                    console.print(f"[blue]Processing document:[/blue] {doc['pdf_url']}")
                    
                    try:
                        # URL encode the pdf_url before downloading
                        encoded_url = quote(doc['pdf_url'], safe=':/?&=%')
                        # Download PDF
                        if not self.download_pdf(encoded_url, pdf_path):
                            self.update_status(doc['_id'], 'error', 'Download failed')
                            continue

                        # Extract text
                        text_content = self.extract_text_from_pdf(pdf_path)
                        
                        # Create chunks with metadata
                        metadata = {
                            "publication_id": doc['publication_id'],
                            "unit_id": doc['unit_id'],
                            "week_id": doc['week_id'],
                            "article_id": doc['article_id'],
                            "type": doc['type'],
                            "source_table": doc['source_table'],
                            "pdf_url": doc['pdf_url']
                        }
                        
                        chunks = self.chunk_text(text_content, metadata)
                        
                        # Upload to vector store
                        self.vector_store.add_texts([chunk["text"] for chunk in chunks],
                                                metadatas=[chunk["metadata"] for chunk in chunks])
                        
                        # Update status
                        self.update_status(doc['_id'], 'complete')
                        print(f"--Successfully processed --")
                    except Exception as e:
                        self.update_status(doc['_id'], 'error', str(e))
                        logging.error(f"Processing failed for {doc['pdf_url']}: {str(e)}")
                    
                    finally:
                        # Cleanup
                        if pdf_path.exists():
                            pdf_path.unlink()
        except Exception as e:
                logging.error(f"Batch processing failed: {str(e)}")
                raise

    def update_status(self, doc_id, status: str, error_message: str = None):
        update = {
            "status": status,
            "uploaded": status == 'complete',
            "updated_at": datetime.now()
        }
        if error_message:
            update["error_message"] = error_message
        
        self.mongo_collection.update_one(
            {"_id": doc_id},
            {"$set": update}
        )

    def register(self, app: typer.Typer) -> None:
        @app.command()
        def ingest_pdfs(
            batch_size: int = typer.Option(10, help="Number of documents to process"),
            verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
        ):
            """Process pending PDFs and add them to the vector store"""
            try:
                if verbose:
                    console.print("[bold blue]Starting PDF ingestion process...[/bold blue]")
                
                self.process_pending_documents(batch_size)
                
                if verbose:
                    # display summary of processed documents
                    processed_count = self.mongo_collection.count_documents({"status": "complete"})
                    total_count = self.mongo_collection.count_documents({})
                    total_pending = self.mongo_collection.count_documents({"status": "pending"})
                    total_error = self.mongo_collection.count_documents({"status": "error"})
                    console.print(f"[green]Processed {processed_count} documents successfully.[/green]")
                    console.print(f"[yellow]Total documents: {total_count}[/yellow]")
                    console.print(f"[yellow]Pending documents: {total_pending}[/yellow]")
                    console.print(f"[red]Documents with errors: {total_error}[/red]")   


                    console.print("[bold green]PDF ingestion completed successfully![/bold green]")
                    
            except Exception as e:
                console.print(f"[bold red]Error during PDF ingestion: {str(e)}[/bold red]")
                raise typer.Exit(code=1)
