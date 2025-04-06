import logging
import requests
import json
import csv
from typing import Dict, Any, Optional, List
from core.interfaces.exporter import Exporter

class NotionExporter(Exporter):
    """Exportador para o Notion."""
    
    def __init__(self, token: Optional[str] = None, database_id: Optional[str] = None):
        """
        Inicializa o exportador do Notion.
        
        Args:
            token: Token de integração da API do Notion
            database_id: ID da base de dados do Notion
        """
        self.token = token
        self.database_id = database_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {token}" if token else "",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.logger = logging.getLogger(__name__)
    
    def export(self, csv_path: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Exporta dados de um CSV para o Notion.
        
        Args:
            csv_path: Caminho para o arquivo CSV
            config: Configurações (pode conter token e database_id)
            
        Returns:
            True se a exportação foi bem-sucedida, False caso contrário
        """
        # Atualizar configurações se fornecidas
        if config:
            if 'token' in config:
                self.token = config['token']
                self.headers["Authorization"] = f"Bearer {self.token}"
            if 'database_id' in config:
                self.database_id = config['database_id']
            # Aplicar configurações avançadas
            self.include_cover = config.get("include_cover", True)
            self.include_description = config.get("include_description", True)
            self.default_reading_status = config.get("default_reading_status", "Não Lido")
        
        if not self.token or not self.database_id:
            self.logger.error("Token ou ID da base de dados do Notion não configurados")
            return False
        
        try:
            return self.import_ebooks_from_csv(csv_path)
        except Exception as e:
            self.logger.error(f"Erro ao exportar para o Notion: {str(e)}")
            return False
    
    def add_ebook(self, ebook_data: Dict[str, Any]) -> Optional[str]:
        """
        Adiciona um ebook à base de dados do Notion com capa como ícone e conteúdo enriquecido.
        
        Args:
            ebook_data: Dicionário com dados do ebook
            
        Returns:
            ID da página criada no Notion ou None em caso de erro
        """
        if not self.database_id:
            self.logger.error("ID da base de dados não configurado")
            return None
            
        url = f"{self.base_url}/pages"
        
        # Extrair dados com prioridade para Google Books
        titulo = (ebook_data.get("GB_Titulo", "") or 
                  ebook_data.get("Titulo_Extraido", "") or 
                  ebook_data.get("Nome", "").split('.')[0])
                  
        autor = (ebook_data.get("GB_Autores", "") or 
                 ebook_data.get("Autor_Extraido", "") or 
                 "Desconhecido")
                 
        formato = ebook_data.get("Formato", "Desconhecido")
        
        # Obter URL da capa se disponível
        cover_url = ebook_data.get("GB_Capa_Link", None)
        
        # Preparar caminho como URL
        caminho = ebook_data.get("Caminho", "")
        if caminho.startswith("http"):
            url_value = caminho
        else:
            url_value = f"file://{caminho}" if caminho else None
        
        # Converter data
        date_str = ebook_data.get("Data Modificação", "")
        date_formatted = None
        if date_str:
            try:
                date_parts = date_str.split(" ")
                date_formatted = f"{date_parts[0]}T{date_parts[1] if len(date_parts) > 1 else '00:00:00'}.000Z"
            except:
                date_formatted = None
        
        # Preparar payload básico
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Título": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": titulo}
                        }
                    ]
                },
                "Autor": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": autor}
                        }
                    ]
                },
                "Formato": {
                    "select": {
                        "name": formato
                    }
                },
                "Status de Leitura": {
                    "select": {
                        "name": "Não Lido"  # Valor padrão
                    }
                }
            }
        }
        
        # Adicionar ícone de capa se disponível
        if cover_url:
            payload["icon"] = {
                "type": "external",
                "external": {
                    "url": cover_url
                }
            }
        
        # Adicionar propriedades opcionais
        if "Tamanho(MB)" in ebook_data:
            try:
                tamanho = float(ebook_data["Tamanho(MB)"])
                payload["properties"]["Tamanho (MB)"] = {"number": tamanho}
            except (ValueError, TypeError):
                pass
                
        if date_formatted:
            payload["properties"]["Data de Modificação"] = {"date": {"start": date_formatted}}
            
        if url_value:
            payload["properties"]["Caminho"] = {"url": url_value}
        
        # Adicionar propriedades do Google Books quando disponíveis
        if "GB_Editora" in ebook_data and ebook_data["GB_Editora"]:
            payload["properties"]["Editora"] = {
                "rich_text": [{"type": "text", "text": {"content": ebook_data["GB_Editora"]}}]
            }
            
        if "GB_Data_Publicacao" in ebook_data and ebook_data["GB_Data_Publicacao"]:
            try:
                # Tentar converter para data Notion
                pub_date = ebook_data["GB_Data_Publicacao"]
                # Se for apenas ano, adicionar mês e dia
                if len(pub_date) == 4 and pub_date.isdigit():
                    pub_date = f"{pub_date}-01-01"
                
                payload["properties"]["Data de Publicação"] = {"date": {"start": pub_date}}
            except:
                # Em caso de erro, adicionar como texto
                payload["properties"]["Ano de Publicação"] = {
                    "rich_text": [{"type": "text", "text": {"content": ebook_data["GB_Data_Publicacao"]}}]
                }
        
        if "GB_ISBN13" in ebook_data and ebook_data["GB_ISBN13"]:
            payload["properties"]["ISBN"] = {
                "rich_text": [{"type": "text", "text": {"content": ebook_data["GB_ISBN13"]}}]
            }
        elif "GB_ISBN10" in ebook_data and ebook_data["GB_ISBN10"]:
            payload["properties"]["ISBN"] = {
                "rich_text": [{"type": "text", "text": {"content": ebook_data["GB_ISBN10"]}}]
            }
            
        if "GB_Paginas" in ebook_data and ebook_data["GB_Paginas"]:
            try:
                payload["properties"]["Páginas"] = {"number": int(ebook_data["GB_Paginas"])}
            except:
                pass
        
        # Adicionar temas/categorias
        temas = []
        # Primeiro verificar categorias do Google Books
        if "GB_Categorias" in ebook_data and ebook_data["GB_Categorias"]:
            for tema in ebook_data["GB_Categorias"].split(','):
                tema = tema.strip()
                if tema:
                    temas.append({"name": tema})
        # Depois verificar temas extraídos normalmente
        elif "Temas" in ebook_data and ebook_data["Temas"]:
            for tema in ebook_data["Temas"].split(','):
                tema = tema.strip()
                if tema:
                    temas.append({"name": tema})
        
        if temas:
            payload["properties"]["Temas"] = {"multi_select": temas}
        
        try:
            # Criar a página básica
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            page_id = result["id"]
            self.logger.info(f"Ebook adicionado com sucesso: {titulo}")
            
            # Adicionar conteúdo à página
            self._add_page_content(page_id, ebook_data)
            
            return page_id
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao adicionar ebook '{titulo}': {str(e)}")
            if hasattr(response, 'text'):
                self.logger.error(f"Detalhes do erro: {response.text}")
            return None
    
    def import_ebooks_from_csv(self, csv_path: str) -> bool:
        """
        Importa ebooks de um arquivo CSV para o Notion.
        
        Args:
            csv_path: Caminho para o arquivo CSV
            
        Returns:
            True se a importação foi bem-sucedida, False caso contrário
        """
        if not self.database_id:
            self.logger.error("ID da base de dados não configurado")
            return False
            
        success_count = 0
        error_count = 0
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                total_rows = sum(1 for _ in open(csv_path, 'r', encoding='utf-8')) - 1  # -1 para cabeçalho
                
                self.logger.info(f"Iniciando importação de {total_rows} ebooks do arquivo {csv_path}")
                
                for i, row in enumerate(reader):
                    try:
                        page_id = self.add_ebook(row)
                        if page_id:
                            success_count += 1
                        else:
                            error_count += 1
                            
                        self.logger.info(f"Progresso: {i+1}/{total_rows} - {row.get('Nome', 'Sem nome')}")
                    except Exception as e:
                        self.logger.error(f"Erro ao importar linha {i+1}: {str(e)}")
                        error_count += 1
                
                self.logger.info(f"Importação concluída. {success_count}/{total_rows} ebooks importados com sucesso. {error_count} erros.")
                
                return success_count > 0
                
        except Exception as e:
            self.logger.error(f"Erro ao ler arquivo CSV: {str(e)}")
            return False