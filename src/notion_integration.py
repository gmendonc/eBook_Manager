import requests
import json
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import os
import pandas as pd
import streamlit as st

# Configuração de logging
logger = logging.getLogger(__name__)

class NotionIntegration:
    """Classe para integrar o sistema de ebooks com o Notion."""
    
    def __init__(self, token: str, database_id: str = None):
        """
        Inicializa a integração com o Notion.
        
        Args:
            token: Token de integração da API do Notion
            database_id: ID opcional da base de dados do Notion para ebooks
        """
        self.token = token
        self.database_id = database_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"  # Usar a versão mais recente disponível
        }
        self.logger = logging.getLogger(__name__)
    
    def create_ebooks_database(self, page_id: str, title: str = "Biblioteca de Ebooks") -> str:
        """
        Cria uma nova base de dados de ebooks no Notion.
        
        Args:
            page_id: ID da página onde a base de dados será criada
            title: Título da base de dados
            
        Returns:
            ID da base de dados criada
        """
        url = f"{self.base_url}/databases"
        
        payload = {
            "parent": {"page_id": page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": {
                "Título": {"title": {}},
                "Autor": {"rich_text": {}},
                "Formato": {"select": {}},
                "Tamanho (MB)": {"number": {}},
                "Data de Modificação": {"date": {}},
                "Caminho": {"url": {}},
                "Status de Leitura": {
                    "select": {
                        "options": [
                            {"name": "Não Lido", "color": "gray"},
                            {"name": "Lendo", "color": "blue"},
                            {"name": "Lido", "color": "green"},
                            {"name": "Para Ler", "color": "yellow"},
                            {"name": "Referência", "color": "purple"}
                        ]
                    }
                },
                "Temas": {"multi_select": {}},
                "Prioridade": {
                    "select": {
                        "options": [
                            {"name": "Baixa", "color": "gray"},
                            {"name": "Média", "color": "yellow"},
                            {"name": "Alta", "color": "red"}
                        ]
                    }
                },
                "Notas": {"rich_text": {}}
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            self.database_id = result["id"]
            self.logger.info(f"Base de dados criada com sucesso: {self.database_id}")
            return self.database_id
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao criar base de dados: {str(e)}")
            if hasattr(response, 'status_code') and response.status_code == 400:
                self.logger.error(f"Detalhes do erro: {response.text}")
            raise
    
    def add_ebook_to_notion(self, ebook_data: Dict[str, Any]) -> str:
        """
        Adiciona um ebook à base de dados do Notion.
        
        Args:
            ebook_data: Dicionário com dados do ebook
            
        Returns:
            ID da página criada no Notion
        """
        if not self.database_id:
            raise ValueError("ID da base de dados não configurado")
            
        url = f"{self.base_url}/pages"
        
        # Converter data para o formato do Notion
        date_str = ebook_data.get("Data Modificação", "")
        if date_str:
            try:
                # Formato esperado: 2021-05-13T00:00:00.000Z
                date_parts = date_str.split(" ")
                date_formatted = f"{date_parts[0]}T{date_parts[1] if len(date_parts) > 1 else '00:00:00'}.000Z"
            except:
                date_formatted = None
        else:
            date_formatted = None
            
        # Extrai título e autor do nome do arquivo, se não fornecido explicitamente
        titulo = ebook_data.get("Titulo", "")
        autor = ebook_data.get("Autor", "")
        
        if not titulo or not autor:
            nome_arquivo = ebook_data.get("Nome", "")
            titulo = titulo or nome_arquivo.split('.')[0]
            autor = autor or "Desconhecido"
            
        # Formata o caminho como URL se possível
        caminho = ebook_data.get("Caminho", "")
        if caminho.startswith("http"):
            url_value = caminho
        else:
            # Tentar criar uma URL local
            url_value = f"file://{caminho}" if caminho else None
        
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
                        "name": ebook_data.get("Formato", "Desconhecido")
                    }
                },
                "Status de Leitura": {
                    "select": {
                        "name": "Não Lido"  # Valor padrão
                    }
                }
            }
        }
        
        # Adicionar propriedades opcionais se estiverem disponíveis
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
            
        # Adicionar temas se disponíveis
        if "Temas" in ebook_data and ebook_data["Temas"]:
            temas_list = []
            temas_str = str(ebook_data["Temas"])
            for tema in temas_str.split(','):
                tema = tema.strip()
                if tema:
                    temas_list.append({"name": tema})
                    
            if temas_list:
                payload["properties"]["Temas"] = {"multi_select": temas_list}
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            page_id = result["id"]
            self.logger.info(f"Ebook adicionado com sucesso: {titulo}")
            return page_id
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao adicionar ebook '{titulo}': {str(e)}")
            if hasattr(response, 'text'):
                self.logger.error(f"Detalhes do erro: {response.text}")
            raise
    
    def import_ebooks_from_csv(self, csv_path: str) -> List[str]:
        """
        Importa ebooks de um arquivo CSV para o Notion.
        
        Args:
            csv_path: Caminho para o arquivo CSV
            
        Returns:
            Lista de IDs das páginas criadas no Notion
        """
        if not self.database_id:
            raise ValueError("ID da base de dados não configurado")
            
        page_ids = []
        try:
            # Usar pandas para ler o CSV
            df = pd.read_csv(csv_path)
            total_rows = len(df)
            
            self.logger.info(f"Iniciando importação de {total_rows} ebooks do arquivo {csv_path}")
            
            # Configurar barra de progresso se estivermos em um contexto Streamlit
            progress_placeholder = None
            progress_text = None
            try:
                if st._is_running_with_streamlit:
                    progress_text = st.empty()
                    progress_placeholder = st.progress(0)
            except:
                pass
                
            for i, row in df.iterrows():
                try:
                    # Atualizar progresso
                    if progress_placeholder:
                        progress = (i + 1) / total_rows
                        progress_placeholder.progress(progress)
                        progress_text.text(f"Importando: {i+1}/{total_rows} - {row.get('Nome', 'Sem nome')}")
                        
                    # Converter row para dicionário
                    ebook_data = row.to_dict()
                    
                    page_id = self.add_ebook_to_notion(ebook_data)
                    page_ids.append(page_id)
                    self.logger.info(f"Progresso: {i+1}/{total_rows} - {row.get('Nome', 'Sem nome')}")
                except Exception as e:
                    self.logger.error(f"Erro ao importar linha {i+1}: {str(e)}")
            
            self.logger.info(f"Importação concluída. {len(page_ids)}/{total_rows} ebooks importados com sucesso.")
            
            # Limpar barra de progresso
            if progress_placeholder:
                progress_placeholder.empty()
                progress_text.empty()
                
        except Exception as e:
            self.logger.error(f"Erro ao ler arquivo CSV: {str(e)}")
            raise
            
        return page_ids
    
    def update_ebook_properties(self, page_id: str, properties: Dict[str, Any]) -> bool:
        """
        Atualiza propriedades de um ebook no Notion.
        
        Args:
            page_id: ID da página do ebook no Notion
            properties: Dicionário com as propriedades a serem atualizadas
            
        Returns:
            True se a atualização for bem-sucedida, False caso contrário
        """
        url = f"{self.base_url}/pages/{page_id}"
        
        # Converter o dicionário de propriedades para o formato esperado pela API do Notion
        notion_properties = {}
        
        # Mapeamento de propriedades comuns
        if "titulo" in properties:
            notion_properties["Título"] = {
                "title": [{"type": "text", "text": {"content": properties["titulo"]}}]
            }
            
        if "autor" in properties:
            notion_properties["Autor"] = {
                "rich_text": [{"type": "text", "text": {"content": properties["autor"]}}]
            }
            
        if "status" in properties:
            notion_properties["Status de Leitura"] = {
                "select": {"name": properties["status"]}
            }
            
        if "prioridade" in properties:
            notion_properties["Prioridade"] = {
                "select": {"name": properties["prioridade"]}
            }
            
        if "temas" in properties and isinstance(properties["temas"], list):
            notion_properties["Temas"] = {
                "multi_select": [{"name": tema} for tema in properties["temas"]]
            }
            
        if "notas" in properties:
            notion_properties["Notas"] = {
                "rich_text": [{"type": "text", "text": {"content": properties["notas"]}}]
            }
        
        payload = {
            "properties": notion_properties
        }
        
        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            response.raise_for_status()
            self.logger.info(f"Propriedades atualizadas com sucesso para a página {page_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao atualizar propriedades da página {page_id}: {str(e)}")
            if hasattr(response, 'text'):
                self.logger.error(f"Detalhes do erro: {response.text}")
            return False
    
    def query_ebooks_by_property(self, property_name: str, value: Any) -> List[Dict[str, Any]]:
        """
        Consulta ebooks na base de dados do Notion com base em uma propriedade.
        
        Args:
            property_name: Nome da propriedade para filtrar
            value: Valor para filtrar
            
        Returns:
            Lista de ebooks que correspondem ao filtro
        """
        if not self.database_id:
            raise ValueError("ID da base de dados não configurado")
            
        url = f"{self.base_url}/databases/{self.database_id}/query"
        
        # Criar o filtro apropriado com base no tipo de propriedade
        filter_obj = {}
        
        if property_name == "Título":
            filter_obj = {
                "property": property_name,
                "title": {"equals": value}
            }
        elif property_name in ["Autor", "Notas"]:
            filter_obj = {
                "property": property_name,
                "rich_text": {"contains": value}
            }
        elif property_name in ["Formato", "Status de Leitura", "Prioridade"]:
            filter_obj = {
                "property": property_name,
                "select": {"equals": value}
            }
        elif property_name == "Temas":
            filter_obj = {
                "property": property_name,
                "multi_select": {"contains": value}
            }
        elif property_name == "Tamanho (MB)":
            if isinstance(value, dict):
                # Para consultas de intervalo: {"min": 1.0, "max": 5.0}
                filter_obj = {
                    "property": property_name,
                    "number": value
                }
            else:
                filter_obj = {
                    "property": property_name,
                    "number": {"equals": float(value)}
                }
        
        payload = {
            "filter": filter_obj
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Converter o resultado para um formato mais amigável
            ebooks = []
            for page in result.get("results", []):
                properties = page.get("properties", {})
                ebook = {
                    "id": page.get("id"),
                    "url": page.get("url")
                }
                
                # Extrair valores das propriedades
                if "Título" in properties:
                    title_content = properties["Título"].get("title", [])
                    ebook["titulo"] = title_content[0].get("text", {}).get("content", "") if title_content else ""
                    
                if "Autor" in properties:
                    author_content = properties["Autor"].get("rich_text", [])
                    ebook["autor"] = author_content[0].get("text", {}).get("content", "") if author_content else ""
                    
                if "Formato" in properties and "select" in properties["Formato"]:
                    select_data = properties["Formato"]["select"]
                    ebook["formato"] = select_data.get("name", "") if select_data else ""
                    
                ebooks.append(ebook)
                
            return ebooks
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro ao consultar ebooks: {str(e)}")
            if hasattr(response, 'text'):
                self.logger.error(f"Detalhes do erro: {response.text}")
            return []

def configure_notion_integration():
    """
    Configura a integração com o Notion interativamente.
    
    Para uso com Streamlit.
    """
    # Verificar se há credenciais salvas
    config_file = Path("notion_config.json")
    
    st.markdown("## 🔌 Configuração do Notion")
    
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                
            st.success("Configuração existente encontrada!")
            st.info(f"Token: {config.get('token', '')[:4]}{'*' * 20}")
            st.info(f"Database ID: {config.get('database_id', 'Não configurado')}")
            
            use_existing = st.radio(
                "Deseja usar esta configuração?", 
                options=["Sim", "Não, configurar novamente"],
                index=0
            )
            
            if use_existing == "Sim":
                return NotionIntegration(
                    token=config.get("token", ""),
                    database_id=config.get("database_id", None)
                )
        except Exception as e:
            st.error(f"Erro ao ler configuração existente: {str(e)}")
    
    # Solicitar novas credenciais
    st.markdown("""
    ### Criar uma nova integração no Notion
    
    Para integrar com o Notion, você precisará criar uma integração:
    
    1. Acesse [www.notion.so/my-integrations](https://www.notion.so/my-integrations)
    2. Clique em '+ New integration'
    3. Dê um nome para sua integração, como 'Gerenciador de Ebooks'
    4. Selecione o workspace onde você deseja adicionar a integração
    5. Copie o 'Internal Integration Token' fornecido
    """)
    
    token = st.text_input("Cole o token de integração aqui:", type="password")
    
    # Verificar se uma base de dados existente deve ser usada
    use_existing_db = st.radio(
        "Você já tem uma base de dados no Notion para ebooks?",
        options=["Sim", "Não, preciso criar uma nova"],
        index=1
    )
    
    database_id = None
    if use_existing_db == "Sim":
        st.markdown("""
        ### Encontrar o ID da base de dados
        
        Para encontrar o ID da base de dados:
        1. Abra sua base de dados no Notion
        2. O ID está na URL: https://www.notion.so/workspace/[ID-DA-BASE]?v=...
        """)
        database_id = st.text_input("ID da base de dados:")
    else:
        st.markdown("""
        ### Criar uma nova base de dados
        
        Para criar uma nova base de dados:
        1. Crie uma página no Notion onde a base de dados será adicionada
        2. Compartilhe a página com sua integração (clique em 'Share' e adicione sua integração)
        3. Copie o ID da página da URL
        """)
    
    # Botão para salvar configuração
    save_config = st.button("Salvar Configuração")
    
    if save_config and token:
        # Salvar configuração
        config = {
            "token": token,
            "database_id": database_id
        }
        
        try:
            with open(config_file, "w") as f:
                json.dump(config, f)
            st.success("Configuração salva com sucesso!")
            
            return NotionIntegration(token=token, database_id=database_id)
        except Exception as e:
            st.error(f"Erro ao salvar configuração: {str(e)}")
    
    return None

def create_notion_database_ui(notion_integration):
    """Interface para criar uma base de dados no Notion."""
    
    st.markdown("## 📋 Criar Base de Dados no Notion")
    
    if not notion_integration or not notion_integration.token:
        st.error("Configuração do Notion não encontrada. Configure o Notion primeiro.")
        return
    
    st.markdown("""
    Para criar uma nova base de dados, você precisa:
    1. Criar uma página no Notion onde a base de dados será adicionada
    2. Compartilhar a página com sua integração (clique em 'Share' e adicione sua integração)
    3. Copiar o ID da página da URL
    """)
    
    page_id = st.text_input("ID da página para criar a base de dados:")
    db_title = st.text_input("Título para a base de dados:", value="Biblioteca de Ebooks")
    
    if st.button("Criar Base de Dados") and page_id:
        try:
            with st.spinner("Criando base de dados..."):
                database_id = notion_integration.create_ebooks_database(page_id, db_title)
                
            if database_id:
                st.success(f"Base de dados criada com sucesso! ID: {database_id}")
                
                # Salvar o novo database_id na configuração
                config_file = Path("notion_config.json")
                if config_file.exists():
                    with open(config_file, "r") as f:
                        config = json.load(f)
                    
                    config["database_id"] = database_id
                    
                    with open(config_file, "w") as f:
                        json.dump(config, f)
                        
                # Atualizar a integração
                notion_integration.database_id = database_id
                
                return database_id
        except Exception as e:
            st.error(f"Erro ao criar base de dados: {str(e)}")
    
    return None