import streamlit as st
import logging
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ebook_manager.log"),
        logging.StreamHandler()
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
# Importar os novos enriquecedores
from adapters.enrichers.default_enricher import DefaultEnricher
from adapters.enrichers.basic_enricher import BasicEnricher
from adapters.enrichers.external_api_enricher import ExternalAPIEnricher
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
        "kindle": KindleScanner()
    }
    
    # Create services
    scan_service = ScanService(scanner_registry)
    enrich_service = EnrichService()
    # Criar instâncias dos enriquecedores
    default_enricher = DefaultEnricher()
    basic_enricher = BasicEnricher()
    external_api_enricher = ExternalAPIEnricher()
    # Registrar os enriquecedores
    enrich_service.register_enricher('default', default_enricher)
    enrich_service.register_enricher('basic', basic_enricher)
    enrich_service.register_enricher('external_api', external_api_enricher)
    # Definir o enriquecedor padrão
    enrich_service.set_active_enricher('default')
    
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