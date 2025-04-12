# ui/components/notion_export_component.py
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, Callable

from adapters.notion.factory import NotionExporterFactory

def render_notion_setup_form(on_submit: Callable[[Dict[str, Any]], None]):
    """
    Renders the Notion setup form.
    
    Args:
        on_submit: Callback function when form is submitted
    """
    st.markdown("## Configure Notion Integration")
    
    with st.form("notion_setup_form"):
        st.markdown("### Notion API Token")
        st.markdown("""
        To export to Notion, you need to:
        1. Create an integration at [Notion Integrations](https://www.notion.so/my-integrations)
        2. Copy the integration token
        3. Share a page/database with your integration
        """)
        
        token = st.text_input(
            "Notion API Token", 
            value=st.session_state.get("notion_token", ""),
            type="password",
            help="Your Notion integration token"
        )
        
        st.markdown("### Export Destination")
        destination_type = st.radio(
            "Select destination type:",
            ["Use existing database", "Create new database"],
            index=0 if st.session_state.get("notion_database_id") else 1,
            help="Choose whether to use an existing database or create a new one"
        )
        
        database_id = ""
        page_id = ""
        database_name = "Biblioteca de Ebooks"
        
        if destination_type == "Use existing database":
            database_id = st.text_input(
                "Database ID",
                value=st.session_state.get("notion_database_id", ""),
                help="ID of your Notion database (found in the URL)"
            )
            st.markdown("📌 **Tip:** The database ID is the long string in the URL after the database name.")
        else:
            page_id = st.text_input(
                "Page ID",
                value=st.session_state.get("notion_page_id", ""),
                help="ID of the Notion page where to create the database"
            )
            st.markdown("📌 **Tip:** The page ID is the long string in the URL after the page name.")
            
            database_name = st.text_input(
                "Database Name",
                value="Biblioteca de Ebooks",
                help="Name for the new database"
            )
        
        test_connection = st.checkbox("Test connection before saving", value=True)
        
        submitted = st.form_submit_button("Save Configuration")
        
        if submitted:
            config = {
                "token": token,
                "database_id": database_id,
                "page_id": page_id,
                "database_name": database_name,
                "create_database_if_not_exists": destination_type == "Create new database"
            }
            
            # Store config in session state
            st.session_state.notion_token = token
            st.session_state.notion_database_id = database_id
            st.session_state.notion_page_id = page_id
            st.session_state.notion_database_name = database_name
            
            # Call the on_submit callback
            on_submit(config)

def render_notion_export_section(csv_path: str, library_service, on_success: Optional[Callable] = None):
    """
    Renders the Notion export section.
    
    Args:
        csv_path: Path to the CSV file to export
        library_service: Library service
        on_success: Callback function when export is successful
    """
    from core.repositories.notion_config_repository import NotionConfigRepository
    
    # Carregar configuração do arquivo para a sessão
    NotionConfigRepository.update_session_state()
    
    st.markdown("## Exportar para o Notion")
    
    # Verificar se já tem configuração
    config = {
        "token": st.session_state.get('notion_token', ''),
        "database_id": st.session_state.get('notion_database_id', ''),
        "page_id": st.session_state.get('notion_page_id', ''),
        "database_name": st.session_state.get('notion_database_name', 'Biblioteca de Ebooks')
    }
    
    configured = config["token"] and (config["database_id"] or config["page_id"])
    
    if not configured:
        st.warning("Você precisa configurar a integração com o Notion primeiro.")
        setup_config = render_notion_setup(on_save=NotionConfigRepository.save_config)
        if setup_config:
            config.update(setup_config)
            configured = True
    
    if configured:
        # Show configuration summary
        with st.expander("Current Configuration", expanded=False):
            token = st.session_state.get("notion_token", "")
            masked_token = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "****"
        
            st.markdown("### Notion Integration Settings")
            st.markdown(f"**API Token:** {masked_token}")
        
            if st.session_state.get("notion_database_id"):
                st.markdown(f"**Database ID:** {st.session_state.get('notion_database_id')}")
        
            if st.session_state.get("notion_page_id"):
                st.markdown(f"**Page ID:** {st.session_state.get('notion_page_id')}")
            
            if st.button("Reconfigure"):
                st.session_state.pop("notion_token", None)
                st.session_state.pop("notion_database_id", None)
                st.session_state.pop("notion_page_id", None)
                st.rerun()
    
        # Show data preview
        st.markdown("### Data Preview")
        try:
            df = pd.read_csv(csv_path)
            preview_rows = min(5, len(df))
        
            st.markdown(f"**Total records:** {len(df)}")
            st.markdown(f"**Preview of first {preview_rows} records:**")
            st.dataframe(df.head(preview_rows), use_container_width=True)
        
            # Columns mapping information
            st.markdown("### Column Mapping")
            st.markdown("""
            The following mapping will be used when exporting to Notion:
        
            | Notion Property | CSV Columns (in priority order) |
            | --------------- | ------------------------------- |
            | Title | GB_Titulo, Titulo_Extraido, Nome |
            | Author | GB_Autores, Autor_Extraido |
            | Format | Formato |
            | Size (MB) | Tamanho(MB) |
            | Modified Date | Data Modificação |
            | Path | Caminho |
            | Publisher | GB_Editora |
            | Publication Date | GB_Data_Publicacao |
            | ISBN | GB_ISBN13, GB_ISBN10 |
            | Topics | Temas_Sugeridos, GB_Categorias |
            """)
        
            # Export button
            if st.button("Export to Notion", type="primary"):
                with st.spinner("Exporting to Notion..."):
                    # Prepare configuration
                    config = {
                        "token": st.session_state.get("notion_token", ""),
                        "database_id": st.session_state.get("notion_database_id", ""),
                        "page_id": st.session_state.get("notion_page_id", ""),
                        "database_name": st.session_state.get("notion_database_name", "Biblioteca de Ebooks"),
                        "create_database_if_not_exists": bool(st.session_state.get("notion_page_id", ""))
                    }
                
                    # Create exporter via factory and export
                    exporter = NotionExporterFactory.create_exporter(config)
                    success = exporter.export(csv_path, config)
                
                    if success:
                        st.success("Export to Notion completed successfully!")
                        if on_success:
                            on_success()
                    else:
                        st.error("Failed to export to Notion. Please check the logs for details.")
                    
                        st.info("""
                        **Troubleshooting tips:**
                        1. Make sure your integration token is correct
                        2. Verify that you've shared your page/database with the integration
                        3. Check that the database has the correct structure
                        4. Check the application logs for more detailed error messages
                        """)
    
        except Exception as e:
            st.error(f"Error loading CSV file: {str(e)}")

def integrate_with_view_page(csv_path: str, library_service):
    """
    Helper function to integrate the Notion export component with the view page.
    
    Args:
        csv_path: Path to the CSV file
        library_service: Library service
    """
    with st.expander("Export to Notion", expanded=False):
        render_notion_export_section(csv_path, library_service)