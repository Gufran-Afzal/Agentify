from abc import ABC, abstractmethod

class ContentGenerator(ABC):
    @abstractmethod
    def generate(self, brief: dict) -> dict[str, str]:
        """
        Generate draft content from a brief.
        Returns a dictionary with keys: 'title', 'introduction', 'body', 'conclusion'.
        """
        pass
