import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from core.interfaces.scanner import Scanner

class FileSystemScanner(Scanner):
    """Scanner para fonte no sistema de arquivos local."""
    
    FORMATOS_EBOOK = {
        '.epub': 'EPUB',
        '.pdf': 'PDF',
        '.mobi': 'MOBI',
        '.azw': 'AZW',
        '.azw3': 'AZW3',
        '.kfx': 'KFX',
        '.txt': 'TXT'
    }
    
    def __init__(self):
        """Inicializa o scanner de sistema de arquivos."""
        self.logger = logging.getLogger(__name__)
    
    def scan(self, path: str, config: Optional[Dict[str, Any]] = None, source_id: Optional[str] = None) -> Optional[str]:
        """
        Escaneia ebooks em uma pasta no sistema de arquivos.
        
        Args:
            path: Caminho para a pasta
            config: Configurações adicionais (não utilizado)
            source_id: ID da fonte (não utilizado)
            
        Returns:
            Caminho para o arquivo CSV gerado ou None em caso de erro
        """
        self.logger.info(f"Escaneando pasta: {path}")
        
        if not os.path.exists(path):
            self.logger.error(f"Pasta {path} não encontrada")
            return None
        
        try:
            # Escanear pasta
            ebooks = self._scan_folder(path)
            
            # Gerar relatório CSV
            csv_name = f"ebooks_filesystem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            csv_path = os.path.join(os.getcwd(), csv_name)
            
            self._save_csv_report(ebooks, csv_path)
            
            self.logger.info(f"Relatório salvo em {csv_path}: {len(ebooks)} ebooks encontrados")
            return csv_path
            
        except Exception as e:
            self.logger.error(f"Erro ao escanear pasta no sistema de arquivos: {str(e)}")
            return None
    
    def _is_ebook(self, nome_arquivo: str) -> bool:
        """Verifica se um arquivo é um ebook baseado na extensão."""
        extensao = Path(nome_arquivo).suffix.lower()
        return extensao in self.FORMATOS_EBOOK
    
    def _get_formato(self, nome_arquivo: str) -> str:
        """Obtém o formato do ebook baseado na extensão."""
        extensao = Path(nome_arquivo).suffix.lower()
        return self.FORMATOS_EBOOK.get(extensao, 'Desconhecido')
    
    def _scan_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """
        Escaneia uma pasta e suas subpastas em busca de ebooks.
        
        Args:
            folder_path: Caminho para a pasta
            
        Returns:
            Lista de dicionários com informações dos ebooks
        """
        ebooks = []
        
        for root, _, files in os.walk(folder_path):
            for filename in files:
                if self._is_ebook(filename):
                    file_path = os.path.join(root, filename)
                    file_stat = os.stat(file_path)
                    
                    ebook = {
                        'Nome': filename,
                        'Formato': self._get_formato(filename),
                        'Tamanho(MB)': round(file_stat.st_size / (1024 * 1024), 2),
                        'Data Modificação': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'Caminho': file_path
                    }
                    ebooks.append(ebook)
                    self.logger.info(f"Ebook encontrado: {filename}")
        
        return ebooks
    
    def _save_csv_report(self, ebooks: List[Dict[str, Any]], csv_path: str) -> None:
        """
        Salva os dados dos ebooks em um arquivo CSV.
        
        Args:
            ebooks: Lista de dicionários com informações dos ebooks
            csv_path: Caminho para salvar o arquivo CSV
        """
        import pandas as pd
        
        try:
            df = pd.DataFrame(ebooks)
            df.to_csv(csv_path, index=False, encoding='utf-8')
        except Exception as e:
            self.logger.error(f"Erro ao salvar relatório CSV: {str(e)}")
            raise