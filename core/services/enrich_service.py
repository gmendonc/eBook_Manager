import logging
from typing import Optional, List, Dict, Any
from core.interfaces.enricher import Enricher

class EnrichService:
    """Serviço para enriquecimento de metadados de ebooks."""
    
    def __init__(self, enricher_registry: Optional[Dict[str, Enricher]] = None, default_enricher: Optional[str] = None):
        """
        Inicializa o serviço de enriquecimento.
        
        Args:
            enricher_registry: Dicionário de enriquecedores disponíveis
            default_enricher: Nome do enriquecedor padrão
        """
        self.enricher_registry = enricher_registry or {}
        self.active_enricher_name = default_enricher
        self.logger = logging.getLogger(__name__)
    
    def register_enricher(self, name: str, enricher: Enricher) -> bool:
        """
        Registra um novo enriquecedor.
        
        Args:
            name: Nome do enriquecedor
            enricher: Implementação do Enricher
            
        Returns:
            True se o registro foi bem-sucedido
        """
        if name in self.enricher_registry:
            self.logger.warning(f"Enriquecedor '{name}' já registrado. Substituindo...")
        
        self.enricher_registry[name] = enricher
        
        # Se for o primeiro enriquecedor registrado, defina-o como ativo
        if not self.active_enricher_name and self.enricher_registry:
            self.active_enricher_name = name
            
        return True
    
    def set_active_enricher(self, name: str) -> bool:
        """
        Define o enriquecedor ativo.
        
        Args:
            name: Nome do enriquecedor a ser ativado
            
        Returns:
            True se o enriquecedor foi ativado com sucesso
        """
        if name not in self.enricher_registry:
            self.logger.error(f"Enriquecedor '{name}' não encontrado")
            return False
            
        self.active_enricher_name = name
        return True
    
    def get_active_enricher(self) -> Optional[Enricher]:
        """
        Obtém o enriquecedor ativo.
        
        Returns:
            Enriquecedor ativo ou None se nenhum estiver ativo
        """
        if not self.active_enricher_name:
            return None
            
        return self.enricher_registry.get(self.active_enricher_name)
    
    def get_available_enrichers(self) -> List[str]:
        """
        Obtém a lista de enriquecedores disponíveis.
        
        Returns:
            Lista de nomes de enriquecedores
        """
        return list(self.enricher_registry.keys())
    
    def enrich(self, csv_path: str, taxonomy_path: Optional[str] = None, enricher_name: Optional[str] = None) -> Optional[str]:
        """
        Enriquece os metadados dos ebooks.
        
        Args:
            csv_path: Caminho para o arquivo CSV
            taxonomy_path: Caminho para o arquivo de taxonomia de temas
            enricher_name: Nome do enriquecedor a ser usado (opcional, usa o ativo se não especificado)
            
        Returns:
            Caminho para o arquivo CSV enriquecido ou None em caso de erro
        """
        # Determinar qual enriquecedor usar
        if enricher_name:
            enricher = self.enricher_registry.get(enricher_name)
            if not enricher:
                self.logger.error(f"Enriquecedor '{enricher_name}' não encontrado")
                return None
        else:
            enricher = self.get_active_enricher()
            
        if not enricher:
            self.logger.error("Nenhum enriquecedor configurado")
            return None
            
        try:
            return enricher.enrich(csv_path, taxonomy_path)
        except Exception as e:
            self.logger.error(f"Erro ao enriquecer dados: {str(e)}")
            return None