import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import dropbox
from core.interfaces.scanner import Scanner

class DropboxScanner(Scanner):
    """Scanner para fonte no Dropbox."""
    
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
        """Inicializa o scanner de Dropbox."""
        self.logger = logging.getLogger(__name__)
    
    def scan(self, path: str, config: Optional[Dict[str, Any]] = None, source_id: Optional[str] = None) -> Optional[str]:
        """
        Escaneia ebooks em uma pasta no Dropbox.
        
        Args:
            path: Caminho para a pasta no Dropbox
            config: Configurações (deve conter token)
            source_id: ID da fonte (não utilizado)
            
        Returns:
            Caminho para o arquivo CSV gerado ou None em caso de erro
        """
        self.logger.info(f"Escaneando pasta Dropbox: {path}")
        
        if not config or 'token' not in config:
            self.logger.error("Token do Dropbox não configurado")
            return None
        
        token = config['token']
        
        try:
            # Inicializar cliente do Dropbox
            dbx = dropbox.Dropbox(token)
            
            # Escanear pasta
            ebooks = self._scan_folder(dbx, path)
            
            # Gerar relatório CSV
            csv_name = f"ebooks_dropbox_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            csv_path = os.path.join(os.getcwd(), csv_name)
            
            self._save_csv_report(ebooks, csv_path)
            
            self.logger.info(f"Relatório salvo em {csv_path}: {len(ebooks)} ebooks encontrados")
            return csv_path
            
        except Exception as e:
            self.logger.error(f"Erro ao escanear pasta no Dropbox: {str(e)}")
            return None
    
    def _is_ebook(self, nome_arquivo: str) -> bool:
        """Verifica se um arquivo é um ebook baseado na extensão."""
        extensao = Path(nome_arquivo).suffix.lower()
        return extensao in self.FORMATOS_EBOOK
    
    def _get_formato(self, nome_arquivo: str) -> str:
        """Obtém o formato do ebook baseado na extensão."""
        extensao = Path(nome_arquivo).suffix.lower()
        return self.FORMATOS_EBOOK.get(extensao, 'Desconhecido')
    
    def _scan_folder(self, dbx: dropbox.Dropbox, folder_path: str) -> List[Dict[str, Any]]:
        """
        Escaneia uma pasta no Dropbox em busca de ebooks.
        
        Args:
            dbx: Cliente do Dropbox
            folder_path: Caminho para a pasta
            
        Returns:
            Lista de dicionários com informações dos ebooks
        """
        ebooks = []
        
        try:
            result = dbx.files_list_folder(folder_path)
            
            # Processar resultados
            has_more = True
            while has_more:
                for entry in result.entries:
                    if isinstance(entry, dropbox.files.FileMetadata):
                        filename = entry.name
                        if self._is_ebook(filename):
                            ebook = {
                                'Nome': filename,
                                'Formato': self._get_formato(filename),
                                'Tamanho(MB)': round(entry.size / (1024 * 1024), 2),
                                'Data Modificação': entry.server_modified.strftime('%Y-%m-%d %H:%M:%S'),
                                'Caminho': f"dropbox://{folder_path}/{filename}"
                            }
                            ebooks.append(ebook)
                            self.logger.info(f"Ebook encontrado: {filename}")
                
                # Verificar se há mais resultados
                if result.has_more:
                    result = dbx.files_list_folder_continue(result.cursor)
                else:
                    has_more = False
                    
        except dropbox.exceptions.ApiError as e:
            self.logger.error(f"Erro na API do Dropbox: {str(e)}")
            raise
        
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