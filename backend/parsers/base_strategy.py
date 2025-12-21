from abc import ABC, abstractmethod
from typing import List, Any
from app.schemas.normalization import UnifiedTransaction

class BaseStrategy(ABC):
    """
    The Abstract Base Class that all banking parsers must inherit from.
    Enforces that every parser has a 'parse' method returning UnifiedTransaction objects.
    """
    @abstractmethod
    def parse(self, content: Any, **kwargs) -> List[UnifiedTransaction]:
        """
        Args:
            content: The raw file content (bytes, str, or file-like object).
            **kwargs: Extra arguments like 'column_mapping' for CSVs.
            
        Returns:
            List[UnifiedTransaction]: A list of normalized transaction objects.
        """
        pass