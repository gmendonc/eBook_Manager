import keyring
import logging
from typing import Tuple, Optional

class CredentialService:
    """Serviço para gerenciamento seguro de credenciais."""
    
    def __init__(self, service_prefix: str = "ebook_manager"):
        """
        Inicializa o serviço de credenciais.
        
        Args:
            service_prefix: Prefixo para identificar serviços no keyring
        """
        self.service_prefix = service_prefix
        self.logger = logging.getLogger(__name__)
    
    def save_credentials(self, source_id: str, username: str, password: str) -> bool:
        """
        Salva credenciais de forma segura usando o keyring do sistema.
        
        Args:
            source_id: Identificador da fonte
            username: Nome de usuário/email
            password: Senha
            
        Returns:
            True se as credenciais foram salvas com sucesso
        """
        try:
            service_name = f"{self.service_prefix}_{source_id}"
            keyring.set_password(service_name, "username", username)
            keyring.set_password(service_name, username, password)
            self.logger.info(f"Credenciais para {source_id} salvas com segurança")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar credenciais: {str(e)}")
            return False
    
    def get_credentials(self, source_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Recupera credenciais armazenadas.
        
        Args:
            source_id: Identificador da fonte
            
        Returns:
            Tupla (username, password) ou (None, None) se não encontradas
        """
        try:
            service_name = f"{self.service_prefix}_{source_id}"
            username = keyring.get_password(service_name, "username")
            if username:
                password = keyring.get_password(service_name, username)
                return username, password
        except Exception as e:
            self.logger.error(f"Erro ao recuperar credenciais: {str(e)}")
        return None, None
    
    def delete_credentials(self, source_id: str) -> bool:
        """
        Remove credenciais armazenadas.
        
        Args:
            source_id: Identificador da fonte
            
        Returns:
            True se as credenciais foram removidas com sucesso
        """
        try:
            service_name = f"{self.service_prefix}_{source_id}"
            username = keyring.get_password(service_name, "username")
            if username:
                keyring.delete_password(service_name, "username")
                keyring.delete_password(service_name, username)
                self.logger.info(f"Credenciais para {source_id} removidas")
                return True
        except Exception as e:
            self.logger.error(f"Erro ao excluir credenciais: {str(e)}")
        return False
    
    def has_credentials(self, source_id: str) -> bool:
        """
        Verifica se existem credenciais armazenadas.
        
        Args:
            source_id: Identificador da fonte
            
        Returns:
            True se as credenciais existirem
        """
        username, password = self.get_credentials(source_id)
        return username is not None and password is not None