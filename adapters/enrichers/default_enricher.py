import logging
import os
import re
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter
from core.interfaces.enricher import Enricher

class DefaultEnricher(Enricher):
    """Implementação padrão do enriquecedor de metadados."""
    
    def __init__(self):
        """Inicializa o enriquecedor."""
        self.logger = logging.getLogger(__name__)
        
        # Carregar stopwords
        try:
            import nltk
            try:
                nltk.data.find('tokenizers/punkt')
                nltk.data.find('corpora/stopwords')
            except LookupError:
                nltk.download('punkt')
                nltk.download('stopwords')
            
            self.stops = set(stopwords.words('portuguese') + stopwords.words('english'))
        except Exception as e:
            self.logger.warning(f"Erro ao inicializar NLTK: {str(e)}")
            self.stops = set()
    
    def enrich(self, csv_path: str, taxonomy_path: Optional[str] = None) -> Optional[str]:
        """
        Enriquece os metadados dos ebooks a partir de um arquivo CSV.
        
        Args:
            csv_path: Caminho para o arquivo CSV com dados básicos
            taxonomy_path: Caminho opcional para o arquivo de taxonomia de temas
            
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
            # Carregar taxonomia de temas se disponível
            temas = {}
            if taxonomy_path and os.path.exists(taxonomy_path):
                try:
                    with open(taxonomy_path, 'r', encoding='utf-8') as f:
                        temas = json.load(f)
                    self.logger.info(f"Taxonomia de temas carregada: {len(temas)} categorias")
                except Exception as e:
                    self.logger.error(f"Erro ao carregar taxonomia: {str(e)}")
            
            # Processar o CSV
            enriched_ebooks = self._enrich_ebooks_from_csv(csv_path, temas)
            
            # Salvar CSV enriquecido
            self._save_enriched_csv(enriched_ebooks, output_path)
            
            self.logger.info(f"Dados enriquecidos salvos em {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Erro ao enriquecer dados: {str(e)}")
            return None
    
    def _enrich_ebooks_from_csv(self, csv_path: str, temas: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """
        Enriquece os metadados dos ebooks a partir de um arquivo CSV.
        
        Args:
            csv_path: Caminho para o arquivo CSV
            temas: Dicionário de temas para classificação
            
        Returns:
            Lista de dicionários com dados enriquecidos
        """
        enriched_ebooks = []
        
        try:
            # Ler dados do CSV
            df = pd.read_csv(csv_path)
            
            for _, row in df.iterrows():
                try:
                    # Copiar dados básicos
                    enriched_ebook = dict(row)
                    
                    # Extrair autor e título do nome do arquivo
                    nome_arquivo = row.get('Nome', '')
                    if nome_arquivo and 'Titulo_Extraido' not in enriched_ebook:
                        autor, titulo = self._extract_author_title(nome_arquivo)
                        enriched_ebook['Autor_Extraido'] = autor
                        enriched_ebook['Titulo_Extraido'] = titulo
                    
                    # Extrair possíveis temas do título
                    if 'Titulo_Extraido' in enriched_ebook:
                        titulo = enriched_ebook['Titulo_Extraido']
                        topics = self._extract_topics(titulo)
                        matched_themes = self._match_topics_to_taxonomy(topics, temas)
                        
                        if matched_themes:
                            enriched_ebook['Temas_Sugeridos'] = ', '.join(matched_themes)
                    
                    enriched_ebooks.append(enriched_ebook)
                    
                except Exception as e:
                    self.logger.warning(f"Erro ao processar linha: {str(e)}")
                    # Adicionar sem enriquecimento
                    enriched_ebooks.append(dict(row))
            
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
    
    def _extract_topics(self, text: str, num_topics: int = 5) -> List[str]:
        """
        Extrai possíveis tópicos/temas de um texto.
        
        Args:
            text: Texto para extrair tópicos
            num_topics: Número de tópicos a retornar
            
        Returns:
            Lista de tópicos extraídos
        """
        if not text:
            return []
            
        try:
            # Tokenizar e remover stopwords
            tokens = word_tokenize(text.lower())
            tokens = [word for word in tokens if word.isalnum() and word not in self.stops and len(word) > 3]
            
            # Contar frequência das palavras
            word_counts = Counter(tokens)
            top_words = word_counts.most_common(num_topics)
            
            return [word for word, _ in top_words]
        except Exception as e:
            self.logger.warning(f"Erro ao extrair tópicos: {str(e)}")
            return []
    
    def _match_topics_to_taxonomy(self, topics: List[str], temas: Dict[str, List[str]]) -> List[str]:
        """
        Associa tópicos extraídos à taxonomia de temas.
        
        Args:
            topics: Lista de tópicos extraídos do texto
            temas: Dicionário de temas para classificação
            
        Returns:
            Lista de temas da taxonomia que melhor correspondem
        """
        if not temas or not topics:
            return []
            
        matched_themes = []
        
        # Para cada tópico extraído
        for topic in topics:
            # Verificar se há correspondência direta na taxonomia
            for theme, subtemas in temas.items():
                # Verificar tema principal
                if topic in theme.lower():
                    if theme not in matched_themes:
                        matched_themes.append(theme)
                    continue
                
                # Verificar subtemas
                for subtema in subtemas:
                    if topic in subtema.lower():
                        if subtema not in matched_themes:
                            matched_themes.append(subtema)
                        break
        
        # Limitar a 5 temas para não sobrecarregar
        return matched_themes[:5]
    
    def _save_enriched_csv(self, enriched_ebooks: List[Dict[str, Any]], output_path: str) -> None:
        """
        Salva os dados enriquecidos em um arquivo CSV.
        
        Args:
            enriched_ebooks: Lista de dicionários com dados enriquecidos
            output_path: Caminho para o arquivo de saída
        """
        try:
            # Criar DataFrame
            df = pd.DataFrame(enriched_ebooks)
            
            # Salvar CSV
            df.to_csv(output_path, index=False, encoding='utf-8')
        except Exception as e:
            self.logger.error(f"Erro ao salvar CSV enriquecido: {str(e)}")
            raise