import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import os
import tempfile
import json
from core.services.library_service import LibraryService

class TestLibraryServiceGoogleBooks(unittest.TestCase):
    def setUp(self):
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample CSV file
        self.csv_path = os.path.join(self.temp_dir, 'test_books.csv')
        self.test_data = pd.DataFrame({
            'Nome': ['Book1.epub', 'Book2.pdf'],
            'Formato': ['EPUB', 'PDF'],
            'Tamanho(MB)': [1.5, 2.5],
            'Data Modificação': ['2023-01-01', '2023-01-02'],
            'Caminho': ['path/to/book1.epub', 'path/to/book2.pdf'],
            'Titulo_Extraido': ['Test Book 1', 'Test Book 2'],
            'Autor_Extraido': ['Test Author 1', 'Test Author 2']
        })
        self.test_data.to_csv(self.csv_path, index=False)
        
        # Mock dependencies
        self.config_repository = MagicMock()
        self.credential_service = MagicMock()
        self.scan_service = MagicMock()
        self.enrich_service = MagicMock()
        self.export_service = MagicMock()
        
        # Create Google Books enricher mock
        self.google_books_enricher = MagicMock()
        
        # Configure enricher registry
        self.enrich_service.enricher_registry = {
            'google_books': self.google_books_enricher
        }
        
        # Create library service
        self.library_service = LibraryService(
            self.config_repository,
            self.credential_service,
            self.scan_service,
            self.enrich_service,
            self.export_service
        )
        
        # Sample book metadata
        self.sample_metadata = {
            'title': 'Test Book',
            'subtitle': 'A Test Subtitle',
            'authors': ['Test Author'],
            'publisher': 'Test Publisher',
            'published_date': '2023',
            'isbn_10': '1234567890',
            'isbn_13': '9781234567890',
            'page_count': 200,
            'categories': ['Fiction', 'Test'],
            'language': 'en',
            'preview_link': 'http://test.com/preview',
            'cover_link': 'http://test.com/thumbnail.jpg',
            'match_confidence': 0.8,
            'confidence_factors': {},
            'volume_id': 'abc123'
        }
    
    def tearDown(self):
        # Remove temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_manual_search_book(self):
        # Configure mock to return sample books
        book1 = MagicMock()
        book1.title = 'Test Book 1'
        book1.subtitle = 'Subtitle 1'
        book1.authors = ['Author 1']
        book1.publisher = 'Publisher 1'
        book1.published_date = '2023'
        book1.isbn_10 = '1234567890'
        book1.isbn_13 = '9781234567890'
        book1.page_count = 200
        book1.categories = ['Fiction']
        book1.language = 'en'
        book1.preview_link = 'http://test.com/preview1'
        book1.cover_link = 'http://test.com/cover1.jpg'
        book1.match_confidence = 0.9
        book1.volume_id = 'book1'
        
        book2 = MagicMock()
        book2.title = 'Test Book 2'
        book2.subtitle = None
        book2.authors = ['Author 2', 'Co-author']
        book2.publisher = 'Publisher 2'
        book2.published_date = '2022'
        book2.isbn_10 = None
        book2.isbn_13 = '9780987654321'
        book2.page_count = 150
        book2.categories = ['Non-fiction']
        book2.language = 'pt'
        book2.preview_link = 'http://test.com/preview2'
        book2.cover_link = 'http://test.com/cover2.jpg'
        book2.match_confidence = 0.7
        book2.volume_id = 'book2'
        
        self.google_books_enricher.search_book_multiple_results.return_value = [book1, book2]
        
        # Test manual search
        results = self.library_service.manual_search_book('Test Book', 'Test Author')
        
        # Verify results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['title'], 'Test Book 1')
        self.assertEqual(results[0]['subtitle'], 'Subtitle 1')
        self.assertEqual(results[0]['authors'], 'Author 1')
        self.assertEqual(results[0]['volume_id'], 'book1')
        
        self.assertEqual(results[1]['title'], 'Test Book 2')
        self.assertIsNone(results[1]['subtitle'])
        self.assertEqual(results[1]['authors'], 'Author 2, Co-author')
        self.assertEqual(results[1]['volume_id'], 'book2')
        
        # Verify mock was called correctly
        self.google_books_enricher.search_book_multiple_results.assert_called_once_with(
            'Test Book', 'Test Author', 3
        )
    
    def test_get_book_by_id(self):
        # Configure mock to return sample book
        book = MagicMock()
        book.title = 'Test Book'
        book.subtitle = 'A Test Subtitle'
        book.authors = ['Test Author']
        book.publisher = 'Test Publisher'
        book.published_date = '2023'
        book.isbn_10 = '1234567890'
        book.isbn_13 = '9781234567890'
        book.page_count = 200
        book.categories = ['Fiction', 'Test']
        book.language = 'en'
        book.preview_link = 'http://test.com/preview'
        book.cover_link = 'http://test.com/cover.jpg'
        book.match_confidence = 0.8
        book.volume_id = 'abc123'
        
        self.google_books_enricher.get_book_by_id.return_value = book
        
        # Test get book by ID
        result = self.library_service.get_book_by_id('abc123')
        
        # Verify result
        self.assertEqual(result['title'], 'Test Book')
        self.assertEqual(result['subtitle'], 'A Test Subtitle')
        self.assertEqual(result['authors'], 'Test Author')
        self.assertEqual(result['publisher'], 'Test Publisher')
        self.assertEqual(result['volume_id'], 'abc123')
        
        # Verify mock was called correctly
        self.google_books_enricher.get_book_by_id.assert_called_once_with('abc123')
    
    def test_update_book_metadata(self):
        # Test update book metadata
        success = self.library_service.update_book_metadata(
            self.csv_path,
            0,  # First row
            {
                'title': 'Updated Title',
                'authors': 'Updated Author',
                'publisher': 'Updated Publisher',
                'volume_id': 'test123'
            }
        )
        
        # Verify success
        self.assertTrue(success)
        
        # Read updated CSV
        updated_df = pd.read_csv(self.csv_path)
        
        # Verify fields were updated
        self.assertEqual(updated_df.at[0, 'Titulo_Extraido'], 'Updated Title')
        self.assertEqual(updated_df.at[0, 'Autor_Extraido'], 'Updated Author')
        
        # Verify Google Books fields were created
        self.assertEqual(updated_df.at[0, 'GB_Titulo'], 'Updated Title')
        self.assertEqual(updated_df.at[0, 'GB_Editora'], 'Updated Publisher')
        self.assertEqual(updated_df.at[0, 'GB_Volume_ID'], 'test123')
        self.assertEqual(updated_df.at[0, 'GB_Status_Busca'], 'Manual')
        
        # Test update with invalid index
        success = self.library_service.update_book_metadata(
            self.csv_path,
            99,  # Invalid index
            {'title': 'Invalid'}
        )
        
        # Verify failure
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()