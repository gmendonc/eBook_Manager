from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class Enricher(ABC):
    """Interface para enriquecedores de metadados de ebooks."""
    
    @abstractmethod
    def enrich(self, csv_path: str, taxonomy_path: Optional[str] = None) -> Optional[str]:
        """
        Enriquece os metadados dos ebooks a partir de um arquivo CSV.
        
        Args:
            csv_path: Caminho para o arquivo CSV com dados básicos
            taxonomy_path: Caminho opcional para o arquivo de taxonomia de temas
            
        Returns:
            Caminho para o arquivo CSV enriquecido ou None em caso de erro
        """
        pass