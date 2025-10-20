# core/repositories/obsidian_config_repository.py
import json
import os
from typing import Dict, Any, Optional


class ObsidianConfigRepository:
    """Repository for managing Obsidian export configuration."""

    CONFIG_FILE = "obsidian_config.json"

    @staticmethod
    def save_config(config: Dict[str, Any]) -> bool:
        """
        Save configuration to file.

        Args:
            config: Configuration dictionary to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(ObsidianConfigRepository.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    @staticmethod
    def load_config() -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Configuration dictionary, or empty dict if file doesn't exist or is invalid
        """
        if not os.path.exists(ObsidianConfigRepository.CONFIG_FILE):
            return {}

        try:
            with open(ObsidianConfigRepository.CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def update_session_state():
        """
        Update Streamlit session state with saved configuration.

        This method is called when loading the configuration page to
        populate form fields with previously saved values.
        """
        import streamlit as st

        config = ObsidianConfigRepository.load_config()

        st.session_state.obsidian_vault_path = config.get("vault_path", "")
        st.session_state.obsidian_notes_folder = config.get("notes_folder", "Books")
        st.session_state.obsidian_template_path = config.get("template_path", "")
        st.session_state.obsidian_filename_pattern = config.get("filename_pattern", "{title} - {author}")
        st.session_state.obsidian_default_status = config.get("default_status", "unread")
        st.session_state.obsidian_default_priority = config.get("default_priority", "medium")
        st.session_state.obsidian_default_device = config.get("default_device", "computer")
        st.session_state.obsidian_default_purpose = config.get("default_purpose", ["read", "reference"])
        st.session_state.obsidian_overwrite_existing = config.get("overwrite_existing", False)
        st.session_state.obsidian_use_mcp_tools = config.get("use_mcp_tools", True)

    @staticmethod
    def save_from_session_state() -> bool:
        """
        Save configuration from Streamlit session state to file.

        Returns:
            True if successful, False otherwise
        """
        import streamlit as st

        config = {
            "vault_path": st.session_state.get("obsidian_vault_path", ""),
            "notes_folder": st.session_state.get("obsidian_notes_folder", "Books"),
            "template_path": st.session_state.get("obsidian_template_path", ""),
            "filename_pattern": st.session_state.get("obsidian_filename_pattern", "{title} - {author}"),
            "default_status": st.session_state.get("obsidian_default_status", "unread"),
            "default_priority": st.session_state.get("obsidian_default_priority", "medium"),
            "default_device": st.session_state.get("obsidian_default_device", "computer"),
            "default_purpose": st.session_state.get("obsidian_default_purpose", ["read", "reference"]),
            "overwrite_existing": st.session_state.get("obsidian_overwrite_existing", False),
            "use_mcp_tools": st.session_state.get("obsidian_use_mcp_tools", True)
        }

        return ObsidianConfigRepository.save_config(config)
