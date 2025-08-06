from .base_command import BaseCommand
import typer

class ExampleCommand(BaseCommand):
    def register(self, app: typer.Typer) -> None:
        @app.command()
        def example():
            """Example command"""
            print("Example command executed")
