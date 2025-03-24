import csv
import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
from collections import Counter
import nltk

# Verificar se os recursos do NLTK estão disponíveis
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
    except:
        logging.warning("Não foi possível baixar recursos do NLTK")

# Verificar se temos ebooklib para processamento de EPUB
try:
    import ebooklib
    from ebooklib import epub
    EBOOKLIB_AVAILABLE = True
except ImportError:
    EBOOKLIB_AVAILABLE = False
    logging.warning("Módulo ebooklib não disponível. Instale com 'pip install ebooklib'")

# Verificar se temos PyPDF2 para processamento de PDF
try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logging.warning("Módulo PyPDF2 não disponível. Instale com 'pip install PyPDF2'")

# Configuração de logging
logger = logging.getLogger(__name__)

class EbookEnricher:
    """Classe para enriquecer metadados de ebooks para integração com PKM."""
    
    def __init__(self, temas_path: Optional[str] = None):
        """
        Inicializa o enriquecedor de ebooks.
        
        Args:
            temas_path: Caminho opcional para um arquivo JSON com a taxonomia de temas
        """
        self.logger = logging.getLogger(__name__)
        
        # Inicializar stopwords
        try:
            from nltk.corpus import stopwords
            self.stops = set(stopwords.words('portuguese') + stopwords.words('english'))
        except:
            self.stops = set()
            self.logger.warning("Não foi possível carregar stopwords. O enriquecimento de temas será limitado.")
        
        # Carregar taxonomia de temas se fornecida
        self.temas = {}
        if temas_path and os.path.exists(temas_path):
            try:
                with open(temas_path, 'r', encoding='utf-8') as f:
                    self.temas = json.load(f)
                self.logger.info(f"Taxonomia de temas carregada com {len(self.temas)} categorias principais")
            except Exception as e:
                self.logger.error(f"Erro ao carregar taxonomia de temas: {str(e)}")
    
    def extract_author_title(self, filename: str) -> Tuple[str, str]:
        """
        Extrai autor e título do nome do arquivo.
        
        Args:
            filename: Nome do arquivo de ebook
            
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
    
    def extract_metadata_from_epub(self, epub_path: str) -> Dict[str, Any]:
        """
        Extrai metadados de um arquivo EPUB.
        
        Args:
            epub_path: Caminho para o arquivo EPUB
            
        Returns:
            Dicionário com metadados
        """
        metadata = {
            "titulo": "",
            "autor": "",
            "publicador": "",
            "idioma": "",
            "data_publicacao": "",
            "descricao": "",
            "palavras_chave": [],
            "conteudo_amostra": ""
        }
        
        if not EBOOKLIB_AVAILABLE:
            self.logger.warning("Módulo ebooklib não disponível. Não é possível extrair metadados de EPUB.")
            return metadata
            
        try:
            book = epub.read_epub(epub_path)
            
            # Extrair metadados básicos
            for item in book.get_metadata('DC', 'title'):
                metadata["titulo"] = item[0] if item[0] else metadata["titulo"]
                
            for item in book.get_metadata('DC', 'creator'):
                metadata["autor"] = item[0] if item[0] else metadata["autor"]
                
            for item in book.get_metadata('DC', 'publisher'):
                metadata["publicador"] = item[0] if item[0] else metadata["publicador"]
                
            for item in book.get_metadata('DC', 'language'):
                metadata["idioma"] = item[0] if item[0] else metadata["idioma"]
                
            for item in book.get_metadata('DC', 'date'):
                metadata["data_publicacao"] = item[0] if item[0] else metadata["data_publicacao"]
                
            for item in book.get_metadata('DC', 'description'):
                metadata["descricao"] = item[0] if item[0] else metadata["descricao"]
                
            for item in book.get_metadata('DC', 'subject'):
                if item[0]:
                    metadata["palavras_chave"].append(item[0])
            
            # Extrair amostra de conteúdo para análise de temas
            text_content = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    try:
                        content = item.get_content().decode('utf-8')
                        # Remover tags HTML para obter texto puro
                        clean_text = re.sub(r'<[^>]+>', ' ', content)
                        text_content.append(clean_text)
                        
                        # Limitar tamanho da amostra
                        if len(''.join(text_content)) > 10000:
                            break
                    except Exception as e:
                        continue
            
            metadata["conteudo_amostra"] = ''.join(text_content)[:10000]
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair metadados de {epub_path}: {str(e)}")
        
        return metadata
    
    def extract_metadata_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extrai metadados de um arquivo PDF.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            Dicionário com metadados
        """
        metadata = {
            "titulo": "",
            "autor": "",
            "publicador": "",
            "data_publicacao": "",
            "palavras_chave": [],
            "conteudo_amostra": ""
        }
        
        if not PYPDF2_AVAILABLE:
            self.logger.warning("Módulo PyPDF2 não disponível. Não é possível extrair metadados de PDF.")
            return metadata
            
        try:
            reader = PdfReader(pdf_path)
            
            # Extrair metadados básicos
            if reader.metadata:
                metadata["titulo"] = reader.metadata.title if reader.metadata.title else metadata["titulo"]
                metadata["autor"] = reader.metadata.author if reader.metadata.author else metadata["autor"]
                metadata["data_publicacao"] = reader.metadata.creation_date if reader.metadata.creation_date else metadata["data_publicacao"]
                
                if reader.metadata.subject:
                    keywords = reader.metadata.subject.split(',')
                    metadata["palavras_chave"] = [k.strip() for k in keywords]
            
            # Extrair amostra de conteúdo para análise de temas
            text_content = []
            # Limitar a 10 páginas para performance
            for i in range(min(10, len(reader.pages))):
                try:
                    page = reader.pages[i]
                    text_content.append(page.extract_text())
                    
                    # Limitar tamanho da amostra
                    if len(''.join(text_content)) > 10000:
                        break
                except Exception as e:
                    continue
            
            metadata["conteudo_amostra"] = ''.join(text_content)[:10000]
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair metadados de {pdf_path}: {str(e)}")
        
        return metadata
    
    def extract_topics(self, text: str, num_topics: int = 5) -> List[str]:
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
            from nltk.tokenize import word_tokenize
            tokens = word_tokenize(text.lower())
            tokens = [word for word in tokens if word.isalnum() and word not in self.stops and len(word) > 3]
            
            # Contar frequência das palavras
            word_counts = Counter(tokens)
            top_words = word_counts.most_common(num_topics)
            
            return [word for word, _ in top_words]
        except Exception as e:
            self.logger.error(f"Erro ao extrair tópicos: {str(e)}")
            return []
    
    def match_topics_to_taxonomy(self, topics: List[str]) -> List[str]:
        """
        Associa tópicos extraídos à taxonomia de temas do PKM.
        
        Args:
            topics: Lista de tópicos extraídos do texto
            
        Returns:
            Lista de temas da taxonomia que melhor correspondem
        """
        if not self.temas or not topics:
            return []
            
        matched_themes = []
        
        # Para cada tópico extraído
        for topic in topics:
            # Verificar se há correspondência direta na taxonomia
            for theme, subtemas in self.temas.items():
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
    
    def enrich_ebooks_from_csv(self, csv_path: str, output_path: str = None) -> List[Dict[str, Any]]:
        """
        Enriquece os metadados de ebooks a partir de um arquivo CSV.
        
        Args:
            csv_path: Caminho para o arquivo CSV com dados básicos dos ebooks
            output_path: Caminho opcional para salvar o CSV enriquecido
            
        Returns:
            Lista de dicionários com dados enriquecidos dos ebooks
        """
        if not output_path:
            output_path = csv_path.replace('.csv', '_enriched.csv')
            if output_path == csv_path:
                output_path = os.path.splitext(csv_path)[0] + '_enriched.csv'
                
        enriched_ebooks = []
        
        try:
            # Ler dados básicos do CSV
            df = pd.read_csv(csv_path)
            total_rows = len(df)
            
            self.logger.info(f"Iniciando enriquecimento de {total_rows} ebooks do arquivo {csv_path}")
            
            for i, row in df.iterrows():
                try:
                    self.logger.info(f"Processando {i+1}/{total_rows}: {row.get('Nome', 'Sem nome')}")
                    
                    # Converter row para dict para facilitar o processamento
                    row_dict = row.to_dict()
                    
                    # Copiar dados básicos
                    enriched_ebook = dict(row_dict)
                    
                    # Extrair autor e título do nome do arquivo
                    autor, titulo = self.extract_author_title(row_dict.get('Nome', ''))
                    enriched_ebook['Autor_Extraido'] = autor
                    enriched_ebook['Titulo_Extraido'] = titulo
                    
                    # Se tiver acesso ao arquivo físico, extrair mais metadados
                    caminho = row_dict.get('Caminho', '')
                    if caminho and os.path.exists(caminho):
                        formato = row_dict.get('Formato', '').lower()
                        
                        if formato == 'epub' and EBOOKLIB_AVAILABLE:
                            metadata = self.extract_metadata_from_epub(caminho)
                        elif formato == 'pdf' and PYPDF2_AVAILABLE:
                            metadata = self.extract_metadata_from_pdf(caminho)
                        else:
                            metadata = {}
                            
                        # Usar metadados extraídos se disponíveis
                        if metadata.get('titulo'):
                            enriched_ebook['Titulo_Extraido'] = metadata['titulo']
                        if metadata.get('autor'):
                            enriched_ebook['Autor_Extraido'] = metadata['autor']
                            
                        # Adicionar novos metadados
                        if metadata.get('publicador'):
                            enriched_ebook['Publicador'] = metadata['publicador']
                        if metadata.get('data_publicacao'):
                            enriched_ebook['Data_Publicacao'] = metadata['data_publicacao']
                        if metadata.get('descricao'):
                            enriched_ebook['Descricao'] = metadata['descricao']
                            
                        # Extrair possíveis temas do conteúdo
                        if metadata.get('conteudo_amostra'):
                            topics = self.extract_topics(metadata['conteudo_amostra'])
                            matched_themes = self.match_topics_to_taxonomy(topics)
                            
                            enriched_ebook['Possiveis_Temas'] = ', '.join(topics)
                            enriched_ebook['Temas_Sugeridos'] = ', '.join(matched_themes)
                    
                    enriched_ebooks.append(enriched_ebook)
                    
                except Exception as e:
                    self.logger.error(f"Erro ao processar linha {i+1}: {str(e)}")
                    # Adicionar mesmo assim, sem enriquecimento
                    enriched_ebooks.append(row_dict)
            
            # Salvar dados enriquecidos em novo CSV
            if enriched_ebooks:
                # Converter para DataFrame e salvar
                df_enriched = pd.DataFrame(enriched_ebooks)
                df_enriched.to_csv(output_path, index=False, encoding='utf-8')
                self.logger.info(f"Dados enriquecidos salvos em {output_path}")
                
        except Exception as e:
            self.logger.error(f"Erro ao processar arquivo CSV: {str(e)}")
            
        return enriched_ebooks
    
    def create_notion_ready_csv(self, enriched_csv_path: str, output_path: str = None) -> str:
        """
        Cria um CSV pronto para importação no Notion com os campos mapeados corretamente.
        
        Args:
            enriched_csv_path: Caminho para o CSV enriquecido
            output_path: Caminho opcional para o CSV de saída
            
        Returns:
            Caminho para o CSV pronto para o Notion
        """
        if not output_path:
            output_path = enriched_csv_path.replace('.csv', '_notion.csv')
            if output_path == enriched_csv_path:
                output_path = os.path.splitext(enriched_csv_path)[0] + '_notion.csv'
        
        try:
            # Ler dados enriquecidos
            df = pd.read_csv(enriched_csv_path)
            
            # Mapear campos para o formato do Notion
            notion_ebooks = []
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                notion_ebook = {
                    "Nome": row_dict.get("Nome", ""),
                    "Titulo": row_dict.get("Titulo_Extraido", "") or row_dict.get("Titulo", "") or row_dict.get("Nome", "").split('.')[0],
                    "Autor": row_dict.get("Autor_Extraido", "") or row_dict.get("Autor", "") or "Desconhecido",
                    "Formato": row_dict.get("Formato", ""),
                    "Tamanho(MB)": row_dict.get("Tamanho(MB)", ""),
                    "Data Modificação": row_dict.get("Data Modificação", ""),
                    "Caminho": row_dict.get("Caminho", ""),
                    "Temas": row_dict.get("Temas_Sugeridos", ""),
                    "Prioridade": "Média",  # Valor padrão
                    "Status de Leitura": "Não Lido"  # Valor padrão
                }
                
                # Adicionar campos extras se disponíveis
                if "Publicador" in row_dict:
                    notion_ebook["Publicador"] = row_dict["Publicador"]
                if "Data_Publicacao" in row_dict:
                    notion_ebook["Data_Publicacao"] = row_dict["Data_Publicacao"]
                if "Descricao" in row_dict:
                    notion_ebook["Descricao"] = row_dict["Descricao"]
                    
                notion_ebooks.append(notion_ebook)
            
            # Salvar CSV pronto para o Notion
            df_notion = pd.DataFrame(notion_ebooks)
            df_notion.to_csv(output_path, index=False, encoding='utf-8')
            
            self.logger.info(f"CSV pronto para o Notion salvo em {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Erro ao criar CSV para o Notion: {str(e)}")
            return enriched_csv_path  # Retornar o CSV original em caso de erro