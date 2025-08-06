import typer
from rich.console import Console
from core.initialize import set_environment_variables

console = Console()

class BaseCommand:
    """Base class for all CLI commands"""
    
    def __init__(self):
        set_environment_variables()
    
    def register(self, app: typer.Typer) -> None:
        """Default register implementation"""
        pass

    @classmethod
    def command(cls, app: typer.Typer):
        """Class decorator to register command"""
        instance = cls()
        instance.register(app)
        return cls
