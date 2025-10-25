import streamlit as st
import logging
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Initialize logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ebook_manager.log", encoding='utf-8'),  # Add encoding='utf-8'
        logging.StreamHandler()  # Console handler
    ]
)
logger = logging.getLogger(__name__)

# Import service initialization code
from core.repositories.config_repository import ConfigRepository
from core.services.credential_service import CredentialService
from core.services.library_service import LibraryService
from core.services.scan_service import ScanService
from core.services.enrich_service import EnrichService
from core.services.export_service import ExportService

from adapters.scanners.icloud_scanner import ICloudScanner
from adapters.scanners.filesystem_scanner import FileSystemScanner
from adapters.scanners.dropbox_scanner import DropboxScanner
from adapters.scanners.kindle_scanner import KindleScanner
from adapters.scanners.kindle_cloud_scanner import KindleCloudScanner
# Importar os novos enriquecedores
from adapters.enrichers.default_enricher import DefaultEnricher
from adapters.enrichers.basic_enricher import BasicEnricher
from adapters.enrichers.external_api_enricher import ExternalAPIEnricher
from adapters.enrichers.google_books_enricher import GoogleBooksEnricher
from adapters.enrichers.factory import register_all_enrichers
from adapters.notion_adapter import NotionExporter

from ui.state import AppState
from ui.router import render_page

# Function to load CSS from external file
def load_css(css_file):
    """
    Loads CSS from a file and applies it to the application.
    
    Args:
        css_file: Path to the CSS file
    """
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        logger.warning(f"CSS file not found: {css_file}")
        # Basic fallback styles
        st.markdown("""
        <style>
            .main-header { font-size: 2.5rem; font-weight: bold; margin-bottom: 1rem; }
            .section-header { font-size: 1.8rem; font-weight: bold; margin-top: 1.5rem; margin-bottom: 1rem; }
            .info-card { background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; border-left: 5px solid #0d6efd; }
        </style>
        """, unsafe_allow_html=True)

# App configuration
st.set_page_config(
    page_title="Gerenciador de Biblioteca de Ebooks",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
css_path = os.path.join("static", "css", "style.css")
load_css(css_path)

# Service initialization (only once)
if 'initialized' not in st.session_state:
    # Create repositories and services
    config_repository = ConfigRepository("ebook_manager_config.json")
    credential_service = CredentialService()
    
    # Create scanner registry
    scanner_registry = {
        "icloud": ICloudScanner(credential_service),
        "filesystem": FileSystemScanner(),
        "dropbox": DropboxScanner(),
        "kindle": KindleScanner(),
        "kindle_cloud": KindleCloudScanner(credential_service)
    }
    
    # Create services
    scan_service = ScanService(scanner_registry)
    enrich_service = EnrichService()

    # Load API keys from configuration (if available)
    enricher_config = {}
    try:
        # This assumes you have a way to get API keys from configuration
        # This could be from a JSON file, environment variables, etc.
        # Here's a simple example using config_repository
        config = config_repository.load_config()
        if 'enrichers' in config:
            if 'external_api_key' in config['enrichers']:
                enricher_config['external_api_key'] = config['enrichers']['external_api_key']
            if 'google_books_api_key' in config['enrichers']:
                enricher_config['google_books_api_key'] = config['enrichers']['google_books_api_key']
    except Exception as e:
        logger.warning(f"Could not load enricher API keys from configuration: {str(e)}")

    # Register all enrichers using the factory
    register_all_enrichers(enrich_service, enricher_config, set_default='default')

  
    export_service = ExportService()
    
    # Create library service
    library_service = LibraryService(
        config_repository,
        credential_service,
        scan_service,
        enrich_service,
        export_service
    )
    
    # Create application state
    app_state = AppState()
    
    # Store in session state
    st.session_state.library_service = library_service
    st.session_state.app_state = app_state
    st.session_state.initialized = True

# Get services and state from session
library_service = st.session_state.library_service
app_state = st.session_state.app_state

# Sidebar navigation
st.sidebar.markdown("## 📚 Gerenciador de Ebooks")
st.sidebar.markdown("---")

# Navigation buttons
if st.sidebar.button("🏠 Início"):
    app_state.change_page("home")
    st.rerun()
if st.sidebar.button("⚙️ Configurar Fontes"):
    app_state.change_page("setup")
    st.rerun()
if st.sidebar.button("⚙️ Configurar Notion"):
    app_state.change_page("notion_config")
    st.rerun()
if st.sidebar.button("🔮 Configurar Obsidian"):
    app_state.change_page("obsidian_config")
    st.rerun()
if st.sidebar.button("🔍 Escanear Fontes"):
    app_state.change_page("scan")
    st.rerun()
if st.sidebar.button("📋 Visualizar Biblioteca"):
    app_state.change_page("view")
    st.rerun()
if st.sidebar.button("📊 Dashboard e Análise"):
    app_state.change_page("dashboard")
    st.rerun()
if st.sidebar.button("🔄 Fluxo Completo"):
    app_state.change_page("workflow")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("Versão 2.0.0 - Refatorado com princípios SOLID")

# Render the current page
current_page = app_state.current_page
render_page(current_page, library_service, app_state)

# Footer
st.markdown("---")
st.markdown("📚 Gerenciador de Biblioteca de Ebooks v2.0.0 | Refatorado para princípios SOLID")

import logging
from adapters.scanners.icloud_scanner import ICloudScanner

logger = logging.getLogger(__name__)

def execute_scan():
    try:
        # Obter credenciais da configuração ou ambiente
        username = config.get('ICLOUD_USERNAME')
        password = config.get('ICLOUD_PASSWORD')
        
        if not username or not password:
            logger.error("Credenciais do iCloud não configuradas")
            return None
            
        # Inicializar e autenticar o scanner
        scanner = ICloudScanner(username, password)
        scanner.authenticate()  # Agora vai lidar com 2FA automaticamente
        
        # Executar o scan
        return scanner.scan()
        
    except Exception as e:
        logger.error(f"Erro durante o scan do iCloud: {str(e)}")
        return None