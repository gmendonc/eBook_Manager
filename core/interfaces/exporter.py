from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class Exporter(ABC):
    """Interface para exportadores de ebooks."""
    
    @abstractmethod
    def export(self, csv_path: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Exporta dados de ebooks para um sistema externo.
        
        Args:
            csv_path: Caminho para o arquivo CSV com dados dos ebooks
            config: Configurações específicas para o exportador
            
        Returns:
            True se a exportação foi bem-sucedida, False caso contrário
        """
        pass