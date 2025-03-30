
import logging
import os
import re
import json
import requests
from typing import Dict, Any, Optional, List
import pandas as pd
from core.interfaces.enricher import Enricher

class ExternalAPIEnricher(Enricher):
    """Enriquecedor que utiliza APIs externas para obter metadados de livros."""
    
    def __init__(self, api_key: str = None):
        """
        Inicializa o enriquecedor com API externa.
        
        Args:
            api_key: Chave de API opcional para serviços que exigem autenticação
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
    
    def enrich(self, csv_path: str, taxonomy_path: Optional[str] = None) -> Optional[str]:
        """
        Enriquece os metadados dos ebooks usando APIs externas.
        
        Args:
            csv_path: Caminho para o arquivo CSV com dados básicos
            taxonomy_path: Caminho opcional para o arquivo de taxonomia
            
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
            
            self.logger.info(f"Dados enriquecidos com API externa salvos em {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Erro ao enriquecer dados: {str(e)}")
            return None
    
    def _enrich_ebooks_from_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Enriquece os metadados dos ebooks usando APIs externas.
        
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
                    
                        # Buscar informações adicionais da API
                        api_data = self._fetch_book_data(titulo, autor)
                        if api_data:
                            # Atualizar com dados da API
                            if 'titulo' in api_data and api_data['titulo']:
                                enriched_ebook['Titulo_Extraido'] = api_data['titulo']
                            if 'autor' in api_data and api_data['autor']:
                                enriched_ebook['Autor_Extraido'] = api_data['autor']
                            if 'publicador' in api_data:
                                enriched_ebook['Publicador'] = api_data['publicador']
                            if 'data_publicacao' in api_data:
                                enriched_ebook['Data_Publicacao'] = api_data['data_publicacao']
                            if 'descricao' in api_data:
                                enriched_ebook['Descricao'] = api_data['descricao']
                            if 'isbn' in api_data:
                                enriched_ebook['ISBN'] = api_data['isbn']
                            if 'categorias' in api_data and api_data['categorias']:
                                enriched_ebook['Temas_Sugeridos'] = ', '.join(api_data['categorias'])
                    
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
        
        # Padrões comuns de nome de arquivo
        patterns = [
            # Autor - Título
            r'^([^-]+)\s*-\s*(.+)$',
            # Título (Autor)
            r'^(.+?)\s*\(([^)]+)\)$',
            # Autor_Título
            r'^([^_]+)_\s*(.+)$',
            # Autor.Título
            r'^([^.]+)\.(.+)$',
            # [Autor] Título
            r'^\[([^]]+)\]\s*(.+)$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, name_without_ext)
            if match:
                part1, part2 = match.groups()
                
                # Heurística: autor geralmente tem menos palavras que o título
                if len(part1.split()) < len(part2.split()):
                    return part1.strip(), part2.strip()
                else:
                    # Verificar outras heurísticas
                    if ":" in part2 or "," in part2:  # Títulos frequentemente têm dois pontos ou vírgulas
                        return part1.strip(), part2.strip()
                    else:
                        return part2.strip(), part1.strip()
        
        # Se não encontrar padrão, assumir que é só o título
        return "Desconhecido", name_without_ext.strip()
    
    def _fetch_book_data(self, titulo: str, autor: str) -> Dict[str, Any]:
        """
        Busca dados de um livro em APIs externas.
        
        Atualmente implementado com Open Library API.
        
        Args:
            titulo: Título do livro
            autor: Autor do livro
            
        Returns:
            Dicionário com dados do livro ou dicionário vazio se não encontrado
        """
        try:
            # Primeiro tentamos buscar por título e autor na Open Library
            query = f'title:"{titulo}" author:"{autor}"'
            encoded_query = requests.utils.quote(query)
            url = f"https://openlibrary.org/search.json?q={encoded_query}"
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('numFound', 0) > 0 and data.get('docs'):
                    book = data['docs'][0]  # Usar o primeiro resultado
                    
                    result = {
                        'titulo': book.get('title'),
                        'autor': ', '.join(book.get('author_name', [])),
                        'publicador': ', '.join(book.get('publisher', [])),
                        'data_publicacao': str(book.get('first_publish_year', '')),
                        'isbn': book.get('isbn', [''])[0] if book.get('isbn') else '',
                        'categorias': book.get('subject', [])
                    }
                    
                    # Buscar descrição se tivermos um key
                    if book.get('key'):
                        try:
                            work_url = f"https://openlibrary.org{book['key']}.json"
                            work_response = requests.get(work_url, timeout=5)
                            if work_response.status_code == 200:
                                work_data = work_response.json()
                                result['descricao'] = work_data.get('description', '')
                        except Exception as e:
                            self.logger.warning(f"Erro ao buscar descrição: {str(e)}")
                    
                    return result
            
            # Se não encontrar, retorna dicionário vazio
            return {}
            
        except Exception as e:
            self.logger.warning(f"Erro ao buscar dados da API: {str(e)}")
            return {}