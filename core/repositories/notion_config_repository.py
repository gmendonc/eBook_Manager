# core/repositories/notion_config_repository.py
import json
import os
from typing import Dict, Any, Optional

class NotionConfigRepository:
    """Repositório para gerenciar a configuração da integração com o Notion."""
    
    CONFIG_FILE = "notion_config.json"
    
    @staticmethod
    def save_config(config: Dict[str, Any]) -> bool:
        """Salva a configuração em um arquivo."""
        try:
            with open(NotionConfigRepository.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Carrega a configuração do arquivo."""
        if not os.path.exists(NotionConfigRepository.CONFIG_FILE):
            return {}
            
        try:
            with open(NotionConfigRepository.CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    @staticmethod
    def update_session_state():
        """Atualiza o estado da sessão com a configuração salva."""
        import streamlit as st
        
        config = NotionConfigRepository.load_config()
        
        st.session_state.notion_token = config.get("token", "")
        st.session_state.notion_database_id = config.get("database_id", "")
        st.session_state.notion_page_id = config.get("page_id", "")
        st.session_state.notion_database_name = config.get("database_name", "Biblioteca de Ebooks")
        
    @staticmethod
    def save_from_session_state() -> bool:
        """Salva a configuração a partir do estado da sessão."""
        import streamlit as st
        
        config = {
            "token": st.session_state.get("notion_token", ""),
            "database_id": st.session_state.get("notion_database_id", ""),
            "page_id": st.session_state.get("notion_page_id", ""),
            "database_name": st.session_state.get("notion_database_name", "Biblioteca de Ebooks")
        }
        
        return NotionConfigRepository.save_config(config)