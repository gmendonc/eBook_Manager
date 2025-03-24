import os
import pandas as pd
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import json

try:
    from pyicloud import PyiCloudService
    ICLOUD_AVAILABLE = True
except ImportError:
    ICLOUD_AVAILABLE = False

try:
    import dropbox
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False

# Configuração de logging
logger = logging.getLogger(__name__)

@dataclass
class EbookFile:
    """Classe para armazenar informações de um arquivo de ebook."""
    nome: str
    formato: str
    tamanho: int
    data_modificacao: datetime
    caminho: str

class ICloudAuthManager:
    """Gerenciador de autenticação segura para iCloud."""
    
    def __init__(self):
        self.keyring_service = "icloud_ebook_scanner"
    
    def get_credentials_from_env(self):
        """Obtém credenciais das variáveis de ambiente."""
        return os.getenv('ICLOUD_USERNAME'), os.getenv('ICLOUD_PASSWORD')
    
    def get_credentials_from_keyring(self):
        """Obtém credenciais do keyring do sistema."""
        try:
            import keyring
            username = keyring.get_password(self.keyring_service, 'username')
            if username:
                password = keyring.get_password(self.keyring_service, username)
                return username, password
        except ImportError:
            logger.warning("Módulo keyring não disponível")
        return None, None
    
    def save_credentials_to_keyring(self, username: str, password: str):
        """Salva credenciais no keyring do sistema."""
        try:
            import keyring
            keyring.set_password(self.keyring_service, 'username', username)
            keyring.set_password(self.keyring_service, username, password)
            return True
        except ImportError:
            logger.warning("Módulo keyring não disponível")
            return False
    
    def handle_2fa(self, api: PyiCloudService):
        """Gerencia o processo de autenticação de dois fatores."""
        if api.requires_2fa:
            logger.info("Autenticação de dois fatores necessária.")
            code = input("Digite o código recebido no seu dispositivo Apple: ")
            result = api.validate_2fa_code(code)
            logger.info("Código 2FA validado." if result else "Falha na validação do código 2FA.")
            return result
            
        elif api.requires_2sa:
            logger.info("Verificação em duas etapas necessária.")
            devices = api.trusted_devices
            logger.info("Dispositivos confiáveis:")
            for i, device in enumerate(devices):
                logger.info(f"{i}: {device.get('deviceName', 'Desconhecido')}")
                
            device_index = int(input("Escolha um dispositivo pelo número: "))
            device = devices[device_index]
            api.send_verification_code(device)
            code = input("Digite o código de verificação: ")
            result = api.validate_verification_code(device, code)
            logger.info("Código validado." if result else "Falha na validação do código.")
            return result
            
        return True

