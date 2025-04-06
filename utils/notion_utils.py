import os
import json
import requests
from typing import Dict, Any, List, Optional
import streamlit as st

def load_notion_config() -> Dict[str, Any]:
    """
    Carrega as configurações do Notion do arquivo de configuração.
    
    Returns:
        Dicionário com as configurações ou um dicionário vazio se não existir
    """
    config_path = "notion_config.json"
    
    if not os.path.exists(config_path):
        return {}
        
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        # Using logger instead of st.error since this might be called in contexts without streamlit
        import logging
        logging.error(f"Erro ao carregar configurações do Notion: {str(e)}")
        return {}

def save_notion_config(config: Dict[str, Any]) -> bool:
    """
    Salva as configurações do Notion no arquivo de configuração.
    
    Args:
        config: Dicionário com as configurações
        
    Returns:
        True se as configurações foram salvas com sucesso, False caso contrário
    """
    config_path = "notion_config.json"
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        import logging
        logging.error(f"Erro ao salvar configurações do Notion: {str(e)}")
        return False

def test_notion_connection(config: Dict[str, Any]) -> bool:
    """
    Testa a conexão com o Notion.
    
    Args:
        config: Configurações do Notion
        
    Returns:
        True se a conexão for bem-sucedida, False caso contrário
    """
    try:
        # Criar o exportador para teste
        token = config.get("token", "")
        if not token:
            return False
            
        # Tentar fazer uma requisição simples para a API do Notion
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        response = requests.get(
            "https://api.notion.com/v1/users/me",
            headers=headers
        )
        
        return response.status_code == 200
    except Exception:
        return False

def load_export_history() -> List[Dict[str, Any]]:
    """
    Carrega o histórico de exportações.
    
    Returns:
        Lista com o histórico de exportações
    """
    history_path = "notion_export_history.json"
    
    if not os.path.exists(history_path):
        return []
        
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def add_export_to_history(file: str, items: int, success: bool, error: Optional[str] = None) -> None:
    """
    Adiciona uma exportação ao histórico.
    
    Args:
        file: Nome do arquivo exportado
        items: Número de itens exportados
        success: Se a exportação foi bem-sucedida
        error: Mensagem de erro, se houver
    """
    history_path = "notion_export_history.json"
    
    # Carregar histórico existente
    history = load_export_history()
    
    # Adicionar nova entrada
    from datetime import datetime
    new_entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file": file,
        "items": items,
        "success": success
    }
    
    if error:
        new_entry["error"] = error
        
    # Adicionar ao início da lista
    history.insert(0, new_entry)
    
    # Limitar o tamanho da lista para não crescer indefinidamente
    if len(history) > 20:
        history = history[:20]
    
    # Salvar histórico atualizado
    try:
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def configure_notion_exporter(library_service, config: Dict[str, Any]) -> None:
    """
    Configura o exportador do Notion no serviço da biblioteca.
    
    Args:
        library_service: Serviço da biblioteca
        config: Configurações do Notion
    """
    # Importar aqui para evitar importação circular
    from adapters.notion_adapter import NotionExporter
    
    # Criar o exportador com as configurações
    notion_exporter = NotionExporter(
        token=config.get("token", ""),
        database_id=config.get("database_id", "")
    )
    
    # Configurar o exportador no serviço de exportação
    library_service.export_service.set_exporter(notion_exporter)
    
    # Adicionar as configurações adicionais
    library_service.export_service.exporter_config = config