import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pyicloud import PyiCloudService
from core.interfaces.scanner import Scanner
from core.services.credential_service import CredentialService

class ICloudScanner(Scanner):
    """Scanner para fonte iCloud com gerenciamento seguro de credenciais."""
    
    FORMATOS_EBOOK = {
        '.epub': 'EPUB',
        '.pdf': 'PDF',
        '.mobi': 'MOBI',
        '.azw': 'AZW',
        '.azw3': 'AZW3',
        '.kfx': 'KFX',
        '.txt': 'TXT'
    }
    
    def __init__(self, credential_service: CredentialService):
        """
        Inicializa o scanner de iCloud.
        
        Args:
            credential_service: Serviço para gerenciamento de credenciais
        """
        self.credential_service = credential_service
        self.logger = logging.getLogger(__name__)
    
    def scan(self, path: str, config: Optional[Dict[str, Any]] = None, source_id: Optional[str] = None) -> Optional[str]:
        """
        Escaneia ebooks no iCloud.
        
        Args:
            path: Caminho no iCloud
            config: Configuração (pode conter credenciais temporárias)
            source_id: Identificador da fonte para recuperar credenciais armazenadas
            
        Returns:
            Caminho para o arquivo CSV gerado ou None em caso de erro
        """
        self.logger.info(f"Escaneando iCloud: {path}")
        
        # Obter credenciais
        username, password = self._get_credentials(source_id, config)
        
        if not username or not password:
            self.logger.error("Credenciais não disponíveis para iCloud")
            return None
        
        try:
            # Conectar ao iCloud
            api = PyiCloudService(username, password)
            
            # Verificar se precisa de 2FA
            if api.requires_2fa:
                self.logger.error("Autenticação de dois fatores necessária. Não suportado nesta versão.")
                return None
            if api.requires_2sa:
                self.logger.error("Verificação em duas etapas necessária. Não suportado nesta versão.")
                return None
            
            # Escanear pasta
            ebooks = self._scan_pasta(api, path)
            
            # Gerar relatório CSV
            csv_name = f"ebooks_icloud_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            csv_path = os.path.join(os.getcwd(), csv_name)
            
            self._save_csv_report(ebooks, csv_path)
            
            self.logger.info(f"Relatório salvo em {csv_path}: {len(ebooks)} ebooks encontrados")
            return csv_path
            
        except Exception as e:
            self.logger.error(f"Erro ao escanear fonte iCloud: {str(e)}")
            return None
    
    def _get_credentials(self, source_id: Optional[str], config: Optional[Dict[str, Any]]) -> tuple:
        """
        Obtém credenciais do iCloud.
        
        Tenta obter do serviço de credenciais primeiro, depois do config.
        
        Args:
            source_id: ID da fonte
            config: Configuração com possíveis credenciais temporárias
            
        Returns:
            Tupla (username, password)
        """
        username, password = None, None
        
        # Tentar obter do serviço de credenciais
        if source_id:
            username, password = self.credential_service.get_credentials(source_id)
        
        # Tentar obter do config
        if (not username or not password) and config:
            username = config.get("username")
            password = config.get("password")
            
            # Se credenciais foram fornecidas e tem source_id, perguntar se quer salvar
            if username and password and source_id and config.get("save_credentials", False):
                self.credential_service.save_credentials(source_id, username, password)
        
        return username, password
    
    def _is_ebook(self, nome_arquivo: str) -> bool:
        """Verifica se um arquivo é um ebook baseado na extensão."""
        from pathlib import Path
        extensao = Path(nome_arquivo).suffix.lower()
        return extensao in self.FORMATOS_EBOOK
    
    def _get_formato(self, nome_arquivo: str) -> str:
        """Obtém o formato do ebook baseado na extensão."""
        from pathlib import Path
        extensao = Path(nome_arquivo).suffix.lower()
        return self.FORMATOS_EBOOK.get(extensao, 'Desconhecido')
    
    def _scan_pasta(self, api, caminho_pasta: str) -> List[Dict[str, Any]]:
        """
        Escaneia uma pasta no iCloud Drive em busca de ebooks.
        
        Args:
            api: Instância autenticada da API do iCloud
            caminho_pasta: Caminho para a pasta no iCloud Drive
            
        Returns:
            Lista de dicionários com informações dos ebooks
        """
        ebooks = []
        self.logger.info(f"Escaneando pasta iCloud Drive: {caminho_pasta}")
        
        try:
            # Ajuste o caminho para o formato correto
            caminho_pasta_formatado = caminho_pasta.split('/')
            pasta = api.drive
            self.logger.info(f"Conteúdo do iCloud Drive: {pasta.dir()}")
            
            for parte in caminho_pasta_formatado:
                if parte:  # Ignorar partes vazias
                    pasta = pasta[parte]
                    self.logger.info(f"Navegando para: {parte}")
            
            for item_str in pasta.dir():
                item = pasta[item_str]
                if self._is_ebook(item.name):
                    ebook = {
                        'Nome': item.name,
                        'Formato': self._get_formato(item.name),
                        'Tamanho(MB)': round(item.size / (1024 * 1024), 2),
                        'Data Modificação': item.date_modified.strftime('%Y-%m-%d %H:%M:%S'),
                        'Caminho': f"{caminho_pasta}/{item.name}"
                    }
                    ebooks.append(ebook)
                    self.logger.info(f"Ebook encontrado: {item.name}")
        
        except Exception as e:
            self.logger.error(f"Erro ao escanear pasta {caminho_pasta}: {str(e)}")
            raise
        
        return ebooks
    
    def _save_csv_report(self, ebooks: List[Dict[str, Any]], csv_path: str) -> None:
        """
        Salva os dados dos ebooks em um arquivo CSV.
        
        Args:
            ebooks: Lista de dicionários com informações dos ebooks
            csv_path: Caminho para salvar o arquivo CSV
        """
        import pandas as pd
        
        try:
            df = pd.DataFrame(ebooks)
            df.to_csv(csv_path, index=False, encoding='utf-8')
        except Exception as e:
            self.logger.error(f"Erro ao salvar relatório CSV: {str(e)}")
            raise