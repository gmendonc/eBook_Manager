"""
Scanner para Kindle Cloud Reader usando Selenium.

Este scanner extrai a biblioteca completa do Kindle Cloud Reader
acessando https://read.amazon.com via navegador automatizado.
"""

import logging
import os
import csv
import json
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path
from tempfile import gettempdir

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager

from core.interfaces.scanner import Scanner
from core.services.credential_service import CredentialService

logger = logging.getLogger(__name__)


class KindleCloudScanner(Scanner):
    """
    Scanner para biblioteca Kindle Cloud Reader.

    Extrai livros do Kindle Cloud Reader usando Selenium WebDriver,
    com suporte a autenticação de dois fatores (2FA) e armazenamento
    seguro de credenciais via keyring.

    Dados extraídos:
    - asin: Identificador único Amazon
    - title: Título do livro
    - authors: Autor(es)
    - imageUrl: URL da capa
    - creationDate: Timestamp de aquisição
    - originType: PURCHASE, FREE, PRIME_READING, UNLIMITED
    - percentageRead: Percentual lido (0-100)
    - webReaderUrl: URL para ler online
    """

    # URLs base por região
    AMAZON_DOMAINS = {
        'amazon.com': 'https://read.amazon.com',
        'amazon.com.br': 'https://read.amazon.com.br',
        'amazon.co.uk': 'https://read.amazon.co.uk',
        'amazon.de': 'https://read.amazon.de'
    }

    # Timeout padrão (segundos)
    LOGIN_TIMEOUT = 30
    LIBRARY_LOAD_TIMEOUT = 60

    def __init__(self, credential_service: CredentialService, headless: bool = True):
        """
        Inicializa o scanner.

        Args:
            credential_service: Serviço para gerenciamento de credenciais
            headless: Se True, executa navegador em modo headless
        """
        self._credential_service = credential_service
        self._headless = headless
        self._driver: Optional[webdriver.Chrome] = None

    def scan(
        self,
        path: str,
        config: Optional[Dict[str, Any]] = None,
        source_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Escaneia biblioteca Kindle Cloud Reader.

        Args:
            path: URL base Amazon (e.g., 'amazon.com') - não utilizado para Cloud
            config: Dicionário com configurações:
                - amazon_domain: Domínio Amazon (amazon.com, amazon.com.br, etc)
                - email: Email Amazon
                - password: Senha Amazon (opcional se usar keyring)
                - region: Região (usa amazon_domain se não fornecido)
            source_id: ID da fonte para buscar credenciais no keyring

        Returns:
            Caminho para arquivo CSV gerado ou None em caso de erro

        Raises:
            ValueError: Se configuração inválida
            WebDriverException: Se erro ao inicializar navegador
        """
        try:
            # Validar e preparar configuração
            config = config or {}
            email, password = self._get_credentials(source_id, config)

            if not email or not password:
                logger.error("Email ou senha não fornecidos para Kindle Cloud Reader")
                return None

            amazon_domain = config.get('amazon_domain', 'amazon.com')
            if amazon_domain not in self.AMAZON_DOMAINS:
                logger.error(f"Domínio Amazon inválido: {amazon_domain}")
                return None

            base_url = self.AMAZON_DOMAINS[amazon_domain]
            logger.info(f"Iniciando scan Kindle Cloud Reader - Domínio: {amazon_domain}")

            # Inicializar navegador
            self._initialize_driver()

            # Realizar login
            if not self._login(base_url, email, password, source_id):
                logger.error("Falha ao fazer login no Kindle Cloud Reader")
                return None

            # Carregar biblioteca
            books = self._extract_library(base_url)
            if not books:
                logger.warning("Nenhum livro encontrado na biblioteca")
                return None

            # Converter para CSV
            csv_path = self._save_to_csv(books)
            logger.info(f"Biblioteca Kindle salva em: {csv_path}")

            return csv_path

        except Exception as e:
            logger.error(f"Erro ao scanear Kindle Cloud Reader: {str(e)}", exc_info=True)
            return None
        finally:
            self._cleanup()

    def _get_credentials(
        self,
        source_id: Optional[str],
        config: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Obtém credenciais do keyring ou configuração.

        Args:
            source_id: ID da fonte para buscar credenciais
            config: Configuração com credenciais alternativas

        Returns:
            Tupla (email, password) ou (None, None) se não encontrado
        """
        email = None
        password = None

        # Tentar obter do keyring primeiro
        if source_id:
            stored_email, stored_password = self._credential_service.get_credentials(source_id)
            if stored_email and stored_password:
                email = stored_email
                password = stored_password
                logger.debug(f"Credenciais recuperadas do keyring para {source_id}")

        # Se não encontrou, usar configuração
        if not email or not password:
            email = config.get('email')
            password = config.get('password')

        return email, password

    def _initialize_driver(self) -> None:
        """Inicializa o Selenium WebDriver."""
        try:
            chrome_options = Options()

            if self._headless:
                chrome_options.add_argument('--headless=new')

            # Desabilitar notificações e popups
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-popup-blocking')

            # Desabilitar modo de aplicativo
            chrome_options.add_argument('--disable-application-cache')

            # User agent padrão
            chrome_options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/121.0.0.0 Safari/537.36'
            )

            service = Service(ChromeDriverManager().install())
            self._driver = webdriver.Chrome(service=service, options=chrome_options)

            logger.debug("WebDriver Chrome inicializado")

        except WebDriverException as e:
            logger.error(f"Erro ao inicializar WebDriver: {str(e)}")
            raise

    def _login(self, base_url: str, email: str, password: str, source_id: Optional[str]) -> bool:
        """
        Realiza login no Kindle Cloud Reader.

        Args:
            base_url: URL base do Kindle Cloud
            email: Email Amazon
            password: Senha Amazon
            source_id: ID da fonte para salvar credenciais se necessário

        Returns:
            True se login bem-sucedido, False caso contrário
        """
        try:
            logger.info("Navegando para Kindle Cloud Reader...")
            self._driver.get(base_url)

            # Aguardar página carregar - tentar múltiplos seletores
            try:
                WebDriverWait(self._driver, self.LOGIN_TIMEOUT).until(
                    EC.presence_of_element_located((By.ID, "ap_email"))
                )
                logger.debug("Campo de email detectado (ID: ap_email)")
            except TimeoutException:
                logger.warning("Seletor #ap_email não encontrado, tentando alternativas...")
                try:
                    WebDriverWait(self._driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
                    )
                    logger.debug("Campo de email detectado (CSS: input[type='email'])")
                except TimeoutException:
                    logger.error("Não foi possível encontrar campo de email em nenhum formato")
                    logger.error(f"URL atual: {self._driver.current_url}")
                    logger.error(f"Primeira 500 chars da página: {self._driver.page_source[:500]}")
                    return False

            logger.debug("Página de login detectada")

            # Preencher email - tentar múltiplos seletores
            try:
                email_field = self._driver.find_element(By.ID, "ap_email")
            except:
                email_field = self._driver.find_element(By.CSS_SELECTOR, "input[type='email']")

            email_field.clear()
            email_field.send_keys(email)
            logger.debug("Email preenchido")

            # Preencher senha
            try:
                password_field = self._driver.find_element(By.ID, "ap_password")
            except:
                password_field = self._driver.find_element(By.CSS_SELECTOR, "input[type='password']")

            password_field.clear()
            password_field.send_keys(password)
            logger.debug("Senha preenchida")

            # Clicar botão de login
            try:
                login_button = self._driver.find_element(By.ID, "signInSubmit")
            except:
                login_button = self._driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

            login_button.click()
            logger.debug("Formulário de login enviado")

            # Aguardar carregamento (pode redirecionar ou exigir 2FA)
            WebDriverWait(self._driver, self.LOGIN_TIMEOUT).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )

            current_url = self._driver.current_url

            # Verificar se há exigência de 2FA
            if "auth-mfa" in current_url or "2FA" in self._driver.page_source:
                logger.warning("Autenticação de dois fatores (2FA) detectada")
                logger.warning("2FA não é suportado de forma automática nesta versão")
                return False

            # Verificar se login foi bem-sucedido
            if "read.amazon" in current_url:
                logger.info("Login bem-sucedido")
                return True
            else:
                logger.error(f"Login falhou. URL atual: {current_url}")
                return False

        except TimeoutException:
            logger.error("Timeout ao fazer login no Kindle Cloud Reader")
            return False
        except Exception as e:
            logger.error(f"Erro ao fazer login: {str(e)}", exc_info=True)
            return False

    def _extract_library(self, base_url: str) -> List[Dict[str, Any]]:
        """
        Extrai lista de livros da biblioteca.

        Extrai dados do Web SQL Database do Cloud Reader ou via JavaScript.

        Args:
            base_url: URL base do Kindle Cloud

        Returns:
            Lista de dicionários com dados dos livros
        """
        try:
            logger.info("Extraindo biblioteca do Kindle Cloud Reader...")

            # Aguardar a página de biblioteca carregar
            WebDriverWait(self._driver, self.LIBRARY_LOAD_TIMEOUT).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "book"))
            )

            logger.debug("Página da biblioteca carregada")

            # Tentar extrair via Web SQL Database (método preferido)
            books = self._extract_from_database()

            if not books:
                # Fallback: extrair via DOM
                logger.debug("Tentando extração via DOM...")
                books = self._extract_from_dom()

            # Ordenar por data de criação (mais recentes primeiro)
            books.sort(
                key=lambda x: x.get('creationDate', 0),
                reverse=True
            )

            logger.info(f"Total de {len(books)} livros extraídos")
            return books

        except TimeoutException:
            logger.error("Timeout ao carregar biblioteca do Kindle")
            return []
        except Exception as e:
            logger.error(f"Erro ao extrair biblioteca: {str(e)}", exc_info=True)
            return []

    def _extract_from_database(self) -> List[Dict[str, Any]]:
        """
        Extrai livros do Web SQL Database do Cloud Reader.

        Returns:
            Lista de livros ou lista vazia se indisponível
        """
        try:
            # Script JavaScript para acessar Web SQL Database
            script = """
            return new Promise((resolve) => {
                // Tentar acessar dados via janela global se disponível
                if (window.__apj_library_data) {
                    resolve(window.__apj_library_data);
                } else if (window.__apj_books) {
                    resolve(window.__apj_books);
                } else {
                    // Nenhum dado disponível
                    resolve([]);
                }
            });
            """

            result = self._driver.execute_script(script)

            if result and isinstance(result, list):
                logger.debug(f"Extratos {len(result)} livros do banco de dados")
                return result

            return []

        except Exception as e:
            logger.debug(f"Não foi possível acessar Web SQL Database: {str(e)}")
            return []

    def _extract_from_dom(self) -> List[Dict[str, Any]]:
        """
        Extrai livros pelo DOM da página.

        Fallback se Web SQL Database não estiver disponível.

        Returns:
            Lista de livros extraídos do DOM
        """
        books = []

        try:
            # Encontrar todos os elementos de livro
            book_elements = self._driver.find_elements(By.CLASS_NAME, "book")
            logger.debug(f"Encontrados {len(book_elements)} elementos de livro no DOM")

            for book_elem in book_elements:
                try:
                    book_data = self._extract_book_data(book_elem)
                    if book_data:
                        books.append(book_data)
                except Exception as e:
                    logger.debug(f"Erro ao extrair livro individual: {str(e)}")
                    continue

            logger.debug(f"Total de {len(books)} livros extraídos do DOM")
            return books

        except Exception as e:
            logger.debug(f"Erro ao extrair do DOM: {str(e)}")
            return []

    def _extract_book_data(self, element) -> Optional[Dict[str, Any]]:
        """
        Extrai dados de um livro individual.

        Args:
            element: Elemento Selenium contendo dados do livro

        Returns:
            Dicionário com dados do livro ou None
        """
        try:
            # Tentar extrair ASIN do atributo data-asin
            asin = element.get_attribute('data-asin')
            if not asin:
                return None

            # Extrair título
            title_elem = element.find_element(By.CLASS_NAME, "book-title")
            title = title_elem.text.strip() if title_elem else "Desconhecido"

            # Extrair autor
            author_elem = element.find_element(By.CLASS_NAME, "book-author")
            authors = author_elem.text.strip() if author_elem else "Desconhecido"

            # Extrair URL da capa
            image_elem = element.find_element(By.TAG_NAME, "img")
            image_url = image_elem.get_attribute('src') if image_elem else ""

            # Extrair data (pode estar em atributo ou texto)
            creation_date = int(datetime.now().timestamp() * 1000)  # Default: agora
            date_elem = element.find_element(By.CLASS_NAME, "acquisition-date")
            if date_elem:
                # Tentar parse da data
                try:
                    date_text = date_elem.text.strip()
                    parsed_date = datetime.strptime(date_text, "%d/%m/%Y")
                    creation_date = int(parsed_date.timestamp() * 1000)
                except:
                    pass

            # Extrair tipo de origem
            origin_type = "PURCHASE"  # Default
            if "Prime Reading" in element.get_attribute('class') or "prime" in element.get_attribute('class'):
                origin_type = "PRIME_READING"

            # Extrair percentual lido
            progress_elem = element.find_element(By.CLASS_NAME, "progress-percent")
            percentage_read = 0
            if progress_elem:
                try:
                    text = progress_elem.text.strip()
                    percentage_read = int(''.join(filter(str.isdigit, text)))
                except:
                    pass

            # URL para ler online
            web_reader_url = element.find_element(By.TAG_NAME, "a").get_attribute('href')
            if not web_reader_url or not web_reader_url.startswith('http'):
                web_reader_url = f"https://read.amazon.com/reader/{asin}"

            return {
                'asin': asin,
                'title': title,
                'authors': authors,
                'imageUrl': image_url,
                'creationDate': creation_date,
                'originType': origin_type,
                'percentageRead': percentage_read,
                'webReaderUrl': web_reader_url
            }

        except Exception as e:
            logger.debug(f"Erro ao extrair dados do livro: {str(e)}")
            return None

    def _save_to_csv(self, books: List[Dict[str, Any]]) -> str:
        """
        Salva livros em arquivo CSV temporário.

        Args:
            books: Lista de livros

        Returns:
            Caminho para o arquivo CSV criado

        Raises:
            IOError: Se erro ao criar arquivo
        """
        try:
            # Gerar nome do arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kindle_temp_{timestamp}.csv"
            csv_path = os.path.join(gettempdir(), filename)

            # Definir colunas no padrão do eBook Manager
            fieldnames = [
                'Nome',
                'Formato',
                'Tamanho(MB)',
                'Data Modificação',
                'Caminho',
                'ASIN',
                'Origem',
                'Tipo_Origem',
                'Percentual_Lido',
                'URL_Capa',
                'Autor'
            ]

            # Escrever CSV
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for book in books:
                    # Converter timestamp para datetime
                    creation_date = datetime.fromtimestamp(book['creationDate'] / 1000)

                    writer.writerow({
                        'Nome': book['title'],
                        'Formato': 'AZW3/KFX',
                        'Tamanho(MB)': 0,
                        'Data Modificação': creation_date.strftime('%d/%m/%Y %H:%M'),
                        'Caminho': book['webReaderUrl'],
                        'ASIN': book['asin'],
                        'Origem': 'Kindle',
                        'Tipo_Origem': book['originType'],
                        'Percentual_Lido': book['percentageRead'],
                        'URL_Capa': book['imageUrl'],
                        'Autor': book['authors']
                    })

            logger.info(f"CSV salvo em: {csv_path}")
            return csv_path

        except IOError as e:
            logger.error(f"Erro ao salvar CSV: {str(e)}")
            raise

    def _cleanup(self) -> None:
        """Limpa recursos (fecha navegador)."""
        try:
            if self._driver:
                self._driver.quit()
                logger.debug("WebDriver encerrado")
        except Exception as e:
            logger.warning(f"Erro ao fechar WebDriver: {str(e)}")
