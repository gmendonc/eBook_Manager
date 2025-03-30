import logging
import os
import re
from typing import Dict, Any, Optional, List
import pandas as pd
from core.interfaces.enricher import Enricher

class BasicEnricher(Enricher):
    """Implementação básica do enriquecedor que extrai apenas autor e título dos nomes de arquivo."""
    
    def __init__(self):
        """Inicializa o enriquecedor básico."""
        self.logger = logging.getLogger(__name__)
    
    def enrich(self, csv_path: str, taxonomy_path: Optional[str] = None) -> Optional[str]:
        """
        Enriquece os metadados dos ebooks com informações básicas.
        
        Args:
            csv_path: Caminho para o arquivo CSV com dados básicos
            taxonomy_path: Ignorado nesta implementação
            
        Returns:
            Caminho para o arquivo CSV enriquecido ou None em caso de erro
        """
        if not os.path.exists(csv_path):
            self.logger.error(f"Arquivo CSV não encontrado: {csv_path}")
            return None
            
        output_path = csv_path.replace('.csv', '_enriched.csv')
        if output_path == csv_path:
            output_path = os.path.splitext(csv_path)[0] + '_enriched.csv'
        
        try:
            # Processar o CSV
            enriched_ebooks = self._enrich_ebooks_from_csv(csv_path)
            
            # Salvar CSV enriquecido
            df_enriched = pd.DataFrame(enriched_ebooks)
            df_enriched.to_csv(output_path, index=False, encoding='utf-8')
            
            self.logger.info(f"Dados enriquecidos básicos salvos em {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Erro ao enriquecer dados: {str(e)}")
            return None
    
    def _enrich_ebooks_from_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Enriquece os metadados dos ebooks com informações básicas.
        
        Args:
            csv_path: Caminho para o arquivo CSV
            
        Returns:
            Lista de dicionários com dados enriquecidos
        """
        enriched_ebooks = []
        
        try:
            # Ler dados do CSV
            df = pd.read_csv(csv_path)
            
            for _, row in df.iterrows():
                try:
                    # Converter row para dict para facilitar o processamento
                    row_dict = row.to_dict()
                    
                    # Copiar dados básicos
                    enriched_ebook = dict(row_dict)
                    
                    # Extrair autor e título do nome do arquivo
                    nome_arquivo = row_dict.get('Nome', '')
                    if nome_arquivo:
                        autor, titulo = self._extract_author_title(nome_arquivo)
                        enriched_ebook['Autor_Extraido'] = autor
                        enriched_ebook['Titulo_Extraido'] = titulo
                    
                    enriched_ebooks.append(enriched_ebook)
                    
                except Exception as e:
                    self.logger.warning(f"Erro ao processar linha: {str(e)}")
                    # Adicionar mesmo assim, sem enriquecimento
                    enriched_ebooks.append(row_dict)
            
            return enriched_ebooks
            
        except Exception as e:
            self.logger.error(f"Erro ao processar CSV: {str(e)}")
            raise
    
    def _extract_author_title(self, filename: str) -> tuple:
        """
        Extrai autor e título do nome do arquivo.
    
        Args:
            filename: Nome do arquivo
        
        Returns:
            Tupla com (autor, título)
        """
        # Remover extensão
        name_without_ext = os.path.splitext(filename)[0]
    
        # Pattern-specific extraction rules for common file naming patterns
        patterns_with_rules = [
            # Autor - Título (always author first)
            (r'^([^-]+)\s*-\s*(.+)$', lambda p1, p2: (p1, p2)),
            # Título (Autor) (always author in parentheses)
            (r'^(.+?)\s*\(([^)]+)\)$', lambda p1, p2: (p2, p1)),
            # Autor_Título (always author first)
            (r'^([^_]+)_\s*(.+)$', lambda p1, p2: (p1, p2)),
            # Autor.Título (always author first)
            (r'^([^.]+)\.(.+)$', lambda p1, p2: (p1, p2)),
            # [Autor] Título (always author in brackets)
            (r'^\[([^]]+)\]\s*(.+)$', lambda p1, p2: (p1, p2)),
        ]
    
        for pattern, rule in patterns_with_rules:
            match = re.match(pattern, name_without_ext)
            if match:
                part1, part2 = match.groups()
                return rule(part1.strip(), part2.strip())
    
        # If no pattern matched, assume it's just the title
        return "Desconhecido", name_without_ext.strip()