from abc import ABC, abstractmethod


class ModelBase(ABC):
    """Abstract class for the tool classes."""

    def __init__(self, tool_name, **kwargs):
        self.tool_name = tool_name
        self.model = self._get_model(**kwargs)

    @abstractmethod
    def _get_model(self, **kwargs):
        """Get the model for the tool. Accepts arbitrary keyword arguments."""
        pass

    @abstractmethod
    def use(self, prompt: str = "Hello, world!") -> str:
        """Use the tool with the given prompt."""
        pass

