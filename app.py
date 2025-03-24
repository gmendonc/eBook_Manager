import streamlit as st
import pandas as pd
import os
import json
import logging
import keyring
from getpass import getpass
from pathlib import Path
from datetime import datetime
import re
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
from wordcloud import WordCloud
import sys

# Adicionando a pasta src ao path do Python para importações
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
if src_path not in sys.path:
    sys.path.append(src_path)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ebook_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Importar módulos do sistema
from ebook_sources import (
    ICloudEbookScanner, 
    ICloudAuthManager,
    DropboxEbookScanner,
    FileSystemEbookScanner,
    KindleEbookScanner
)
from ebook_enricher import EbookEnricher
from notion_integration import NotionIntegration, configure_notion_integration
from dashboard_utils import load_data, process_data, generate_wordcloud, extract_year

# Configuração da aplicação
st.set_page_config(
    page_title="Gerenciador de Biblioteca de Ebooks",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS
def load_css(css_file_path):
    """
    Carrega arquivo CSS de uma pasta dedicada.
    
    Args:
        css_file_path: Caminho relativo para o arquivo CSS dentro da pasta static/css
    """
    # Determinar o caminho para a pasta static/css
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(current_dir, 'static', 'css', css_file_path)
    
    # Verificar se o arquivo existe
    if not os.path.exists(css_path):
        st.warning(f"Arquivo CSS não encontrado: {css_path}")
        return
    
    # Carregar e aplicar o CSS
    with open(css_path, 'r', encoding='utf-8') as f:
        css = f.read()
    return st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Carregar o arquivo CSS da pasta dedicada
load_css('style.css')

class EbookLibraryManager:
    """Gerenciador integrado de biblioteca de ebooks para Streamlit."""
    
    def __init__(self, config_path="ebook_manager_config.json"):
        """
        Inicializa o gerenciador de biblioteca.
        
        Args:
            config_path: Caminho para o arquivo de configuração
        """
        self.config_path = config_path
        self.sources = []
        self.taxonomy_path = None
        self.notion_integration = None
        
        # Carregar configuração se existir
        if os.path.exists(config_path):
            self.load_config()
        else:
            self.create_default_config()
    
    def load_config(self):
        """Carrega a configuração do arquivo."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Carregar fontes de ebooks
            self.sources = []
            for source in config.get('sources', []):
                self.sources.append({
                    "name": source.get('name', ''),
                    "type": source.get('type', ''),
                    "path": source.get('path', ''),
                    "config": source.get('config', {}),
                    "last_scan": source.get('last_scan')
                })
                
            # Carregar caminho da taxonomia
            self.taxonomy_path = config.get('taxonomy_path')
            
            logger.info(f"Configuração carregada: {len(self.sources)} fontes de ebooks")
                
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {str(e)}")
            self.create_default_config()
    
    def save_config(self):
        """Salva a configuração no arquivo."""
        config = {
            'sources': self.sources,
            'taxonomy_path': self.taxonomy_path
        }
            
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Configuração salva em {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {str(e)}")
            return False
    
    def create_default_config(self):
        """Cria uma configuração padrão."""
        self.sources = []
        self.taxonomy_path = "taxonomia_temas.json"
        self.save_config()
        logger.info("Configuração padrão criada")
    
    def add_source(self, name, type_name, path, config=None):
        """Adiciona uma nova fonte de ebooks."""
        if config is None:
            config = {}
            
        # Verificar se já existe uma fonte com este nome
        for i, source in enumerate(self.sources):
            if source["name"] == name:
                logger.warning(f"Já existe uma fonte com o nome '{name}'. Atualizando configuração.")
                self.sources[i]["type"] = type_name
                self.sources[i]["path"] = path
                self.sources[i]["config"] = config
                self.save_config()
                return True
        
        # Criar nova fonte
        source = {
            "name": name,
            "type": type_name,
            "path": path,
            "config": config,
            "last_scan": None
        }
        self.sources.append(source)
        self.save_config()
        logger.info(f"Fonte '{name}' adicionada com sucesso")
        return True
    
    def remove_source(self, name):
        """Remove uma fonte de ebooks pelo nome."""
        for i, source in enumerate(self.sources):
            if source["name"] == name:
                del self.sources[i]
                self.save_config()
                logger.info(f"Fonte '{name}' removida com sucesso")
                return True
                
        logger.warning(f"Fonte '{name}' não encontrada")
        return False
    
    def get_source_by_name(self, name):
        """Obtém uma fonte pelo nome."""
        for source in self.sources:
            if source["name"] == name:
                return source
        return None
    
    def scan_source(self, source_name):
        """
        Escaneia uma fonte de ebooks e gera um relatório CSV.
        
        Args:
            source_name: Nome da fonte a ser escaneada
            
        Returns:
            Caminho para o arquivo CSV gerado
        """
        source = self.get_source_by_name(source_name)
                
        if not source:
            logger.error(f"Fonte '{source_name}' não encontrada")
            return None
            
        # Gerar nome para o arquivo CSV
        csv_name = f"ebooks_{source['name'].lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Escanear de acordo com o tipo da fonte
        if source["type"] == 'icloud':
            csv_path = self._scan_icloud(source, csv_name)
        elif source["type"] == 'filesystem':
            csv_path = self._scan_filesystem(source, csv_name)
        elif source["type"] == 'dropbox':
            csv_path = self._scan_dropbox(source, csv_name)
        elif source["type"] == 'kindle':
            csv_path = self._scan_kindle(source, csv_name)
        else:
            logger.error(f"Tipo de fonte '{source['type']}' não suportado")
            return None
            
        # Atualizar data do último escaneamento
        for i, src in enumerate(self.sources):
            if src["name"] == source_name:
                self.sources[i]["last_scan"] = datetime.now().isoformat()
                self.save_config()
                break
        
        return csv_path
    
    def _scan_icloud(self, source, csv_name):
        """Escaneia uma fonte iCloud."""
        try:
            logger.info(f"Escaneando fonte iCloud: {source['name']}")
            
            # Obter credenciais
            username = source["config"].get("username")
            password = source["config"].get("password")
            
            if not username or not password:
                st.error("Credenciais do iCloud não configuradas.")
                return None
            
            # Criar scanner
            logger.info(f"Conectando ao iCloud com usuário {username}")
            scanner = ICloudEbookScanner(username, password)
            
            # Escanear pasta
            ebooks = scanner.scan_pasta(source["path"])
            
            # Gerar relatório CSV
            relatorio_csv = scanner.gerar_relatorio(ebooks, formato='csv')
            
            # Salvar relatório
            csv_path = os.path.join(os.getcwd(), csv_name)
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write(relatorio_csv)
                
            logger.info(f"Relatório salvo em {csv_path}")
            return csv_path
                
        except Exception as e:
            logger.error(f"Erro ao escanear fonte iCloud: {str(e)}")
            st.error(f"Erro ao escanear iCloud: {str(e)}")
            return None
    
    def _scan_filesystem(self, source, csv_name):
        """Escaneia uma pasta no sistema de arquivos."""
        try:
            logger.info(f"Escaneando pasta: {source['path']}")
            
            scanner = FileSystemEbookScanner()
            ebooks = scanner.scan_folder(source["path"])
            
            # Gerar relatório CSV
            csv_path = os.path.join(os.getcwd(), csv_name)
            scanner.save_report_csv(ebooks, csv_path)
            
            logger.info(f"Relatório salvo em {csv_path}: {len(ebooks)} ebooks encontrados")
            return csv_path
            
        except Exception as e:
            logger.error(f"Erro ao escanear pasta no sistema de arquivos: {str(e)}")
            st.error(f"Erro ao escanear sistema de arquivos: {str(e)}")
            return None
    
    def _scan_dropbox(self, source, csv_name):
        """Escaneia uma pasta no Dropbox."""
        try:
            logger.info(f"Escaneando pasta Dropbox: {source['path']}")
            
            # Obter token das configurações
            token = source["config"].get("token")
            
            if not token:
                logger.error("Token do Dropbox não configurado para esta fonte")
                st.error("Token do Dropbox não configurado.")
                return None
            
            scanner = DropboxEbookScanner(token)
            ebooks = scanner.scan_folder(source["path"])
            
            # Gerar relatório CSV
            csv_path = os.path.join(os.getcwd(), csv_name)
            scanner.save_report_csv(ebooks, csv_path)
            
            logger.info(f"Relatório salvo em {csv_path}: {len(ebooks)} ebooks encontrados")
            return csv_path
            
        except Exception as e:
            logger.error(f"Erro ao escanear pasta no Dropbox: {str(e)}")
            st.error(f"Erro ao escanear Dropbox: {str(e)}")
            return None
    
    def _scan_kindle(self, source, csv_name):
        """Escaneia a biblioteca do Kindle."""
        try:
            logger.info(f"Escaneando biblioteca Kindle: {source['name']}")
            
            scanner = KindleEbookScanner()
            ebooks = scanner.scan_kindle_library(source["path"])
            
            # Gerar relatório CSV
            csv_path = os.path.join(os.getcwd(), csv_name)
            scanner.save_report_csv(ebooks, csv_path)
            
            logger.info(f"Relatório salvo em {csv_path}: {len(ebooks)} ebooks encontrados")
            return csv_path
            
        except Exception as e:
            logger.error(f"Erro ao processar biblioteca Kindle: {str(e)}")
            st.error(f"Erro ao escanear Kindle: {str(e)}")
            return None
    
    def enrich_csv(self, csv_path):
        """
        Enriquece os dados de um arquivo CSV de ebooks.
        
        Args:
            csv_path: Caminho para o arquivo CSV
            
        Returns:
            Caminho para o CSV enriquecido
        """
        try:
            logger.info(f"Enriquecendo dados do arquivo {csv_path}")
            
            # Inicializar enriquecedor
            enricher = EbookEnricher(temas_path=self.taxonomy_path)
            
            # Enriquecer dados
            enriched_ebooks = enricher.enrich_ebooks_from_csv(csv_path)
            
            # Criar CSV pronto para o Notion
            notion_csv = enricher.create_notion_ready_csv(
                os.path.splitext(csv_path)[0] + '_enriched.csv'
            )
            
            logger.info(f"Dados enriquecidos salvos em {notion_csv}")
            return notion_csv
            
        except Exception as e:
            logger.error(f"Erro ao enriquecer dados: {str(e)}")
            st.error(f"Erro ao enriquecer dados: {str(e)}")
            return None
    
    def export_to_notion(self, csv_path):
        """
        Exporta dados de um arquivo CSV para o Notion.
        
        Args:
            csv_path: Caminho para o arquivo CSV
            
        Returns:
            True se a exportação for bem-sucedida, False caso contrário
        """
        try:
            logger.info(f"Exportando dados para o Notion: {csv_path}")
            
            # Configurar integração com o Notion, se necessário
            if not self.notion_integration:
                self.notion_integration = configure_notion_integration()
            
            # Importar ebooks para o Notion
            page_ids = self.notion_integration.import_ebooks_from_csv(csv_path)
            
            if page_ids:
                logger.info(f"Exportação concluída: {len(page_ids)} ebooks exportados para o Notion")
                return True
            else:
                logger.warning("Nenhum ebook foi exportado para o Notion")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao exportar para o Notion: {str(e)}")
            st.error(f"Erro ao exportar para o Notion: {str(e)}")
            return False
    
    def merge_libraries(self, csv_paths, output_path=None):
        """
        Mescla várias bibliotecas de ebooks em um único CSV.
        
        Args:
            csv_paths: Lista de caminhos para arquivos CSV
            output_path: Caminho opcional para o arquivo de saída
            
        Returns:
            Caminho para o CSV mesclado
        """
        if not output_path:
            output_path = f"ebooks_merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
        try:
            logger.info(f"Mesclando {len(csv_paths)} bibliotecas")
            
            all_ebooks = []
            
            for csv_path in csv_paths:
                try:
                    df = pd.read_csv(csv_path)
                    # Adicionar coluna para identificar a fonte
                    source_name = os.path.basename(csv_path).replace('.csv', '')
                    df['Fonte'] = source_name
                    
                    all_ebooks.append(df)
                except Exception as e:
                    logger.warning(f"Erro ao ler {csv_path}: {str(e)}")
            
            if not all_ebooks:
                logger.error("Nenhum arquivo CSV válido encontrado")
                return None
                
            # Mesclar todos os DataFrames
            merged_df = pd.concat(all_ebooks, ignore_index=True)
            
            # Remover duplicatas com base no título e autor
            if 'Titulo_Extraido' in merged_df.columns and 'Autor_Extraido' in merged_df.columns:
                merged_df = merged_df.drop_duplicates(subset=['Titulo_Extraido', 'Autor_Extraido'])
            else:
                # Se não tiver esses campos, usar o nome do arquivo
                merged_df = merged_df.drop_duplicates(subset=['Nome'])
                
            # Salvar arquivo mesclado
            merged_df.to_csv(output_path, index=False, encoding='utf-8')
            
            logger.info(f"Mesclagem concluída: {len(merged_df)} ebooks únicos salvos em {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erro ao mesclar bibliotecas: {str(e)}")
            st.error(f"Erro ao mesclar bibliotecas: {str(e)}")
            return None


# Inicializar sessão do Streamlit se ainda não existir
if 'manager' not in st.session_state:
    st.session_state.manager = EbookLibraryManager()

if 'current_page' not in st.session_state:
    st.session_state.current_page = "home"

if 'scan_results' not in st.session_state:
    st.session_state.scan_results = {}

if 'last_processed_file' not in st.session_state:
    st.session_state.last_processed_file = None

# Função para mudar de página
def change_page(page):
    st.session_state.current_page = page

# Barra lateral com navegação
st.sidebar.markdown("## 📚 Gerenciador de Ebooks")
st.sidebar.markdown("---")

# Botões de navegação
if st.sidebar.button("🏠 Início"):
    change_page("home")
if st.sidebar.button("⚙️ Configurar Fontes"):
    change_page("setup")
if st.sidebar.button("🔍 Escanear Fontes"):
    change_page("scan")
if st.sidebar.button("📋 Visualizar Biblioteca"):
    change_page("view")
if st.sidebar.button("📊 Dashboard e Análise"):
    change_page("dashboard")
if st.sidebar.button("🔄 Fluxo Completo"):
    change_page("workflow")

st.sidebar.markdown("---")
st.sidebar.info("Versão 1.0.0")

# Página Principal
if st.session_state.current_page == "home":
    st.markdown('<div class="main-header">📚 Gerenciador de Biblioteca de Ebooks</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Esta aplicação permite gerenciar sua biblioteca de ebooks de várias fontes, 
    enriquecer metadados, visualizar estatísticas e integrar com outras ferramentas.
    """)
    
    # Dashboard rápido - resumo da biblioteca
    st.markdown('<div class="section-header">📊 Resumo da Biblioteca</div>', unsafe_allow_html=True)
    
    # Encontrar arquivos CSV recentes
    csv_files = [f for f in os.listdir() if f.endswith('.csv') and os.path.isfile(f)]
    
    if csv_files:
        # Ordenar por data de modificação (mais recente primeiro)
        csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Verificar se há arquivos enriquecidos
        enriched_files = [f for f in csv_files if 'enriched' in f]
        if enriched_files:
            latest_file = enriched_files[0]
        else:
            latest_file = csv_files[0]
        
        try:
            df = pd.read_csv(latest_file)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Ebooks", len(df))
            
            with col2:
                if 'Tamanho(MB)' in df.columns:
                    total_size = df['Tamanho(MB)'].sum()
                    st.metric("Tamanho Total", f"{total_size:.2f} MB")
                else:
                    st.metric("Tamanho Total", "N/D")
            
            with col3:
                if 'Autor' in df.columns or 'Autor_Extraido' in df.columns:
                    autor_col = 'Autor' if 'Autor' in df.columns else 'Autor_Extraido'
                    unique_authors = df[autor_col].nunique()
                    st.metric("Autores Únicos", unique_authors)
                else:
                    st.metric("Autores Únicos", "N/D")
                    
            st.caption(f"Dados do arquivo: {latest_file}")
            
            # Link para visualização completa
            if st.button("Ver Dashboard Completo"):
                change_page("dashboard")
                
        except Exception as e:
            st.warning(f"Não foi possível carregar o resumo da biblioteca: {str(e)}")
    else:
        st.info("Nenhum dado disponível. Escaneie suas fontes de ebooks para visualizar estatísticas.")
    
    # Fontes configuradas
    st.markdown('<div class="section-header">📂 Fontes Configuradas</div>', unsafe_allow_html=True)
    
    if st.session_state.manager.sources:
        for i, source in enumerate(st.session_state.manager.sources):
            last_scan = source.get("last_scan", "Nunca")
            if last_scan and last_scan != "Nunca":
                try:
                    last_scan_date = datetime.fromisoformat(last_scan)
                    last_scan = last_scan_date.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
                    
            st.markdown(f"""
            <div class="info-card">
                <h3>{source["name"]}</h3>
                <p><strong>Tipo:</strong> {source["type"]}</p>
                <p><strong>Caminho:</strong> {source["path"]}</p>
                <p><strong>Último escaneamento:</strong> {last_scan}</p>
            </div>
            """, unsafe_allow_html=True)
            
        if st.button("Configurar Fontes"):
            change_page("setup")
    else:
        st.warning("Nenhuma fonte configurada.")
        if st.button("Adicionar Fontes"):
            change_page("setup")
    
    # Links rápidos
    st.markdown('<div class="section-header">🔗 Ações Rápidas</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Escanear Fontes"):
            change_page("scan")
            
    with col2:
        if st.button("Visualizar Biblioteca"):
            change_page("view")
            
    with col3:
        if st.button("Executar Fluxo Completo"):
            change_page("workflow")

# Página de Configuração de Fontes
elif st.session_state.current_page == "setup":
    st.markdown('<div class="main-header">⚙️ Configuração de Fontes</div>', unsafe_allow_html=True)
    
    # Abas para configuração
    tab1, tab2, tab3 = st.tabs(["Adicionar Fonte", "Gerenciar Fontes", "Configurar Taxonomia"])
    
    with tab1:
        st.markdown('<div class="section-header">📂 Adicionar Nova Fonte</div>', unsafe_allow_html=True)
        
        # Formulário para adicionar fonte
        with st.form("add_source_form"):
            name = st.text_input("Nome da Fonte", placeholder="Ex: Meus Ebooks no iCloud")
            
            source_type = st.selectbox(
                "Tipo de Fonte",
                options=["icloud", "filesystem", "dropbox", "kindle"],
                format_func=lambda x: {
                    "icloud": "iCloud Drive",
                    "filesystem": "Sistema de Arquivos Local",
                    "dropbox": "Dropbox",
                    "kindle": "Amazon Kindle"
                }[x]
            )
            
            path = st.text_input(
                "Caminho", 
                placeholder={"icloud": "Ex: Documents/Ebooks",
                             "filesystem": "Ex: C:/Meus Ebooks",
                             "dropbox": "Ex: /Ebooks",
                             "kindle": "Ex: biblioteca_kindle.csv"}[source_type]
            )
            
            # Configurações específicas por tipo
            if source_type == "icloud":
                st.subheader("Credenciais do iCloud")
                username = st.text_input("Email do iCloud")
                password = st.text_input("Senha do iCloud", type="password")
                config = {"username": username, "password": password}
                
            elif source_type == "dropbox":
                st.subheader("Configuração do Dropbox")
                st.markdown("Você precisa de um token de acesso do Dropbox. [Saiba mais](https://www.dropbox.com/developers/apps)")
                token = st.text_input("Token de Acesso")
                config = {"token": token}
                
            else:
                config = {}
            
            submitted = st.form_submit_button("Adicionar Fonte")
            
            if submitted:
                if not name or not path:
                    st.error("Nome e caminho são obrigatórios.")
                elif source_type == "icloud" and (not username or not password):
                    st.error("Credenciais do iCloud são obrigatórias.")
                elif source_type == "dropbox" and not token:
                    st.error("Token do Dropbox é obrigatório.")
                else:
                    if st.session_state.manager.add_source(name, source_type, path, config):
                        st.success(f"Fonte '{name}' adicionada com sucesso!")
                    else:
                        st.error("Erro ao adicionar fonte.")
    
    with tab2:
        st.markdown('<div class="section-header">📋 Gerenciar Fontes</div>', unsafe_allow_html=True)
        
        if not st.session_state.manager.sources:
            st.warning("Nenhuma fonte configurada.")
        else:
            for i, source in enumerate(st.session_state.manager.sources):
                with st.expander(f"{source['name']} ({source['type']})"):
                    st.markdown(f"**Tipo:** {source['type']}")
                    st.markdown(f"**Caminho:** {source['path']}")
                    
                    last_scan = source.get("last_scan", "Nunca")
                    if last_scan and last_scan != "Nunca":
                        try:
                            last_scan_date = datetime.fromisoformat(last_scan)
                            last_scan = last_scan_date.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                    st.markdown(f"**Último escaneamento:** {last_scan}")
                    
                    if st.button(f"Remover {source['name']}", key=f"remove_{i}"):
                        if st.session_state.manager.remove_source(source['name']):
                            st.success(f"Fonte '{source['name']}' removida com sucesso!")
                            st.rerun()
                        else:
                            st.error(f"Erro ao remover fonte '{source['name']}'.")
    
    with tab3:
        st.markdown('<div class="section-header">📋 Configurar Taxonomia de Temas</div>', unsafe_allow_html=True)
        
        current_path = st.session_state.manager.taxonomy_path
        st.markdown(f"**Caminho atual:** {current_path}")
        
        # Upload de arquivo de taxonomia
        uploaded_file = st.file_uploader("Carregar arquivo de taxonomia", type=["json"])
        
        if uploaded_file is not None:
            # Salvar o arquivo
            try:
                with open(uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Arquivo carregado: {uploaded_file.name}")
                
                # Atualizar caminho
                new_path = uploaded_file.name
                st.session_state.manager.taxonomy_path = new_path
                st.session_state.manager.save_config()
                st.success(f"Taxonomia atualizada para: {new_path}")
            except Exception as e:
                st.error(f"Erro ao salvar arquivo: {str(e)}")
                
        # Ou inserir caminho manualmente
        st.markdown("### Ou especifique o caminho manualmente")
        new_path = st.text_input("Caminho para o arquivo de taxonomia", value=current_path)
        
        if st.button("Atualizar Caminho"):
            st.session_state.manager.taxonomy_path = new_path
            if st.session_state.manager.save_config():
                st.success(f"Taxonomia atualizada para: {new_path}")
            else:
                st.error("Erro ao atualizar taxonomia.")

# Página de Escaneamento
elif st.session_state.current_page == "scan":
    st.markdown('<div class="main-header">🔍 Escanear Fontes</div>', unsafe_allow_html=True)
    
    if not st.session_state.manager.sources:
        st.warning("Nenhuma fonte configurada.")
        if st.button("Adicionar Fontes"):
            change_page("setup")
    else:
        st.markdown("""
        Selecione uma fonte para escanear ou escaneie todas as fontes de uma vez.
        O processo pode levar algum tempo dependendo do tamanho da biblioteca.
        """)
        
        # Opção para escanear todas as fontes
        if st.button("Escanear Todas as Fontes"):
            csv_paths = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, source in enumerate(st.session_state.manager.sources):
                progress = i / len(st.session_state.manager.sources)
                progress_bar.progress(progress)
                status_text.text(f"Escaneando {source['name']}...")
                
                csv_path = st.session_state.manager.scan_source(source['name'])
                if csv_path:
                    csv_paths.append(csv_path)
                    st.session_state.scan_results[source['name']] = {
                        "status": "success",
                        "message": f"Escaneamento concluído: {csv_path}",
                        "path": csv_path
                    }
                else:
                    st.session_state.scan_results[source['name']] = {
                        "status": "error",
                        "message": f"Erro ao escanear {source['name']}",
                        "path": None
                    }
                    
            progress_bar.progress(1.0)
            status_text.text("Escaneamento concluído!")
            
            if csv_paths:
                st.success(f"Escaneamento concluído para {len(csv_paths)} fontes!")
                
                if len(csv_paths) > 1:
                    if st.button("Mesclar Resultados"):
                        merged_path = st.session_state.manager.merge_libraries(csv_paths)
                        if merged_path:
                            st.success(f"Mesclagem concluída! Arquivo: {merged_path}")
                            st.session_state.last_processed_file = merged_path
                            
                            if st.button("Enriquecer Dados"):
                                change_page("workflow")
            else:
                st.error("Não foi possível escanear nenhuma fonte.")
        
        # Interface para escanear uma fonte específica
        st.markdown('<div class="section-header">📂 Escanear Fonte Específica</div>', unsafe_allow_html=True)
        
        source_names = [source['name'] for source in st.session_state.manager.sources]
        selected_source = st.selectbox("Selecione uma fonte", source_names)
        
        if st.button(f"Escanear {selected_source}"):
            with st.spinner(f"Escaneando {selected_source}..."):
                csv_path = st.session_state.manager.scan_source(selected_source)
                
                if csv_path:
                    st.success(f"Escaneamento concluído! Arquivo: {csv_path}")
                    st.session_state.scan_results[selected_source] = {
                        "status": "success",
                        "message": f"Escaneamento concluído: {csv_path}",
                        "path": csv_path
                    }
                    st.session_state.last_processed_file = csv_path
                    
                    # Oferecer opções para próximos passos
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Enriquecer Dados"):
                            enriched_path = st.session_state.manager.enrich_csv(csv_path)
                            if enriched_path:
                                st.success(f"Dados enriquecidos! Arquivo: {enriched_path}")
                                st.session_state.last_processed_file = enriched_path
                    with col2:
                        if st.button("Visualizar Dados"):
                            change_page("view")
                            
                else:
                    st.error(f"Erro ao escanear {selected_source}")
                    st.session_state.scan_results[selected_source] = {
                        "status": "error",
                        "message": f"Erro ao escanear {selected_source}",
                        "path": None
                    }
        
        # Exibir resultados anteriores
        if st.session_state.scan_results:
            st.markdown('<div class="section-header">📋 Resultados Recentes</div>', unsafe_allow_html=True)
            
            for source_name, result in st.session_state.scan_results.items():
                status_color = "green" if result["status"] == "success" else "red"
                st.markdown(
                    f"<div style='padding: 10px; border-left: 5px solid {status_color}; background-color: #f0f0f0;'>"
                    f"<strong>{source_name}:</strong> {result['message']}"
                    f"</div>",
                    unsafe_allow_html=True
                )

# Página de Visualização da Biblioteca
elif st.session_state.current_page == "view":
    st.markdown('<div class="main-header">📋 Visualizar Biblioteca</div>', unsafe_allow_html=True)
    
    # Encontrar arquivos CSV
    csv_files = [f for f in os.listdir() if f.endswith('.csv') and os.path.isfile(f)]
    
    if not csv_files:
        st.warning("Nenhum arquivo CSV encontrado. Escaneie suas fontes primeiro.")
        if st.button("Ir para Escaneamento"):
            change_page("scan")
    else:
        # Ordenar por data de modificação (mais recente primeiro)
        csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Priorizar o último arquivo processado, se houver
        if st.session_state.last_processed_file in csv_files:
            default_index = csv_files.index(st.session_state.last_processed_file)
        else:
            default_index = 0
            
        selected_file = st.selectbox(
            "Selecione um arquivo para visualizar", 
            csv_files,
            index=default_index
        )
        
        try:
            df = pd.read_csv(selected_file)
            
            # Informações básicas
            st.markdown('<div class="section-header">📊 Informações Básicas</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Ebooks", len(df))
            
            with col2:
                if 'Tamanho(MB)' in df.columns:
                    df['Tamanho(MB)'] = pd.to_numeric(df['Tamanho(MB)'], errors='coerce')
                    total_size = df['Tamanho(MB)'].sum()
                    st.metric("Tamanho Total", f"{total_size:.2f} MB")
                else:
                    st.metric("Tamanho Total", "N/D")
            
            with col3:
                if 'Autor' in df.columns or 'Autor_Extraido' in df.columns:
                    autor_col = 'Autor' if 'Autor' in df.columns else 'Autor_Extraido'
                    unique_authors = df[autor_col].nunique()
                    st.metric("Autores Únicos", unique_authors)
                else:
                    st.metric("Autores Únicos", "N/D")
            
            # Visualização dos dados
            st.markdown('<div class="section-header">📋 Dados</div>', unsafe_allow_html=True)
            
            # Opções de filtro
            st.markdown('<div class="subsection-header">🔍 Filtros</div>', unsafe_allow_html=True)
            
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                if 'Formato' in df.columns:
                    formats = ['Todos'] + sorted(df['Formato'].dropna().unique().tolist())
                    selected_format = st.selectbox("Formato", formats)
                    if selected_format != 'Todos':
                        df = df[df['Formato'] == selected_format]
            
            with filter_col2:
                author_col = None
                if 'Autor' in df.columns:
                    author_col = 'Autor'
                elif 'Autor_Extraido' in df.columns:
                    author_col = 'Autor_Extraido'
                    
                if author_col:
                    authors = ['Todos'] + sorted(df[author_col].dropna().unique().tolist())
                    selected_author = st.selectbox("Autor", authors)
                    if selected_author != 'Todos':
                        df = df[df[author_col] == selected_author]
            
            with filter_col3:
                if 'Temas' in df.columns:
                    # Extrair temas únicos de toda a coluna
                    all_themes = set()
                    for themes in df['Temas'].dropna():
                        if isinstance(themes, str):
                            theme_list = re.split(r'[,;]', themes)
                            all_themes.update([t.strip() for t in theme_list if t.strip()])
                    
                    if all_themes:
                        themes = ['Todos'] + sorted(all_themes)
                        selected_theme = st.selectbox("Tema", themes)
                        if selected_theme != 'Todos':
                            df = df[df['Temas'].str.contains(selected_theme, na=False)]
            
            # Exibir dados
            st.dataframe(df, use_container_width=True)
            
            # Opção para download
            st.download_button(
                label="📥 Download como CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name=f"biblioteca_ebooks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # Opções adicionais
            st.markdown('<div class="section-header">🔧 Opções Adicionais</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Enriquecer Dados"):
                    with st.spinner("Enriquecendo dados..."):
                        enriched_path = st.session_state.manager.enrich_csv(selected_file)
                        if enriched_path:
                            st.success(f"Dados enriquecidos! Arquivo: {enriched_path}")
                            st.session_state.last_processed_file = enriched_path
                            # Recarregar a página para mostrar o novo arquivo
                            st.rerun()
                        else:
                            st.error("Erro ao enriquecer dados.")
            
            with col2:
                if st.button("Exportar para Notion"):
                    with st.spinner("Exportando para Notion..."):
                        success = st.session_state.manager.export_to_notion(selected_file)
                        if success:
                            st.success("Exportação para Notion concluída com sucesso!")
                        else:
                            st.error("Erro ao exportar para Notion.")
            
            with col3:
                if st.button("Ver Dashboard"):
                    st.session_state.last_processed_file = selected_file
                    change_page("dashboard")
        
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo: {str(e)}")

# Página do Dashboard
elif st.session_state.current_page == "dashboard":
    st.markdown('<div class="main-header">📊 Dashboard da Biblioteca</div>', unsafe_allow_html=True)
    
    # Encontrar arquivos CSV
    csv_files = [f for f in os.listdir() if f.endswith('.csv') and os.path.isfile(f)]
    
    if not csv_files:
        st.warning("Nenhum arquivo CSV encontrado. Escaneie suas fontes primeiro.")
        if st.button("Ir para Escaneamento"):
            change_page("scan")
    else:
        # Ordenar arquivos
        csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Priorizar arquivos enriquecidos
        enriched_files = [f for f in csv_files if 'enriched' in f]
        if enriched_files:
            files_to_display = enriched_files + [f for f in csv_files if f not in enriched_files]
        else:
            files_to_display = csv_files
            
        # Priorizar o último arquivo processado, se houver
        if st.session_state.last_processed_file in files_to_display:
            default_index = files_to_display.index(st.session_state.last_processed_file)
        else:
            default_index = 0
            
        selected_file = st.selectbox(
            "Selecione um arquivo para análise", 
            files_to_display,
            index=default_index
        )
        
        try:
            # Carregar e processar dados
            df = load_data(selected_file)
            if df is None or df.empty:
                st.warning("Não foi possível carregar os dados ou o arquivo está vazio.")
            else:              
                df_processed = process_data(df)
            
            # Mostrar informações básicas
            st.markdown('<div class="section-header">📊 Informações da Biblioteca</div>', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Ebooks", len(df_processed))
            
            with col2:
                if 'Tamanho(MB)' in df_processed.columns:
                    df_processed['Tamanho(MB)'] = pd.to_numeric(df_processed['Tamanho(MB)'], errors='coerce')
                    total_size = df_processed['Tamanho(MB)'].sum()
                    st.metric("Tamanho Total", f"{total_size:.2f} MB")
                else:
                    st.metric("Tamanho Total", "N/D")
            
            with col3:
                if 'Autor' in df_processed.columns:
                    unique_authors = df_processed['Autor'].nunique()
                    st.metric("Autores Únicos", unique_authors)
                else:
                    st.metric("Autores Únicos", "N/D")
            
            # Abas para diferentes visualizações
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Estatísticas", "👥 Autores", "📑 Formatos e Temas", "🔍 Explorar"])
            
            with tab1:
                st.markdown('<div class="section-header">📊 Estatísticas Gerais</div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Distribuição por formatos
                    if 'Formato' in df_processed.columns:
                        format_counts = df_processed['Formato'].value_counts()
                        
                        st.markdown('<div class="subsection-header">📚 Distribuição por Formato</div>', unsafe_allow_html=True)
                        fig, ax = plt.subplots(figsize=(10, 6))
                        format_counts.plot(kind='bar', ax=ax, color='skyblue')
                        plt.xticks(rotation=45)
                        plt.ylabel('Quantidade')
                        plt.tight_layout()
                        st.pyplot(fig)
                        
                    # Distribuição por ano (se disponível)
                    if 'Ano' in df_processed.columns or 'Data Modificação' in df_processed.columns:
                        # Extrair ano se necessário
                        if 'Ano' not in df_processed.columns and 'Data Modificação' in df_processed.columns:
                            df_processed['Ano'] = df_processed['Data Modificação'].apply(extract_year)
                            
                        year_counts = df_processed['Ano'].dropna().astype(int).value_counts().sort_index()
                        
                        if not year_counts.empty:
                            st.markdown('<div class="subsection-header">📅 Distribuição por Ano</div>', unsafe_allow_html=True)
                            fig, ax = plt.subplots(figsize=(10, 6))
                            year_counts.plot(kind='line', marker='o', ax=ax, color='green')
                            plt.ylabel('Quantidade')
                            plt.grid(True, alpha=0.3)
                            plt.tight_layout()
                            st.pyplot(fig)
                
                with col2:
                    # Distribuição de tamanho
                    if 'Tamanho(MB)' in df_processed.columns:
                        st.markdown('<div class="subsection-header">📊 Distribuição de Tamanho</div>', unsafe_allow_html=True)
                        fig, ax = plt.subplots(figsize=(10, 6))
                        sns.histplot(df_processed['Tamanho(MB)'].dropna(), bins=20, kde=True, ax=ax, color='purple')
                        plt.xlabel('Tamanho (MB)')
                        plt.ylabel('Frequência')
                        plt.tight_layout()
                        st.pyplot(fig)
                        
                    # Top 5 maiores ebooks
                    if 'Tamanho(MB)' in df_processed.columns and 'Titulo' in df_processed.columns:
                        st.markdown('<div class="subsection-header">📚 Top 5 Maiores Ebooks</div>', unsafe_allow_html=True)
                        top_size = df_processed.sort_values('Tamanho(MB)', ascending=False).head(5)[['Titulo', 'Tamanho(MB)']]
                        
                        # Criar gráfico de barras horizontal
                        fig, ax = plt.subplots(figsize=(10, 5))
                        bars = ax.barh(top_size['Titulo'], top_size['Tamanho(MB)'], color='orange')
                        ax.set_xlabel('Tamanho (MB)')
                        ax.invert_yaxis()  # Inverter para que o maior fique no topo
                        
                        # Adicionar valores nas barras
                        for bar in bars:
                            width = bar.get_width()
                            ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{width:.1f} MB', 
                                    ha='left', va='center')
                            
                        plt.tight_layout()
                        st.pyplot(fig)
            
            with tab2:
                st.markdown('<div class="section-header">👥 Análise de Autores</div>', unsafe_allow_html=True)
                
                if 'Autor' not in df_processed.columns:
                    st.warning("Dados de autor não disponíveis.")
                else:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Top 10 autores por quantidade
                        author_counts = df_processed['Autor'].value_counts().head(10)
                        
                        st.markdown('<div class="subsection-header">🔝 Top 10 Autores por Quantidade</div>', unsafe_allow_html=True)
                        
                        # Criar gráfico com Altair para melhor interatividade
                        author_df = pd.DataFrame({
                            'Autor': author_counts.index,
                            'Quantidade': author_counts.values
                        })
                        
                        chart = alt.Chart(author_df).mark_bar().encode(
                            x='Quantidade:Q',
                            y=alt.Y('Autor:N', sort='-x'),
                            color=alt.Color('Quantidade:Q', scale=alt.Scale(scheme='blues')),
                            tooltip=['Autor', 'Quantidade']
                        ).properties(height=300)
                        
                        st.altair_chart(chart, use_container_width=True)
                    
                    with col2:
                        # Nuvem de palavras de autores
                        if len(df_processed['Autor'].dropna()) > 5:
                            st.markdown('<div class="subsection-header">🔤 Nuvem de Palavras - Autores</div>', unsafe_allow_html=True)
                            wordcloud = generate_wordcloud(df_processed['Autor'])
                            
                            fig, ax = plt.subplots(figsize=(10, 6))
                            ax.imshow(wordcloud, interpolation='bilinear')
                            ax.axis('off')
                            st.pyplot(fig)
                        
                        # Top autores por tamanho total
                        if 'Tamanho(MB)' in df_processed.columns:
                            author_size = df_processed.groupby('Autor')['Tamanho(MB)'].sum().sort_values(ascending=False).head(10)
                            
                            st.markdown('<div class="subsection-header">📊 Top 10 Autores por Volume (MB)</div>', unsafe_allow_html=True)
                            
                            author_size_df = pd.DataFrame({
                                'Autor': author_size.index,
                                'Tamanho Total (MB)': author_size.values
                            })
                            
                            chart = alt.Chart(author_size_df).mark_bar().encode(
                                x='Tamanho Total (MB):Q',
                                y=alt.Y('Autor:N', sort='-x'),
                                color=alt.Color('Tamanho Total (MB):Q', scale=alt.Scale(scheme='oranges')),
                                tooltip=['Autor', 'Tamanho Total (MB)']
                            ).properties(height=300)
                            
                            st.altair_chart(chart, use_container_width=True)
            
            with tab3:
                st.markdown('<div class="section-header">📑 Análise de Formatos e Temas</div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de pizza dos formatos
                    if 'Formato' in df_processed.columns:
                        format_counts = df_processed['Formato'].value_counts()
                        
                        st.markdown('<div class="subsection-header">📊 Distribuição de Formatos</div>', unsafe_allow_html=True)
                        
                        fig, ax = plt.subplots(figsize=(8, 8))
                        ax.pie(format_counts, labels=format_counts.index, autopct='%1.1f%%', 
                               startangle=90, shadow=True, explode=[0.05] * len(format_counts))
                        plt.axis('equal')
                        st.pyplot(fig)
                        
                    # Formato por ano (se disponível)
                    if 'Formato' in df_processed.columns and 'Ano' in df_processed.columns:
                        # Filtrar apenas linhas com ano válido
                        df_with_year = df_processed.dropna(subset=['Ano']).copy()
                        df_with_year['Ano'] = df_with_year['Ano'].astype(int)
                        
                        if not df_with_year.empty:
                            format_year = pd.crosstab(df_with_year['Ano'], df_with_year['Formato'])
                            
                            st.markdown('<div class="subsection-header">📈 Evolução de Formatos por Ano</div>', unsafe_allow_html=True)
                            
                            fig, ax = plt.subplots(figsize=(10, 6))
                            format_year.plot(kind='bar', stacked=True, ax=ax, cmap='viridis')
                            plt.xlabel('Ano')
                            plt.ylabel('Quantidade')
                            plt.xticks(rotation=45)
                            plt.legend(title='Formato')
                            plt.tight_layout()
                            st.pyplot(fig)
                
                with col2:
                    # Análise de temas (se disponível)
                    if 'Temas' in df_processed.columns:
                        # Processar temas (podem estar como lista, string separada por vírgula, etc.)
                        all_themes = []
                        
                        for themes in df_processed['Temas'].dropna():
                            if isinstance(themes, str):
                                # Split por vírgula ou ponto e vírgula
                                theme_list = re.split(r'[,;]', themes)
                                all_themes.extend([t.strip() for t in theme_list if t.strip()])
                        
                        if all_themes:
                            theme_counts = pd.Series(all_themes).value_counts().head(15)
                            
                            st.markdown('<div class="subsection-header">🔝 Top 15 Temas</div>', unsafe_allow_html=True)
                            
                            theme_df = pd.DataFrame({
                                'Tema': theme_counts.index,
                                'Quantidade': theme_counts.values
                            })
                            
                            chart = alt.Chart(theme_df).mark_bar().encode(
                                x='Quantidade:Q',
                                y=alt.Y('Tema:N', sort='-x'),
                                color=alt.Color('Quantidade:Q', scale=alt.Scale(scheme='greenblue')),
                                tooltip=['Tema', 'Quantidade']
                            ).properties(height=400)
                            
                            st.altair_chart(chart, use_container_width=True)
                            
                            # Nuvem de palavras de temas
                            st.markdown('<div class="subsection-header">🔤 Nuvem de Palavras - Temas</div>', unsafe_allow_html=True)
                            wordcloud = generate_wordcloud(pd.Series(all_themes))
                            
                            fig, ax = plt.subplots(figsize=(10, 6))
                            ax.imshow(wordcloud, interpolation='bilinear')
                            ax.axis('off')
                            st.pyplot(fig)
                        else:
                            st.info("Não foram encontrados temas nos dados.")
                    else:
                        st.info("Dados de temas não disponíveis. Execute o enriquecedor de ebooks para adicionar temas.")
            
            with tab4:
                st.markdown('<div class="section-header">🔍 Explorador de Dados</div>', unsafe_allow_html=True)
                
                # Filtros
                st.markdown('<div class="subsection-header">🔍 Filtros</div>', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if 'Formato' in df_processed.columns:
                        formats = ['Todos'] + sorted(df_processed['Formato'].dropna().unique().tolist())
                        selected_format = st.selectbox("Formato", formats)
                        if selected_format != 'Todos':
                            df_processed = df_processed[df_processed['Formato'] == selected_format]
                
                with col2:
                    if 'Autor' in df_processed.columns:
                        # Obter autores únicos e ordenar
                        authors = ['Todos'] + sorted(df_processed['Autor'].dropna().unique().tolist())
                        selected_author = st.selectbox("Autor", authors)
                        if selected_author != 'Todos':
                            df_processed = df_processed[df_processed['Autor'] == selected_author]
                
                with col3:
                    if 'Temas' in df_processed.columns:
                        # Extrair temas únicos
                        all_themes = set()
                        for themes in df_processed['Temas'].dropna():
                            if isinstance(themes, str):
                                theme_list = re.split(r'[,;]', themes)
                                all_themes.update([t.strip() for t in theme_list if t.strip()])
                        
                        themes = ['Todos'] + sorted(list(all_themes))
                        selected_theme = st.selectbox("Tema", themes)
                        if selected_theme != 'Todos':
                            df_processed = df_processed[df_processed['Temas'].str.contains(selected_theme, na=False)]
                
                # Mostrar dados filtrados
                st.markdown(f"<p>Mostrando {len(df_processed)} de {len(df)} ebooks</p>", unsafe_allow_html=True)
                
                # Seleção de colunas para exibir
                default_columns = ['Titulo', 'Autor', 'Formato', 'Tamanho(MB)']
                available_columns = [col for col in df_processed.columns if col in df_processed.columns]
                
                # Usar apenas colunas disponíveis dentre as default
                display_columns = [col for col in default_columns if col in available_columns]
                
                # Adicionar mais colunas se necessário
                if 'Temas' in available_columns and 'Temas' not in display_columns:
                    display_columns.append('Temas')
                    
                if 'Data Modificação' in available_columns and 'Data Modificação' not in display_columns:
                    display_columns.append('Data Modificação')
                
                # Exibir tabela paginada
                st.dataframe(df_processed[display_columns], use_container_width=True)
                
                # Opção para download
                csv = df_processed.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download dados filtrados como CSV",
                    data=csv,
                    file_name=f"ebooks_filtrados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
        
        except Exception as e:
            st.error(f"Erro ao processar dados para o dashboard: {str(e)}")

# Página de Fluxo de Trabalho Completo
elif st.session_state.current_page == "workflow":
    st.markdown('<div class="main-header">🔄 Fluxo de Trabalho Completo</div>', unsafe_allow_html=True)
    
    st.markdown("""
    O fluxo de trabalho completo executa as seguintes etapas:
    1. Escanear todas as fontes configuradas
    2. Mesclar os resultados em um único arquivo
    3. Enriquecer os metadados dos ebooks
    4. Opcionalmente, exportar para o Notion
    """)
    
    if not st.session_state.manager.sources:
        st.warning("Nenhuma fonte configurada. Adicione fontes primeiro.")
        if st.button("Configurar Fontes"):
            change_page("setup")
    else:
        # Iniciar fluxo
        if st.button("Iniciar Fluxo Completo"):
            st.markdown('<div class="section-header">⏳ Progresso</div>', unsafe_allow_html=True)
            
            # Criar placeholders para status
            scan_status = st.empty()
            merge_status = st.empty()
            enrich_status = st.empty()
            notion_status = st.empty()
            
            # Barra de progresso geral
            progress_bar = st.progress(0)
            
            # 1. Escanear todas as fontes
            scan_status.markdown("🔍 **Escaneando fontes...**")
            
            csv_paths = []
            for i, source in enumerate(st.session_state.manager.sources):
                source_status = st.empty()
                source_status.markdown(f"Escaneando {source['name']}...")
                
                csv_path = st.session_state.manager.scan_source(source['name'])
                if csv_path:
                    csv_paths.append(csv_path)
                    source_status.markdown(f"✅ {source['name']} escaneado com sucesso.")
                else:
                    source_status.markdown(f"❌ Erro ao escanear {source['name']}.")
                
                # Atualizar progresso
                progress = (i + 1) / (len(st.session_state.manager.sources) * 3 + 1)  # +1 para mesclagem
                progress_bar.progress(progress)
            
            if not csv_paths:
                scan_status.markdown("❌ **Nenhum ebook encontrado.**")
                progress_bar.progress(1.0)
                st.error("Falha no fluxo de trabalho: Nenhum ebook encontrado.")
            else:                
                scan_status.markdown("✅ **Escaneamento concluído.**")
            
            # 2. Mesclar resultados
            merge_status.markdown("🔄 **Mesclando bibliotecas...**")
            
            merged_path = st.session_state.manager.merge_libraries(csv_paths)
            if not merged_path:
                merge_status.markdown("❌ **Falha ao mesclar bibliotecas.**")
                progress_bar.progress(1.0)
                st.error("Falha no fluxo de trabalho: Erro ao mesclar bibliotecas.")
            else:                
                merge_status.markdown("✅ **Mesclagem concluída.**")
            
            # Atualizar progresso
            progress = (len(st.session_state.manager.sources) + 1) / (len(st.session_state.manager.sources) * 3 + 1)
            progress_bar.progress(progress)
            
            # 3. Enriquecer dados
            enrich_status.markdown("🔍 **Enriquecendo metadados...**")
            
            enriched_path = st.session_state.manager.enrich_csv(merged_path)
            if not enriched_path:
                enrich_status.markdown("❌ **Falha ao enriquecer dados.**")
                progress_bar.progress(1.0)
                st.error("Falha no fluxo de trabalho: Erro ao enriquecer dados.")
            else:                
                enrich_status.markdown("✅ **Enriquecimento concluído.**")
                st.session_state.last_processed_file = enriched_path
            
            # Atualizar progresso para quase completo
            progress = 0.9
            progress_bar.progress(progress)
            
            # 4. Exportar para o Notion (opcional)
            export_notion = st.checkbox("Exportar para o Notion", value=False)
            
            if export_notion:
                notion_status.markdown("🔄 **Exportando para o Notion...**")
                
                success = st.session_state.manager.export_to_notion(enriched_path)
                if success:
                    notion_status.markdown("✅ **Exportação para o Notion concluída.**")
                else:
                    notion_status.markdown("❌ **Falha ao exportar para o Notion.**")
            else:
                notion_status.markdown("⏸️ **Exportação para o Notion ignorada.**")
            
            # Fluxo concluído
            progress_bar.progress(1.0)
            
            st.markdown('<div class="success-message">🎉 Fluxo de trabalho concluído com sucesso!</div>', unsafe_allow_html=True)
            
            # Opções para próximos passos
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Visualizar Biblioteca"):
                    change_page("view")
                    
            with col2:
                if st.button("Ver Dashboard"):
                    change_page("dashboard")

# Rodapé
st.markdown("---")
st.markdown("📚 Gerenciador de Biblioteca de Ebooks | Desenvolvido com ❤️ usando Streamlit")