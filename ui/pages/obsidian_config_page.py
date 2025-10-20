# ui/pages/obsidian_config_page.py
import streamlit as st
from pathlib import Path
from core.repositories.obsidian_config_repository import ObsidianConfigRepository


def render_obsidian_config_page(library_service, app_state):
    """Render the Obsidian configuration page."""
    st.markdown('<div class="main-header">⚙️ Configuração do Obsidian</div>', unsafe_allow_html=True)

    # Load existing configuration
    ObsidianConfigRepository.update_session_state()

    st.markdown("""
    Configure a integração com o Obsidian para exportar sua biblioteca de ebooks como notas em Markdown.
    """)

    # Configuration form
    with st.form("obsidian_config_form"):
        st.markdown("### 📁 Vault do Obsidian")

        vault_path = st.text_input(
            "Caminho do Vault",
            value=st.session_state.get("obsidian_vault_path", ""),
            help="Caminho completo para o diretório do vault do Obsidian",
            placeholder="C:\\Users\\SeuNome\\Documents\\ObsidianVault"
        )

        # Validate vault path
        if vault_path:
            vault_path_obj = Path(vault_path)
            if vault_path_obj.exists() and vault_path_obj.is_dir():
                st.success(f"✓ Vault encontrado: {vault_path}")
            else:
                st.warning("⚠️ Caminho não encontrado. A pasta será criada se necessário.")

        notes_folder = st.text_input(
            "Pasta de Notas",
            value=st.session_state.get("obsidian_notes_folder", "Books"),
            help="Pasta dentro do vault onde as notas serão criadas"
        )

        st.markdown("### 📝 Template")

        template_option = st.radio(
            "Opção de Template",
            ["Usar template padrão", "Usar template customizado"],
            help="Template padrão inclui todos os metadados do Google Books"
        )

        template_path = ""
        if template_option == "Usar template customizado":
            template_path = st.text_input(
                "Caminho do Template",
                value=st.session_state.get("obsidian_template_path", ""),
                help="Caminho para arquivo .md com template customizado",
                placeholder="C:\\caminho\\para\\seu_template.md"
            )

            if template_path and not Path(template_path).exists():
                st.warning("⚠️ Arquivo de template não encontrado")

            st.info("""
            **Placeholders disponíveis:**
            - `{{title}}`, `{{author}}`, `{{publisher}}`
            - `{{publishDate}}`, `{{totalPage}}`, `{{isbn10}}`, `{{isbn13}}`
            - `{{coverUrl}}`, `{{description}}`, `{{categories}}`, `{{language}}`
            - `{{format}}`, `{{file_size}}`, `{{file_path}}`
            - `{{status}}`, `{{priority}}`, `{{device}}`, `{{purpose}}`
            - `{{created}}`, `{{updated}}`
            """)

        st.markdown("### 📄 Nomeação de Arquivos")

        filename_pattern = st.text_input(
            "Padrão do Nome do Arquivo",
            value=st.session_state.get("obsidian_filename_pattern", "{title} - {author}"),
            help="Padrão para gerar nomes de arquivo. Placeholders: {title}, {author}, {publisher}, {isbn}, {format}"
        )

        # Show filename preview
        if filename_pattern:
            sample_title = "Clean Code: A Handbook of Agile Software Craftsmanship"
            sample_author = "Robert C. Martin"
            sample_format = "pdf"

            preview = filename_pattern.replace("{title}", sample_title)
            preview = preview.replace("{author}", sample_author)
            preview = preview.replace("{format}", sample_format)
            preview = preview.replace("{publisher}", "Prentice Hall")
            preview = preview.replace("{isbn}", "9780132350884")

            # Sanitize preview
            import re
            preview = re.sub(r'[:<>/\\|*?""]', '', preview)
            preview = re.sub(r'\s+', ' ', preview).strip()
            if not preview.endswith('.md'):
                preview += '.md'

            if len(preview) > 50:
                preview = preview[:50] + "... (truncado)"

            st.caption(f"**Prévia:** `{preview}`")

        st.markdown("### 🎯 Valores Padrão")

        col1, col2 = st.columns(2)

        with col1:
            default_status = st.selectbox(
                "Status Padrão",
                ["unread", "reading", "next", "want to", "maybe", "paused", "finished"],
                index=0 if st.session_state.get("obsidian_default_status") == "unread" else 0,
                help="Status padrão para notas criadas"
            )

            default_priority = st.selectbox(
                "Prioridade Padrão",
                ["low", "medium", "high", "top", "archive", "eval"],
                index=1 if st.session_state.get("obsidian_default_priority") == "medium" else 1,
                help="Nível de prioridade padrão"
            )

        with col2:
            default_device = st.selectbox(
                "Dispositivo Padrão",
                ["computer", "kindle", "ipad"],
                index=0 if st.session_state.get("obsidian_default_device") == "computer" else 0,
                help="Dispositivo de leitura padrão"
            )

            default_purpose = st.multiselect(
                "Propósito Padrão",
                ["read", "reference", "study", "work"],
                default=st.session_state.get("obsidian_default_purpose", ["read", "reference"]),
                help="Tags de propósito padrão"
            )

        st.markdown("### ⚙️ Opções Avançadas")

        col3, col4 = st.columns(2)

        with col3:
            overwrite_existing = st.checkbox(
                "Sobrescrever notas existentes",
                value=st.session_state.get("obsidian_overwrite_existing", False),
                help="Se marcado, notas existentes serão atualizadas. Caso contrário, serão puladas."
            )

        with col4:
            use_mcp_tools = st.checkbox(
                "Usar ferramentas MCP (se disponíveis)",
                value=st.session_state.get("obsidian_use_mcp_tools", True),
                help="Tenta usar Obsidian MCP tools, com fallback para filesystem direto"
            )

        # Submit button
        submitted = st.form_submit_button("💾 Salvar Configuração", use_container_width=True)

        if submitted:
            # Validate required fields
            if not vault_path:
                st.error("❌ Caminho do vault é obrigatório!")
            elif not notes_folder:
                st.error("❌ Pasta de notas é obrigatória!")
            elif not filename_pattern:
                st.error("❌ Padrão de nome de arquivo é obrigatório!")
            else:
                # Save to session state
                st.session_state.obsidian_vault_path = vault_path
                st.session_state.obsidian_notes_folder = notes_folder
                st.session_state.obsidian_template_path = template_path if template_option == "Usar template customizado" else ""
                st.session_state.obsidian_filename_pattern = filename_pattern
                st.session_state.obsidian_default_status = default_status
                st.session_state.obsidian_default_priority = default_priority
                st.session_state.obsidian_default_device = default_device
                st.session_state.obsidian_default_purpose = default_purpose if default_purpose else ["read", "reference"]
                st.session_state.obsidian_overwrite_existing = overwrite_existing
                st.session_state.obsidian_use_mcp_tools = use_mcp_tools

                # Save to repository
                if ObsidianConfigRepository.save_from_session_state():
                    st.success("✅ Configuração salva com sucesso!")
                else:
                    st.error("❌ Erro ao salvar configuração. Verifique as permissões do arquivo.")

    # Show current configuration summary
    if st.session_state.get("obsidian_vault_path"):
        st.markdown("---")
        st.markdown("### 📋 Configuração Atual")

        config_summary = f"""
        - **Vault:** `{st.session_state.get('obsidian_vault_path', 'Não configurado')}`
        - **Pasta de notas:** `{st.session_state.get('obsidian_notes_folder', 'Books')}`
        - **Template:** {'Padrão' if not st.session_state.get('obsidian_template_path') else 'Customizado'}
        - **Padrão de nome:** `{st.session_state.get('obsidian_filename_pattern', '{title} - {author}')}`
        - **Sobrescrever existentes:** {'Sim' if st.session_state.get('obsidian_overwrite_existing') else 'Não'}
        """

        st.markdown(config_summary)
