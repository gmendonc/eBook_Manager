import logging
from typing import Dict, Any, Optional
from core.interfaces.scanner import Scanner
from core.domain.source import Source

class ScanService:
    """Serviço para escaneamento de ebooks."""
    
    def __init__(self, scanner_registry: Dict[str, Scanner]):
        """
        Inicializa o serviço de escaneamento.
        
        Args:
            scanner_registry: Dicionário de scanners por tipo
        """
        self.scanner_registry = scanner_registry
        self.logger = logging.getLogger(__name__)
    
    def scan_source(self, source: Source) -> Optional[str]:
        """
        Escaneia uma fonte de ebooks.
        
        Args:
            source: Objeto Source com configuração da fonte
            
        Returns:
            Caminho para o arquivo CSV gerado ou None em caso de erro
        """
        source_type = source.type
        scanner = self.scanner_registry.get(source_type)
        
        if not scanner:
            self.logger.error(f"Tipo de fonte não suportado: {source_type}")
            return None
            
        try:
            return scanner.scan(source.path, source.config, source.id)
        except Exception as e:
            self.logger.error(f"Erro ao escanear fonte: {str(e)}")
            return None