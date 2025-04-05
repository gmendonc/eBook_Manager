import unittest
import os
import tempfile
import shutil
import json
from unittest.mock import patch, MagicMock
from adapters.enrichers.google_books_enricher import GoogleBooksEnricher, BookMetadata

class TestGoogleBooksEnricher(unittest.TestCase):
    def setUp(self):
        # Criar diretório de cache temporário
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, 'cache/google_books')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Patch do diretório de cache
        self.cache_patcher = patch('adapters.enrichers.google_books_enricher.os.makedirs')
        self.mock_makedirs = self.cache_patcher.start()
        
        # Criar o enriquecedor
        self.enricher = GoogleBooksEnricher()
        
        # Dados de teste
        self.sample_volume_info = {
            'title': 'Test Book',
            'subtitle': 'A Test Subtitle',
            'authors': ['Test Author'],
            'publisher': 'Test Publisher',
            'publishedDate': '2023',
            'industryIdentifiers': [
                {'type': 'ISBN_10', 'identifier': '1234567890'},
                {'type': 'ISBN_13', 'identifier': '9781234567890'}
            ],
            'pageCount': 200,
            'categories': ['Fiction', 'Test'],
            'language': 'en',
            'previewLink': 'http://test.com/preview',
            'imageLinks': {
                'thumbnail': 'http://test.com/thumbnail.jpg'
            }
        }
        
        self.sample_response = {
            'items': [
                {
                    'id': 'abc123',
                    'volumeInfo': self.sample_volume_info
                }
            ]
        }
    
    def tearDown(self):
        # Remover diretório temporário
        shutil.rmtree(self.temp_dir)
        
        # Parar patcher
        self.cache_patcher.stop()
    
    @patch('adapters.enrichers.google_books_enricher.requests.Session')
    def test_search_book_multiple_results(self, mock_session):
        # Configurar mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_response
        
        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Testar busca
        self.enricher.session = mock_session_instance
        results = self.enricher.search_book_multiple_results('Test Book', 'Test Author')
        
        # Verificar resultados
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, 'Test Book')
        self.assertEqual(results[0].subtitle, 'A Test Subtitle')
        self.assertEqual(results[0].authors, ['Test Author'])
        self.assertEqual(results[0].volume_id, 'abc123')
    
    @patch('adapters.enrichers.google_books_enricher.requests.Session')
    def test_get_book_by_id(self, mock_session):
        # Configurar mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'abc123',
            'volumeInfo': self.sample_volume_info
        }
        
        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Testar busca por ID
        self.enricher.session = mock_session_instance
        book = self.enricher.get_book_by_id('abc123')
        
        # Verificar resultado
        self.assertIsNotNone(book)
        self.assertEqual(book.title, 'Test Book')
        self.assertEqual(book.isbn_10, '1234567890')
        self.assertEqual(book.isbn_13, '9781234567890')
        self.assertEqual(book.volume_id, 'abc123')
    
    def test_parse_volume_info(self):
        # Testar parse de volume_info
        metadata = self.enricher._parse_volume_info(self.sample_volume_info, 0.8, {})
        
        # Verificar resultado
        self.assertEqual(metadata.title, 'Test Book')
        self.assertEqual(metadata.subtitle, 'A Test Subtitle')
        self.assertEqual(metadata.authors, ['Test Author'])
        self.assertEqual(metadata.publisher, 'Test Publisher')
        self.assertEqual(metadata.published_date, '2023')
        self.assertEqual(metadata.isbn_10, '1234567890')
        self.assertEqual(metadata.isbn_13, '9781234567890')
        self.assertEqual(metadata.page_count, 200)
        self.assertEqual(metadata.categories, ['Fiction', 'Test'])
        self.assertEqual(metadata.language, 'en')
        self.assertEqual(metadata.preview_link, 'http://test.com/preview')
        self.assertEqual(metadata.cover_link, 'http://test.com/thumbnail.jpg')
        self.assertEqual(metadata.match_confidence, 0.8)
    
    def test_calculate_match_confidence(self):
        # Caso 1: Correspondência exata
        confidence, factors = self.enricher._calculate_match_confidence(
            self.sample_volume_info, 
            'Test Book', 
            'Test Author'
        )
        self.assertGreater(confidence, 0.8)
        
        # Caso 2: Correspondência parcial
        confidence, factors = self.enricher._calculate_match_confidence(
            self.sample_volume_info, 
            'Book Test', 
            'Another Author'
        )
        self.assertLess(confidence, 0.8)
        
        # Caso 3: Sem correspondência
        confidence, factors = self.enricher._calculate_match_confidence(
            self.sample_volume_info, 
            'Completely Different', 
            'Unknown Author'
        )
        self.assertLess(confidence, 0.3)
    
    def test_cache_key(self):
        # Testar geração de chave de cache
        key1 = self.enricher._cache_key('Test Query', 'en')
        key2 = self.enricher._cache_key('Test Query', 'en')
        key3 = self.enricher._cache_key('Test Query', 'pt')
        
        # Verificar que a mesma consulta gera a mesma chave
        self.assertEqual(key1, key2)
        
        # Verificar que consultas diferentes geram chaves diferentes
        self.assertNotEqual(key1, key3)
    
    @patch('builtins.open')
    @patch('json.load')
    @patch('os.path.exists')
    def test_get_from_cache(self, mock_exists, mock_json_load, mock_open):
        # Configurar mocks
        mock_exists.return_value = True
        mock_json_load.return_value = {
            'timestamp': time.time(),
            'data': self.sample_response
        }
        
        # Testar recuperação do cache
        result = self.enricher._get_from_cache('test_key')
        
        # Verificar resultado
        self.assertEqual(result, self.sample_response)
        mock_exists.assert_called_once()
        mock_open.assert_called_once()
        mock_json_load.assert_called_once()

if __name__ == '__main__':
    unittest.main()