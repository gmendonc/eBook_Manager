# ui/pages/notion_config_page.py
import streamlit as st
from core.repositories.notion_config_repository import NotionConfigRepository

def render_notion_config_page(library_service, app_state):
    """Renderiza a página de configuração do Notion."""
    st.markdown('<div class="main-header">⚙️ Configuração do Notion</div>', unsafe_allow_html=True)
    
    # Carregar configuração atual
    NotionConfigRepository.update_session_state()
    
    # Formulário de configuração
    with st.form("notion_config_form"):
        st.markdown("### Token da API do Notion")
        st.markdown("""
        Para exportar para o Notion, você precisa:
        1. Criar uma integração no [site do Notion](https://www.notion.so/my-integrations)
        2. Obter o token de integração
        3. Compartilhar uma página com sua integração
        """)
        
        token = st.text_input(
            "Token de Integração", 
            value=st.session_state.get("notion_token", ""),
            type="password",
            help="O token secreto da sua integração Notion"
        )
        
        st.markdown("### Destino no Notion")
        option = st.radio(
            "Escolha uma opção:",
            ["Usar uma base de dados existente", "Criar uma nova base de dados"],
            index=0 if st.session_state.get("notion_database_id") else 1
        )
        
        database_id = ""
        page_id = ""
        database_name = "Biblioteca de Ebooks"
        
        if option == "Usar uma base de dados existente":
            database_id = st.text_input(
                "ID da Base de Dados", 
                value=st.session_state.get("notion_database_id", ""),
                help="O ID da base de dados do Notion (ex: 1a2b3c4d5e6f7g8h9i0j)"
            )
            st.info("O ID está na URL após o título da base de dados e antes de '?'")
        else:
            page_id = st.text_input(
                "ID da Página", 
                value=st.session_state.get("notion_page_id", ""),
                help="O ID da página do Notion onde criar a base de dados"
            )
            st.info("O ID está na URL após o título da página e antes de '?'")
            
            database_name = st.text_input(
                "Nome da Base de Dados",
                value=st.session_state.get("notion_database_name", "Biblioteca de Ebooks"),
                help="O nome da nova base de dados a ser criada"
            )
        
        submitted = st.form_submit_button("Salvar Configuração")
        
        if submitted:
            # Salvar na sessão
            st.session_state.notion_token = token
            st.session_state.notion_database_id = database_id
            st.session_state.notion_page_id = page_id
            st.session_state.notion_database_name = database_name
            
            # Salvar no repositório
            config = {
                "token": token,
                "database_id": database_id,
                "page_id": page_id,
                "database_name": database_name,
                "create_database_if_not_exists": option == "Criar uma nova base de dados"
            }
            
            if NotionConfigRepository.save_config(config):
                st.success("Configuração salva com sucesso!")
            else:
                st.error("Erro ao salvar configuração.")