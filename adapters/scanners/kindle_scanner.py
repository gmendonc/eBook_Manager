import logging
import os
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from core.interfaces.scanner import Scanner

class KindleScanner(Scanner):
    """Scanner para biblioteca do Kindle."""
    
    def __init__(self):
        """Inicializa o scanner de Kindle."""
        self.logger = logging.getLogger(__name__)
    
    def scan(self, path: str, config: Optional[Dict[str, Any]] = None, source_id: Optional[str] = None) -> Optional[str]:
        """
        Escaneia a biblioteca do Kindle a partir de um arquivo CSV exportado.
        
        Args:
            path: Caminho para o arquivo CSV exportado da biblioteca Kindle
            config: Configurações adicionais (não utilizado)
            source_id: ID da fonte (não utilizado)
            
        Returns:
            Caminho para o arquivo CSV gerado ou None em caso de erro
        """
        self.logger.info(f"Escaneando biblioteca Kindle: {path}")
        
        if not os.path.exists(path):
            self.logger.error(f"Arquivo {path} não encontrado")
            return None
            
        if not path.endswith('.csv'):
            self.logger.error(f"O caminho deve apontar para um arquivo CSV exportado da biblioteca Kindle")
            return None
        
        try:
            # Ler CSV existente
            kindle_df = pd.read_csv(path)
            
            # Processar dados
            ebooks = self._process_kindle_data(kindle_df)
            
            # Gerar relatório CSV
            csv_name = f"ebooks_kindle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            csv_path = os.path.join(os.getcwd(), csv_name)
            
            self._save_csv_report(ebooks, csv_path)
            
            self.logger.info(f"Relatório salvo em {csv_path}: {len(ebooks)} ebooks encontrados")
            return csv_path
            
        except Exception as e:
            self.logger.error(f"Erro ao processar biblioteca Kindle: {str(e)}")
            return None
    
    def _process_kindle_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Processa os dados do CSV exportado do Kindle.
        
        Args:
            df: DataFrame do pandas com os dados do Kindle
            
        Returns:
            Lista de dicionários com informações dos ebooks
        """
        ebooks = []
        
        for _, row in df.iterrows():
            try:
                # Campos esperados no CSV do Kindle: "Title", "Author", "ASIN", etc.
                title = row.get('Title', '')
                author = row.get('Author', '')
                asin = row.get('ASIN', '')
                
                ebook = {
                    'Nome': f"{title} - {author}.azw",
                    'Formato': "AZW",
                    'Tamanho(MB)': 0,  # Não disponível no CSV do Kindle
                    'Data Modificação': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Caminho': f"kindle://{asin}",
                    'Titulo_Extraido': title,
                    'Autor_Extraido': author,
                    'ASIN': asin
                }
                ebooks.append(ebook)
            except Exception as e:
                self.logger.warning(f"Erro ao processar linha no CSV do Kindle: {str(e)}")
        
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