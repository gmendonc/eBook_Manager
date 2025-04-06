import logging
from typing import Optional, Dict, Any
from core.interfaces.exporter import Exporter

class ExportService:
    """Serviço para exportação de ebooks para sistemas externos."""
    
    def __init__(self, exporter: Optional[Exporter] = None):
        """
        Inicializa o serviço de exportação.
        
        Args:
            exporter: Implementação do Exporter (opcional)
        """
        self.exporter = exporter
        self.exporter_config = {}  # Configurações específicas
        self.logger = logging.getLogger(__name__)
    
    def set_exporter(self, exporter: Exporter):
        """Define o exportador a ser usado."""
        self.exporter = exporter
    
    def export(self, csv_path: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Exporta dados de ebooks para um sistema externo.
        
        Args:
            csv_path: Caminho para o arquivo CSV
            config: Configurações específicas para o exportador
            
        Returns:
            True se a exportação foi bem-sucedida, False caso contrário
        """
        if not self.exporter:
            self.logger.error("Nenhum exportador configurado")
            return False
        
        # Combinar configurações salvas com as fornecidas
        export_config = {**self.exporter_config}
        if config:
            export_config.update(config)
            
        try:
            return self.exporter.export(csv_path, export_config)
        except Exception as e:
            self.logger.error(f"Erro ao exportar dados: {str(e)}")
            return False