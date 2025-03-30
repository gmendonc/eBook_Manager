class AppState:
    """Gerencia o estado da aplicação."""
    
    def __init__(self):
        """Inicializa o estado da aplicação."""
        self.current_page = "home"
        self.scan_results = {}
        self.last_processed_file = None
    
    def change_page(self, page: str):
        """
        Muda a página atual.
        
        Args:
            page: Nome da página
        """
        self.current_page = page
    
    def add_scan_result(self, source_name: str, success: bool, message: str, path: str = None):
        """
        Adiciona um resultado de escaneamento.
        
        Args:
            source_name: Nome da fonte
            success: Se o escaneamento foi bem-sucedido
            message: Mensagem de resultado
            path: Caminho para o arquivo gerado (opcional)
        """
        self.scan_results[source_name] = {
            "status": "success" if success else "error",
            "message": message,
            "path": path
        }
    
    def set_last_processed_file(self, file_path: str):
        """
        Define o último arquivo processado.
        
        Args:
            file_path: Caminho para o arquivo
        """
        self.last_processed_file = file_path