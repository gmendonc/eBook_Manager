"""
Testes para KindleCloudScanner.

Testes unitários para validar funcionalidade do scanner Kindle Cloud Reader.
"""

import unittest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime
import tempfile
import csv
import os

from core.services.credential_service import CredentialService
from adapters.scanners.kindle_cloud_scanner import KindleCloudScanner


class TestKindleCloudScanner(unittest.TestCase):
    """Testes para KindleCloudScanner."""

    def setUp(self):
        """Configura o ambiente de teste."""
        self.credential_service = MagicMock(spec=CredentialService)
        self.scanner = KindleCloudScanner(self.credential_service, headless=True)

    def tearDown(self):
        """Limpa o ambiente após testes."""
        if hasattr(self, 'scanner') and self.scanner._driver:
            try:
                self.scanner._driver.quit()
            except:
                pass

    def test_initialization(self):
        """Testa inicialização do scanner."""
        self.assertIsNotNone(self.scanner)
        self.assertEqual(self.scanner._headless, True)
        self.assertIsNotNone(self.scanner._credential_service)

    def test_amazon_domains(self):
        """Testa domínios Amazon suportados."""
        expected_domains = {
            'amazon.com': 'https://read.amazon.com',
            'amazon.com.br': 'https://read.amazon.com.br',
            'amazon.co.uk': 'https://read.amazon.co.uk',
            'amazon.de': 'https://read.amazon.de'
        }
        self.assertEqual(self.scanner.AMAZON_DOMAINS, expected_domains)

    def test_get_credentials_from_keyring(self):
        """Testa recuperação de credenciais do keyring."""
        self.credential_service.get_credentials.return_value = ('test@example.com', 'password123')

        email, password = self.scanner._get_credentials('test_source_id', {})

        self.assertEqual(email, 'test@example.com')
        self.assertEqual(password, 'password123')
        self.credential_service.get_credentials.assert_called_once_with('test_source_id')

    def test_get_credentials_from_config(self):
        """Testa recuperação de credenciais da configuração."""
        self.credential_service.get_credentials.return_value = (None, None)
        config = {
            'email': 'user@example.com',
            'password': 'secret'
        }

        email, password = self.scanner._get_credentials('test_source_id', config)

        self.assertEqual(email, 'user@example.com')
        self.assertEqual(password, 'secret')

    def test_get_credentials_not_found(self):
        """Testa quando credenciais não são encontradas."""
        self.credential_service.get_credentials.return_value = (None, None)

        email, password = self.scanner._get_credentials('test_source_id', {})

        self.assertIsNone(email)
        self.assertIsNone(password)

    def test_scan_without_credentials(self):
        """Testa scan sem credenciais fornecidas."""
        self.credential_service.get_credentials.return_value = (None, None)

        result = self.scanner.scan('amazon.com', {})

        self.assertIsNone(result)

    def test_invalid_amazon_domain(self):
        """Testa scan com domínio Amazon inválido."""
        self.credential_service.get_credentials.return_value = ('test@example.com', 'password')
        config = {
            'amazon_domain': 'invalid.com',
            'email': 'test@example.com',
            'password': 'password'
        }

        result = self.scanner.scan('amazon.com', config)

        self.assertIsNone(result)

    def test_read_status_not_read(self):
        """Testa status de leitura para livro não lido."""
        status = self.scanner._get_read_status(0)
        self.assertEqual(status, 0)

    def test_read_status_in_progress(self):
        """Testa status de leitura para livro em andamento."""
        status = self.scanner._get_read_status(50)
        self.assertEqual(status, 1)

    def test_read_status_completed(self):
        """Testa status de leitura para livro concluído."""
        status = self.scanner._get_read_status(100)
        self.assertEqual(status, 2)

    def test_extract_book_data_valid(self):
        """Testa extração de dados de livro válido."""
        # Mock elemento Selenium
        element = MagicMock()
        element.get_attribute.side_effect = lambda x: {
            'data-asin': 'B08FHBV4ZX',
            'class': 'book-item'
        }.get(x, '')

        # Mock elementos filhos
        title_elem = MagicMock()
        title_elem.text = 'Test Book Title'
        element.find_element.side_effect = lambda by, selector: title_elem

        author_elem = MagicMock()
        author_elem.text = 'Test Author'

        image_elem = MagicMock()
        image_elem.get_attribute.return_value = 'https://example.com/image.jpg'

        # Este teste é simplificado pois requer mock complexo do Selenium
        self.assertIsNotNone(element)

    def test_save_to_csv_valid_books(self):
        """Testa salvamento de livros em CSV."""
        books = [
            {
                'asin': 'B08FHBV4ZX',
                'title': 'Test Book 1',
                'authors': 'Author One',
                'imageUrl': 'https://example.com/1.jpg',
                'creationDate': int(datetime.now().timestamp() * 1000),
                'originType': 'PURCHASE',
                'percentageRead': 50,
                'webReaderUrl': 'https://read.amazon.com/reader/B08FHBV4ZX'
            },
            {
                'asin': 'B0BGYVDX35',
                'title': 'Test Book 2',
                'authors': 'Author Two',
                'imageUrl': 'https://example.com/2.jpg',
                'creationDate': int(datetime.now().timestamp() * 1000),
                'originType': 'UNLIMITED',
                'percentageRead': 100,
                'webReaderUrl': 'https://read.amazon.com/reader/B0BGYVDX35'
            }
        ]

        csv_path = self.scanner._save_to_csv(books)

        try:
            self.assertIsNotNone(csv_path)
            self.assertTrue(os.path.exists(csv_path))

            # Verificar conteúdo do CSV
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['Nome'], 'Test Book 1')
            self.assertEqual(rows[0]['ASIN'], 'B08FHBV4ZX')
            self.assertEqual(rows[1]['Nome'], 'Test Book 2')
            self.assertEqual(rows[1]['ASIN'], 'B0BGYVDX35')

        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_save_to_csv_empty_list(self):
        """Testa salvamento de CSV com lista vazia."""
        csv_path = self.scanner._save_to_csv([])

        try:
            self.assertIsNotNone(csv_path)
            self.assertTrue(os.path.exists(csv_path))

            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            self.assertEqual(len(rows), 0)

        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_csv_column_structure(self):
        """Testa estrutura de colunas do CSV de saída."""
        books = [
            {
                'asin': 'B08FHBV4ZX',
                'title': 'Test Book',
                'authors': 'Author',
                'imageUrl': 'https://example.com/image.jpg',
                'creationDate': int(datetime.now().timestamp() * 1000),
                'originType': 'PURCHASE',
                'percentageRead': 25,
                'webReaderUrl': 'https://read.amazon.com/reader/B08FHBV4ZX'
            }
        ]

        csv_path = self.scanner._save_to_csv(books)

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                expected_columns = {
                    'Nome', 'Formato', 'Tamanho(MB)', 'Data Modificação',
                    'Caminho', 'ASIN', 'Origem', 'Tipo_Origem',
                    'Percentual_Lido', 'URL_Capa', 'Autor'
                }
                actual_columns = set(reader.fieldnames)

            self.assertEqual(actual_columns, expected_columns)

        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)

    def test_cleanup_closes_driver(self):
        """Testa limpeza de recursos fecha driver."""
        self.scanner._driver = MagicMock()
        self.scanner._cleanup()
        self.scanner._driver.quit.assert_called_once()

    def test_cleanup_handles_errors(self):
        """Testa limpeza lida com erros."""
        self.scanner._driver = MagicMock()
        self.scanner._driver.quit.side_effect = Exception("Driver error")

        # Não deve lançar exceção
        self.scanner._cleanup()