class ICloudEbookScanner:
    """Classe para escanear e gerenciar ebooks no iCloud."""
    
    FORMATOS_EBOOK = {
        '.epub': 'EPUB',
        '.pdf': 'PDF',
        '.mobi': 'MOBI',
        '.azw': 'AZW',
        '.azw3': 'AZW3',
        '.kfx': 'KFX',
        '.txt': 'TXT',
        '.djvu': 'DJVU',
        '.fb2': 'FB2',
        '.cbz': 'CBZ',
        '.cbr': 'CBR'
    }
    
    def __init__(self, usuario: str, senha: str):
        self.logger = logging.getLogger(__name__)
        self.api = None
        self.logger.info(f"Conectando ao iCloud com usuário: {usuario}")
        
        if not ICLOUD_AVAILABLE:
            self.logger.error("Módulo PyiCloudService não disponível. Instale com 'pip install pyicloud'")
            raise ImportError("Módulo PyiCloudService não disponível")
            
        try:
            self.api = PyiCloudService(usuario, senha)
            
            # Verificar se é necessária autenticação adicional
            auth_manager = ICloudAuthManager()
            if not auth_manager.handle_2fa(self.api):
                raise Exception("Falha na autenticação de dois fatores")
                
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao iCloud: {str(e)}")
            raise
    
    def is_ebook(self, nome_arquivo: str) -> bool:
        extensao = Path(nome_arquivo).suffix.lower()
        return extensao in self.FORMATOS_EBOOK
    
    def get_formato(self, nome_arquivo: str) -> str:
        extensao = Path(nome_arquivo).suffix.lower()
        return self.FORMATOS_EBOOK.get(extensao, 'Desconhecido')
    
    def scan_pasta(self, caminho_pasta: str) -> List[EbookFile]:
        ebooks = []
        self.logger.info(f"Escaneando pasta iCloud Drive modificada: {caminho_pasta}")
        try:
            # Ajuste o caminho para o formato correto
            caminho_pasta_formatado = caminho_pasta.split('/')
            pasta = self.api.drive
            self.logger.info(f"Conteúdo do iCloud Drive: {pasta.dir()}")
            for parte in caminho_pasta_formatado:
                pasta = pasta[parte]
                self.logger.info(f"Parte: {parte}")
            for item_str in pasta.dir():
                item = pasta[item_str]
                if self.is_ebook(item.name):
                    ebook = EbookFile(
                        nome=item.name,
                        formato=self.get_formato(item.name),
                        tamanho=item.size,
                        data_modificacao=item.date_modified,
                        caminho=f"{caminho_pasta}/{item.name}"
                    )
                    ebooks.append(ebook)
                    self.logger.info(f"Ebook encontrado: {item.name}")
        
        except Exception as e:
            self.logger.error(f"Erro Bruto ao escanear pasta {caminho_pasta}: {str(e)}")
            raise
        
        return ebooks
    
    def gerar_relatorio(self, ebooks: List[EbookFile], formato: str = 'texto') -> str:
        if not ebooks:
            return "Nenhum ebook encontrado."
            
        if formato == 'csv':
            linhas = ['Nome,Formato,Tamanho(MB),Data Modificação,Caminho']
            for ebook in ebooks:
                tamanho_mb = round(ebook.tamanho / (1024 * 1024), 2)
                data = ebook.data_modificacao.strftime('%Y-%m-%d %H:%M:%S')
                linha = f'"{ebook.nome}",{ebook.formato},{tamanho_mb},{data},"{ebook.caminho}"'
                linhas.append(linha)
            return '\n'.join(linhas)
        
        else:  # formato texto
            relatorio = []
            relatorio.append("=== Relatório de Ebooks ===\n")
            for ebook in ebooks:
                tamanho_mb = round(ebook.tamanho / (1024 * 1024), 2)
                relatorio.append(f"Nome: {ebook.nome}")
                relatorio.append(f"Formato: {ebook.formato}")
                relatorio.append(f"Tamanho: {tamanho_mb} MB")
                relatorio.append(f"Última modificação: {ebook.data_modificacao}")
                relatorio.append(f"Caminho: {ebook.caminho}")
                relatorio.append("-" * 50)
            
            return '\n'.join(relatorio)
    
    def save_report_csv(self, ebooks: List[EbookFile], output_path: str) -> bool:
        """Salva o relatório em um arquivo CSV."""
        try:
            df = pd.DataFrame([
                {
                    'Nome': ebook.nome,
                    'Formato': ebook.formato,
                    'Tamanho(MB)': round(ebook.tamanho / (1024 * 1024), 2),
                    'Data Modificação': ebook.data_modificacao.strftime('%Y-%m-%d %H:%M:%S'),
                    'Caminho': ebook.caminho
                }
                for ebook in ebooks
            ])
            
            df.to_csv(output_path, index=False, encoding='utf-8')
            self.logger.info(f"Relatório salvo em {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar relatório CSV: {str(e)}")
            return False

