# ui/components/obsidian_export_component.py
import streamlit as st
from pathlib import Path
import logging

from core.domain.obsidian_export_config import ObsidianExportConfig
from core.repositories.obsidian_config_repository import ObsidianConfigRepository
from core.services.obsidian_export_service import ObsidianExportService
from adapters.obsidian.filesystem_file_manager import FilesystemFileManager
from adapters.obsidian.mcp_file_manager import McpFileManager
from adapters.obsidian.template_engine import MarkdownTemplateEngine
from adapters.obsidian.record_mapper import GoogleBooksObsidianRecordMapper
from core.exceptions import ObsidianExportError, ObsidianConfigError, ObsidianFileError


logger = logging.getLogger(__name__)


def render_obsidian_export_button(csv_path: str, app_state):
    """
    Render Obsidian export button and handle export workflow.

    Args:
        csv_path: Path to the CSV file to export
        app_state: Application state object
    """
    st.markdown("### 🔮 Exportar para Obsidian")

    # Check if configuration exists
    config = ObsidianConfigRepository.load_config()

    if not config.get("vault_path"):
        st.warning("⚠️ Configure o Obsidian primeiro na página de configuração.")
        if st.button("Ir para Configuração"):
            app_state.current_page = "obsidian_config"
            st.rerun()
        return

    # Show current configuration summary
    with st.expander("📋 Configuração Atual", expanded=False):
        st.markdown(f"""
        - **Vault:** `{config.get('vault_path', 'N/A')}`
        - **Pasta:** `{config.get('notes_folder', 'Books')}`
        - **Template:** {'Customizado' if config.get('template_path') else 'Padrão'}
        - **Padrão de nome:** `{config.get('filename_pattern', '{title} - {author}')}`
        - **Sobrescrever:** {'Sim' if config.get('overwrite_existing') else 'Não'}
        """)

    # Export button
    if st.button("🚀 Exportar para Obsidian", use_container_width=True, type="primary"):
        try:
            # Validate configuration
            _validate_config(config)

            # Create export configuration
            export_config = _create_export_config(config)

            # Perform export with progress
            _perform_export(csv_path, export_config)

        except ObsidianConfigError as e:
            st.error(f"❌ Erro de configuração: {str(e)}")
            logger.error(f"Configuration error: {str(e)}")

        except ObsidianFileError as e:
            st.error(f"❌ Erro de arquivo: {str(e)}")
            logger.error(f"File error: {str(e)}")

        except ObsidianExportError as e:
            st.error(f"❌ Erro na exportação: {str(e)}")
            logger.error(f"Export error: {str(e)}")

        except Exception as e:
            st.error(f"❌ Erro inesperado: {str(e)}")
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)


def _validate_config(config: dict):
    """
    Validate export configuration.

    Args:
        config: Configuration dictionary

    Raises:
        ObsidianConfigError: If configuration is invalid
    """
    if not config.get("vault_path"):
        raise ObsidianConfigError("Caminho do vault não configurado")

    if not config.get("notes_folder"):
        raise ObsidianConfigError("Pasta de notas não configurada")

    if not config.get("filename_pattern"):
        raise ObsidianConfigError("Padrão de nome de arquivo não configurado")

    # Check if vault path exists
    vault_path = Path(config["vault_path"])
    if not vault_path.exists():
        # Offer to create it
        st.warning(f"⚠️ Vault não encontrado: {config['vault_path']}")
        if st.button("Criar pasta do vault"):
            try:
                vault_path.mkdir(parents=True, exist_ok=True)
                st.success(f"✅ Vault criado: {config['vault_path']}")
            except Exception as e:
                raise ObsidianConfigError(f"Falha ao criar vault: {str(e)}")
        else:
            raise ObsidianConfigError("Vault não existe e não foi criado")


def _create_export_config(config: dict) -> ObsidianExportConfig:
    """
    Create ObsidianExportConfig from config dictionary.

    Args:
        config: Configuration dictionary

    Returns:
        ObsidianExportConfig instance
    """
    return ObsidianExportConfig(
        vault_path=config["vault_path"],
        notes_folder=config.get("notes_folder", "Books"),
        template_path=config.get("template_path") or None,
        filename_pattern=config.get("filename_pattern", "{title} - {author}"),
        default_status=config.get("default_status", "unread"),
        default_priority=config.get("default_priority", "medium"),
        default_device=config.get("default_device", "computer"),
        default_purpose=config.get("default_purpose", ["read", "reference"]),
        overwrite_existing=config.get("overwrite_existing", False),
        use_mcp_tools=config.get("use_mcp_tools", True)
    )


