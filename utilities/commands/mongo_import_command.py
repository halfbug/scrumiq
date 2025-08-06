from .base_command import BaseCommand
import typer
from datetime import datetime
from core.mongoengine_connect import init_mongoengine
from utilities.database.models.pdf_index import PDFIndex
import pandas as pd
from rich.console import Console

console = Console()

class MongoImportCommand(BaseCommand):
    def __init__(self):
        self.valid_types = ['assessment', 'printable', 'student edition', 'teacher resources']
        init_mongoengine()
        
    def validate_and_process_row(self, row):
        if not isinstance(row['type'], str) or row['type'].lower() not in self.valid_types:
            raise ValueError(f"Invalid type value: {row['type']}")
        
        return {
            'title': row.get('title'),
            'description': row.get('description'),
            'media_type': row.get('media_type', 'pdf'),
            'transcript': row.get('transcript'),
            'pdf_url': row['pdf_url'],
            'publication_id': int(row['publication_id']),
            'type': row['type'].lower(),
            'source_table': row['source_table'],
            'unit_id': int(row['unit_id']),
            'week_id': int(row['week_id']),
            'article_id': int(row['article_id']),
            'status': 'pending',
            'error_message': None,
            'uploaded': False,
            'created_at': datetime.now()
        }

    def register(self, app: typer.Typer) -> None:
        @app.command()
        def import_pdf_index(
            csv_path: str = typer.Argument(..., help="Path to the CSV file"),
            verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
        ):
            """Import PDF index data from CSV to MongoDB"""
            try:
                console.print("[bold blue]Starting PDF index import...[/bold blue]")
                if verbose:
                    console.print(f"[yellow]Reading CSV file: {csv_path}[/yellow]")
                df = pd.read_csv(csv_path)
                required_columns = ['pdf_url', 'publication_id', 'type', 'source_table', 
                                  'unit_id', 'week_id', 'article_id']
                if not all(col in df.columns for col in required_columns):
                    raise ValueError("CSV missing required columns")
                if verbose:
                    console.print(f"[cyan]CSV file contains {len(df)} rows[/cyan]")
                for _, row in df.iterrows():
                    document = self.validate_and_process_row(row.to_dict())
                    if verbose:
                        console.print(f"[green]Processing document[/green]")
                    # Upsert using mongoengine
                    PDFIndex.objects(pdf_url=document['pdf_url']).update_one(
                        **document,
                        upsert=True
                    )
                    if verbose:
                        console.print(f"Processed: [cyan] {document['pdf_url']} [/cyan]")
                
                console.print("[bold green]Import completed successfully![/bold green]")
                
            except Exception as e:
                console.print(f"[red]Error during import: {e}[/red]")