class FileSystemEbookScanner:
    """Classe para escanear ebooks no sistema de arquivos local."""
    
    FORMATOS_EBOOK = {
        '.epub': 'EPUB',
        '.pdf': 'PDF',
        '.mobi': 'MOBI',
        '.azw': 'AZW',
        '.azw3': 'AZW3',
        '.kfx': 'KFX',
        '.txt': 'TXT',
        '.djvu': 'DJVU',
        '.fb2': 'FB2',
        '.cbz': 'CBZ',
        '.cbr': 'CBR'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def is_ebook(self, nome_arquivo: str) -> bool:
        extensao = Path(nome_arquivo).suffix.lower()
        return extensao in self.FORMATOS_EBOOK
    
    def get_formato(self, nome_arquivo: str) -> str:
        extensao = Path(nome_arquivo).suffix.lower()
        return self.FORMATOS_EBOOK.get(extensao, 'Desconhecido')
    
    def scan_folder(self, folder_path: str) -> List[EbookFile]:
        """Escaneia uma pasta no sistema de arquivos."""
        ebooks = []
        
        try:
            self.logger.info(f"Escaneando pasta: {folder_path}")
            
            if not os.path.exists(folder_path):
                self.logger.error(f"Pasta {folder_path} não encontrada")
                return ebooks
            
            for root, _, files in os.walk(folder_path):
                for filename in files:
                    if self.is_ebook(filename):
                        file_path = os.path.join(root, filename)
                        file_stat = os.stat(file_path)
                        
                        ebook = EbookFile(
                            nome=filename,
                            formato=self.get_formato(filename),
                            tamanho=file_stat.st_size,
                            data_modificacao=datetime.fromtimestamp(file_stat.st_mtime),
                            caminho=file_path
                        )
                        ebooks.append(ebook)
                        self.logger.info(f"Ebook encontrado: {filename}")
                        
            self.logger.info(f"Total de {len(ebooks)} ebooks encontrados em {folder_path}")
            return ebooks
            
        except Exception as e:
            self.logger.error(f"Erro ao escanear pasta: {str(e)}")
            return ebooks
    
    def save_report_csv(self, ebooks: List[EbookFile], output_path: str) -> bool:
        """Salva o relatório em um arquivo CSV."""
        try:
            df = pd.DataFrame([
                {
                    'Nome': ebook.nome,
                    'Formato': ebook.formato,
                    'Tamanho(MB)': round(ebook.tamanho / (1024 * 1024), 2),
                    'Data Modificação': ebook.data_modificacao.strftime('%Y-%m-%d %H:%M:%S'),
                    'Caminho': ebook.caminho
                }
                for ebook in ebooks
            ])
            
            df.to_csv(output_path, index=False, encoding='utf-8')
            self.logger.info(f"Relatório salvo em {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar relatório CSV: {str(e)}")
            return False

class DropboxEbookScanner:
    """Classe para escanear ebooks no Dropbox."""
    
    FORMATOS_EBOOK = {
        '.epub': 'EPUB',
        '.pdf': 'PDF',
        '.mobi': 'MOBI',
        '.azw': 'AZW',
        '.azw3': 'AZW3',
        '.kfx': 'KFX',
        '.txt': 'TXT',
        '.djvu': 'DJVU',
        '.fb2': 'FB2',
        '.cbz': 'CBZ',
        '.cbr': 'CBR'
    }
    
    def __init__(self, token: str):
        self.logger = logging.getLogger(__name__)
        
        if not DROPBOX_AVAILABLE:
            self.logger.error("Módulo dropbox não disponível. Instale com 'pip install dropbox'")
            raise ImportError("Módulo dropbox não disponível")
            
        try:
            self.dbx = dropbox.Dropbox(token)
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao Dropbox: {str(e)}")
            raise
    
    def is_ebook(self, nome_arquivo: str) -> bool:
        extensao = Path(nome_arquivo).suffix.lower()
        return extensao in self.FORMATOS_EBOOK
    
    def get_formato(self, nome_arquivo: str) -> str:
        extensao = Path(nome_arquivo).suffix.lower()
        return self.FORMATOS_EBOOK.get(extensao, 'Desconhecido')
    
    def scan_folder(self, folder_path: str) -> List[EbookFile]:
        """Escaneia uma pasta no Dropbox."""
        ebooks = []
        
        try:
            self.logger.info(f"Escaneando pasta Dropbox: {folder_path}")
            
            # Garantir que o caminho comece com /
            if not folder_path.startswith('/'):
                folder_path = '/' + folder_path
                
            result = self.dbx.files_list_folder(folder_path)
            
            has_more = True
            while has_more:
                for entry in result.entries:
                    if isinstance(entry, dropbox.files.FileMetadata):
                        filename = entry.name
                        if self.is_ebook(filename):
                            ebook = EbookFile(
                                nome=filename,
                                formato=self.get_formato(filename),
                                tamanho=entry.size,
                                data_modificacao=entry.server_modified,
                                caminho=f"dropbox://{folder_path}/{filename}"
                            )
                            ebooks.append(ebook)
                            self.logger.info(f"Ebook encontrado: {filename}")
                
                # Verificar se há mais resultados
                if result.has_more:
                    result = self.dbx.files_list_folder_continue(result.cursor)
                else:
                    has_more = False
                    
            self.logger.info(f"Total de {len(ebooks)} ebooks encontrados em {folder_path}")
            return ebooks
            
        except dropbox.exceptions.ApiError as e:
            self.logger.error(f"Erro na API do Dropbox: {str(e)}")
            return ebooks
        except Exception as e:
            self.logger.error(f"Erro ao escanear pasta Dropbox: {str(e)}")
            return ebooks
    
    def save_report_csv(self, ebooks: List[EbookFile], output_path: str) -> bool:
        """Salva o relatório em um arquivo CSV."""
        try:
            df = pd.DataFrame([
                {
                    'Nome': ebook.nome,
                    'Formato': ebook.formato,
                    'Tamanho(MB)': round(ebook.tamanho / (1024 * 1024), 2),
                    'Data Modificação': ebook.data_modificacao.strftime('%Y-%m-%d %H:%M:%S'),
                    'Caminho': ebook.caminho
                }
                for ebook in ebooks
            ])
            
            df.to_csv(output_path, index=False, encoding='utf-8')
            self.logger.info(f"Relatório salvo em {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar relatório CSV: {str(e)}")
            return False

class KindleEbookScanner:
    """Classe para processar dados da biblioteca Kindle."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def scan_kindle_library(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Processa um arquivo CSV exportado da biblioteca Kindle.
        
        Args:
            csv_path: Caminho para o arquivo CSV da biblioteca Kindle
            
        Returns:
            Lista de dicionários com dados dos ebooks
        """
        ebooks = []
        
        try:
            self.logger.info(f"Processando biblioteca Kindle: {csv_path}")
            
            if not os.path.exists(csv_path):
                self.logger.error(f"Arquivo {csv_path} não encontrado")
                return ebooks
                
            if not csv_path.endswith('.csv'):
                self.logger.error(f"O arquivo deve ser um CSV: {csv_path}")
                return ebooks
                
            # Ler CSV existente
            df = pd.read_csv(csv_path)
            
            # Mapear colunas para o formato padrão
            for _, row in df.iterrows():
                try:
                    # Campos esperados no CSV do Kindle: "Title", "Author", "ASIN", etc.
                    title = row.get('Title', '')
                    author = row.get('Author', '')
                    asin = row.get('ASIN', '')
                    
                    ebook = {
                        'Nome': f"{title} - {author}.azw",
                        'Formato': "AZW",
                        'Tamanho(MB)': 0,  # Não disponível no CSV do Kindle
                        'Data Modificação': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Caminho': f"kindle://{asin}",
                        'Titulo_Extraido': title,
                        'Autor_Extraido': author,
                        'ASIN': asin
                    }
                    
                    ebooks.append(ebook)
                    self.logger.info(f"Ebook processado: {title}")
                    
                except Exception as e:
                    self.logger.warning(f"Erro ao processar linha no CSV do Kindle: {str(e)}")
            
            self.logger.info(f"Total de {len(ebooks)} ebooks processados da biblioteca Kindle")
            return ebooks
            
        except Exception as e:
            self.logger.error(f"Erro ao processar biblioteca Kindle: {str(e)}")
            return ebooks
    
    def save_report_csv(self, ebooks: List[Dict[str, Any]], output_path: str) -> bool:
        """Salva o relatório em um arquivo CSV."""
        try:
            df = pd.DataFrame(ebooks)
            df.to_csv(output_path, index=False, encoding='utf-8')
            self.logger.info(f"Relatório Kindle salvo em {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar relatório CSV do Kindle: {str(e)}")
            return False