def _perform_export(csv_path: str, config: ObsidianExportConfig):
    """
    Perform the export with progress tracking.

    Args:
        csv_path: Path to CSV file
        config: Export configuration
    """
    # Progress tracking state
    progress_placeholder = st.empty()
    status_placeholder = st.empty()

    # Create progress callback
    def update_progress(current: int, total: int):
        progress = current / total if total > 0 else 0
        progress_placeholder.progress(progress, text=f"Processando {current}/{total} livros...")

    try:
        logger.info("="*60)
        logger.info("OBSIDIAN EXPORT STARTED")
        logger.info(f"CSV: {csv_path}")
        logger.info(f"Vault: {config.vault_path}")
        logger.info(f"Folder: {config.notes_folder}")
        logger.info(f"Template: {'Custom' if config.template_path else 'Default'}")
        logger.info(f"Pattern: {config.filename_pattern}")
        logger.info("="*60)

        # Create file manager (MCP with filesystem fallback)
        if config.use_mcp_tools:
            status_placeholder.info("🔧 Inicializando file manager (MCP com fallback)...")
            logger.info("Using McpFileManager (with filesystem fallback)")
            file_manager = McpFileManager(config.vault_path)
        else:
            status_placeholder.info("🔧 Inicializando file manager (filesystem direto)...")
            logger.info("Using FilesystemFileManager (direct)")
            file_manager = FilesystemFileManager(config.vault_path)

        # Create other components
        template_engine = MarkdownTemplateEngine()
        record_mapper = GoogleBooksObsidianRecordMapper()

        # Create export service
        export_service = ObsidianExportService(
            config=config,
            file_manager=file_manager,
            template_engine=template_engine,
            record_mapper=record_mapper,
            progress_callback=update_progress
        )

        # Perform export
        status_placeholder.info("📤 Exportando...")
        logger.info("Starting export process...")

        success, success_count, skipped_count, error_count, error_messages = \
            export_service.export_csv_to_obsidian(csv_path)

        logger.info("="*60)
        logger.info("OBSIDIAN EXPORT COMPLETED")
        logger.info(f"Success: {success_count}")
        logger.info(f"Skipped: {skipped_count}")
        logger.info(f"Errors: {error_count}")
        logger.info("="*60)

        # Clear progress
        progress_placeholder.empty()
        status_placeholder.empty()

        # Show results
        _show_export_results(success, success_count, skipped_count, error_count, error_messages)

    except Exception as e:
        progress_placeholder.empty()
        status_placeholder.empty()
        raise


def _show_export_results(
    success: bool,
    success_count: int,
    skipped_count: int,
    error_count: int,
    error_messages: list
):
    """
    Display export results summary.

    Args:
        success: Overall success status
        success_count: Number of successful exports
        skipped_count: Number of skipped records
        error_count: Number of errors
        error_messages: List of error messages
    """
    st.markdown("---")

    if success and error_count == 0:
        st.success("✅ Exportação concluída com sucesso!")
    elif success and error_count > 0:
        st.warning("⚠️ Exportação concluída com alguns erros")
    else:
        st.error("❌ Exportação falhou")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    total = success_count + skipped_count + error_count

    with col1:
        st.metric("Total", total)

    with col2:
        st.metric("✅ Sucesso", success_count)

    with col3:
        st.metric("⊘ Pulados", skipped_count, help="Notas que já existem (sobrescrever desativado)")

    with col4:
        st.metric("✗ Erros", error_count)

    # Show errors if any
    if error_messages:
        with st.expander(f"❌ Ver Erros ({len(error_messages)})", expanded=error_count > 0):
            for i, error_msg in enumerate(error_messages, 1):
                st.text(f"{i}. {error_msg}")

    # Success message with vault info
    if success_count > 0:
        st.info(f"📝 {success_count} notas criadas em: `{st.session_state.get('obsidian_vault_path')}/{st.session_state.get('obsidian_notes_folder')}`")
