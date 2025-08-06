import os
import importlib
import typer
from rich.console import Console

app = typer.Typer(help="RAG CLI Tool")
console = Console()

def register_commands(app: typer.Typer):
    """Automatically register all commands from the commands folder"""
    commands_dir = os.path.dirname(__file__)
    
    for filename in os.listdir(commands_dir):
        if filename.endswith('_command.py') and filename != 'base_command.py':
            try:
                module_name = f'utilities.commands.{filename[:-3]}'
                module = importlib.import_module(module_name)
                # Find class with register method and instantiate it
                for item in dir(module):
                    obj = getattr(module, item)
                    if isinstance(obj, type) and hasattr(obj, 'register'):
                        command = obj()
                        command.register(app)
                        # console.print(f"[green]Registered command from {filename}[/green]")
            except Exception as e:
                console.print(f"[red]Failed to load {filename}: {str(e)}[/red]")

register_commands(app)

if __name__ == "__main__":
    app()
