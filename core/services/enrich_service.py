import logging
from typing import Optional, List, Dict, Any
from core.interfaces.enricher import Enricher

class EnrichService:
    """Serviço para enriquecimento de metadados de ebooks."""
    
    def __init__(self, enricher: Optional[Enricher] = None):
        """
        Inicializa o serviço de enriquecimento.
        
        Args:
            enricher: Implementação do Enricher (opcional)
        """
        self.enricher = enricher
        self.logger = logging.getLogger(__name__)
    
    def set_enricher(self, enricher: Enricher):
        """Define o enriquecedor a ser usado."""
        self.enricher = enricher
    
    def enrich(self, csv_path: str, taxonomy_path: Optional[str] = None) -> Optional[str]:
        """
        Enriquece os metadados dos ebooks.
        
        Args:
            csv_path: Caminho para o arquivo CSV
            taxonomy_path: Caminho para o arquivo de taxonomia de temas
            
        Returns:
            Caminho para o arquivo CSV enriquecido ou None em caso de erro
        """
        if not self.enricher:
            self.logger.error("Nenhum enriquecedor configurado")
            return None
            
        try:
            return self.enricher.enrich(csv_path, taxonomy_path)
        except Exception as e:
            self.logger.error(f"Erro ao enriquecer dados: {str(e)}")
            return None