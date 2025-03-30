from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class Scanner(ABC):
    """Interface para scanners de ebooks."""
    
    @abstractmethod
    def scan(self, path: str, config: Optional[Dict[str, Any]] = None, source_id: Optional[str] = None) -> Optional[str]:
        """
        Escaneia ebooks e retorna o caminho do arquivo CSV gerado.
        
        Args:
            path: Caminho para a fonte de ebooks
            config: Configurações específicas para o scanner
            source_id: Identificador da fonte para buscar credenciais armazenadas
            
        Returns:
            Caminho para o arquivo CSV gerado ou None em caso de erro
        """
        pass