import keyring
import logging

class SecureCredentialManager:
    """Gerenciador de armazenamento seguro de credenciais."""
    
    def __init__(self):
        self.keyring_service = "ebook_manager"
        self.logger = logging.getLogger(__name__)
    
    def save_credentials(self, source_name, username, password):
        """
        Salva credenciais de forma segura usando o keyring.
        
        Args:
            source_name: Nome da fonte para identificar as credenciais
            username: Nome de usuário/email
            password: Senha
            
        Returns:
            bool: True se as credenciais foram salvas com sucesso
        """
        try:
            keyring.set_password(f"{self.keyring_service}_{source_name}", "username", username)
            keyring.set_password(f"{self.keyring_service}_{source_name}", username, password)
            self.logger.info(f"Credenciais para {source_name} salvas com segurança")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar credenciais: {str(e)}")
            return False
    
    def get_credentials(self, source_name):
        """
        Recupera credenciais armazenadas.
        
        Args:
            source_name: Nome da fonte
            
        Returns:
            tuple: (username, password) ou (None, None) se não encontradas
        """
        try:
            username = keyring.get_password(f"{self.keyring_service}_{source_name}", "username")
            if username:
                password = keyring.get_password(f"{self.keyring_service}_{source_name}", username)
                return username, password
        except Exception as e:
            self.logger.error(f"Erro ao recuperar credenciais: {str(e)}")
        return None, None
    
    def delete_credentials(self, source_name):
        """
        Remove credenciais armazenadas.
        
        Args:
            source_name: Nome da fonte
            
        Returns:
            bool: True se as credenciais foram removidas com sucesso
        """
        try:
            username = keyring.get_password(f"{self.keyring_service}_{source_name}", "username")
            if username:
                keyring.delete_password(f"{self.keyring_service}_{source_name}", "username")
                keyring.delete_password(f"{self.keyring_service}_{source_name}", username)
                self.logger.info(f"Credenciais para {source_name} removidas")
                return True
        except Exception as e:
            self.logger.error(f"Erro ao excluir credenciais: {str(e)}")
        return False
    
    def has_credentials(self, source_name):
        """
        Verifica se existem credenciais armazenadas.
        
        Args:
            source_name: Nome da fonte
            
        Returns:
            bool: True se as credenciais existirem
        """
        username, password = self.get_credentials(source_name)
        return username is not None and password is not None