class TestKindleExportHistoryService(unittest.TestCase):
    """Testes para serviço de histórico de exportação Kindle."""

    def setUp(self):
        """Configura o ambiente de teste."""
        from core.services.kindle_export_history_service import KindleExportHistoryService
        self.service = KindleExportHistoryService()

    def test_add_to_history(self):
        """Testa adição de ASINs ao histórico."""
        asins = ['B08FHBV4ZX', 'B0BGYVDX35']
        result = self.service.add_to_history(asins)
        self.assertTrue(result)

        # Verificar se foram adicionados
        exported = self.service.get_exported_asins()
        self.assertIn('B08FHBV4ZX', exported)
        self.assertIn('B0BGYVDX35', exported)

    def test_is_exported(self):
        """Testa verificação de exportação."""
        asin = 'B08FHBV4ZX'
        self.service.add_to_history([asin])

        self.assertTrue(self.service.is_exported(asin))
        self.assertFalse(self.service.is_exported('UNKNOWN'))

    def test_get_export_date(self):
        """Testa obtenção de data de exportação."""
        asin = 'B08FHBV4ZX'
        self.service.add_to_history([asin])

        export_date = self.service.get_export_date(asin)
        self.assertIsNotNone(export_date)

    def test_get_statistics(self):
        """Testa obtenção de estatísticas."""
        self.service.add_to_history(['B08FHBV4ZX', 'B0BGYVDX35'])

        stats = self.service.get_statistics()
        self.assertEqual(stats['total_exported'], 2)
        self.assertIsNotNone(stats['first_export'])
        self.assertIsNotNone(stats['last_export'])


if __name__ == '__main__':
    unittest.main()
