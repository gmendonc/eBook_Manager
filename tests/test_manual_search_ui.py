import unittest
from unittest.mock import patch, MagicMock
import streamlit as st
from ui.pages.view_page import (
    init_manual_search_state, 
    display_book_search_results,
    render_manual_search_section
)

class TestManualSearchUI(unittest.TestCase):
    def setUp(self):
        # Mock Streamlit session state
        self.mock_session_state = {}
        self.session_state_patcher = patch.object(st, 'session_state', self.mock_session_state)
        self.mock_st_session_state = self.session_state_patcher.start()
        
        # Mock Streamlit components
        self.mock_st_write = patch.object(st, 'write').start()
        self.mock_st_button = patch.object(st, 'button').start()
        self.mock_st_form = patch.object(st, 'form', return_value=MagicMock()).start()
        self.mock_st_columns = patch.object(st, 'columns').start()
        self.mock_st_container = patch.object(st, 'container', return_value=MagicMock()).start()
        self.mock_st_expander = patch.object(st, 'expander', return_value=MagicMock()).start()
        self.mock_st_image = patch.object(st, 'image').start()
        self.mock_st_spinner = patch.object(st, 'spinner', return_value=MagicMock()).start()
        self.mock_st_success = patch.object(st, 'success').start()
        self.mock_st_error = patch.object(st, 'error').start()
        self.mock_st_warning = patch.object(st, 'warning').start()
        self.mock_st_subheader = patch.object(st, 'subheader').start()
        self.mock_st_text_input = patch.object(st, 'text_input').start()
        self.mock_st_selectbox = patch.object(st, 'selectbox').start()
        self.mock_st_markdown = patch.object(st, 'markdown').start()
        self.mock_st_rerun = patch.object(st, 'experimental_rerun').start()
        self.mock_st_dataframe = patch.object(st, 'dataframe').start()
        
        # Sample results for testing
        self.sample_results = [
            {
                'title': 'Test Book 1',
                'subtitle': 'A Test Subtitle',
                'authors': 'Test Author',
                'publisher': 'Test Publisher',
                'published_date': '2023',
                'isbn_10': '1234567890',
                'isbn_13': '9781234567890',
                'page_count': 200,
                'categories': 'Fiction, Test',
                'language': 'en',
                'preview_link': 'http://test.com/preview',
                'cover_link': 'http://test.com/thumbnail.jpg',
                'confidence': 0.8,
                'volume_id': 'abc123'
            },
            {
                'title': 'Test Book 2',
                'subtitle': None,
                'authors': 'Another Author',
                'publisher': 'Another Publisher',
                'published_date': '2020',
                'isbn_10': None,
                'isbn_13': '9780987654321',
                'page_count': 150,
                'categories': 'Non-fiction',
                'language': 'pt',
                'preview_link': 'http://test.com/preview2',
                'cover_link': None,
                'confidence': 0.6,
                'volume_id': 'def456'
            }
        ]
        
        # Mock library service
        self.mock_library_service = MagicMock()
        self.mock_library_service.update_book_metadata.return_value = True
        
        # Mock pandas DataFrame for testing
        self.mock_df = MagicMock()
        self.mock_df.iloc.__getitem__.return_value.get.side_effect = lambda key, default=None: {
            'Titulo_Extraido': 'Test Book',
            'Autor_Extraido': 'Test Author',
            'Nome': 'TestBook.epub',
            'Formato': 'EPUB'
        }.get(key, default)
    
    def tearDown(self):
        # Stop all patches
        patch.stopall()
    
    def test_init_manual_search_state(self):
        # Test initializing state
        init_manual_search_state()
        
        # Verify state was initialized
        self.assertEqual(self.mock_session_state.get('manual_search_mode'), 'select')
        self.assertEqual(self.mock_session_state.get('selected_row'), 0)
        self.assertEqual(self.mock_session_state.get('search_results'), [])
        self.assertEqual(self.mock_session_state.get('manual_search_expanded'), False)
    
    def test_display_book_search_results_with_results(self):
        # Setup state
        self.mock_session_state['selected_row'] = 0
        
        # Configure mock buttons
        self.mock_st_button.return_value = False
        
        # Test displaying results
        display_book_search_results(
            self.sample_results,
            'test.csv',
            self.mock_library_service
        )
        
        # Verify components were created
        self.mock_st_write.assert_any_call("### Resultados da Busca")
        self.mock_st_write.assert_any_call("Selecione o resultado que melhor corresponde ao seu livro:")
        
        # Verify container was created twice (once for each result)
        self.assertEqual(self.mock_st_container.call_count, 2)
        
        # Verify subheader was called for book titles
        self.mock_st_subheader.assert_any_call('Test Book 1')
        self.mock_st_subheader.assert_any_call('Test Book 2')
        
        # Verify buttons were created
        self.mock_st_button.assert_any_call("Selecionar", key="select_0")
        self.mock_st_button.assert_any_call("Selecionar", key="select_1")
        self.mock_st_button.assert_any_call("Cancelar")
    
    def test_display_book_search_results_with_selection(self):
        # Setup state
        self.mock_session_state['selected_row'] = 0
        
        # Configure mock buttons
        self.mock_st_button.side_effect = [True, False]  # First button (select_0) returns True
        
        # Test displaying results with selection
        display_book_search_results(
            self.sample_results,
            'test.csv',
            self.mock_library_service
        )
        
        # Verify update_book_metadata was called
        self.mock_library_service.update_book_metadata.assert_called_once_with(
            'test.csv',
            0,
            self.sample_results[0]
        )
        
        # Verify success message was shown
        self.mock_st_success.assert_called_once()
        
        # Verify state was reset
        self.assertEqual(self.mock_session_state['manual_search_mode'], 'select')
        self.assertEqual(self.mock_session_state['search_results'], [])
        self.assertEqual(self.mock_session_state['manual_search_expanded'], False)
        
        # Verify page was rerun
        self.mock_st_rerun.assert_called_once()
    
    def test_display_book_search_results_empty(self):
        # Test displaying empty results
        display_book_search_results(
            [],
            'test.csv',
            self.mock_library_service
        )
        
        # Verify warning was shown
        self.mock_st_warning.assert_called_once()
        
        # Verify back button was created
        self.mock_st_button.assert_called_once_with("Voltar à Busca")
    
    def test_render_manual_search_section_select_mode(self):
        # Setup state
        self.mock_session_state['manual_search_mode'] = 'select'
        self.mock_session_state['manual_search_expanded'] = True
        
        # Configure mock components
        self.mock_st_button.return_value = False
        
        # Test rendering search section in select mode
        render_manual_search_section(
            self.mock_df,
            'test.csv',
            self.mock_library_service
        )
        
        # Verify expander was created
        self.mock_st_expander.assert_called_once_with("🔍 Enriquecimento Manual", expanded=True)
        
        # Verify write was called
        self.mock_st_write.assert_any_call("Selecione um livro para busca manual no Google Books:")
        
        # Verify selectbox was created
        self.mock_st_selectbox.assert_called_once()
        
        # Verify book info was displayed
        self.mock_st_write.assert_any_call("### Informações do Livro")
        
        # Verify search button was created
        self.mock_st_button.assert_called_once_with("Buscar no Google Books", key="start_search")
    
    def test_render_manual_search_section_search_mode(self):
        # Setup state
        self.mock_session_state['manual_search_mode'] = 'search'
        self.mock_session_state['manual_search_expanded'] = True
        self.mock_session_state['selected_row'] = 0
        
        # Mock length of dataframe
        def mock_len(df):
            return 2
        len_patcher = patch('len', mock_len)
        len_patcher.start()
        
        # Configure mock components
        self.mock_st_button.side_effect = [True, False]  # Search button returns True
        self.mock_st_text_input.side_effect = ['Test Book', 'Test Author']
        
        # Mock library service search
        self.mock_library_service.manual_search_book.return_value = self.sample_results
        
        # Test rendering search section in search mode
        render_manual_search_section(
            self.mock_df,
            'test.csv',
            self.mock_library_service
        )
        
        # Verify text inputs were created
        self.mock_st_text_input.assert_any_call("Título para busca:", value="Test Book", key="search_title")
        self.mock_st_text_input.assert_any_call("Autor para busca:", value="Test Author", key="search_author")
        
        # Verify buttons were created
        self.mock_st_button.assert_any_call("Buscar", key="search_button")
        
        # Verify manual search was called
        self.mock_library_service.manual_search_book.assert_called_once_with('Test Book', 'Test Author')
        
        # Verify state was updated
        self.assertEqual(self.mock_session_state['search_results'], self.sample_results)
        self.assertEqual(self.mock_session_state['manual_search_mode'], 'results')
        
        # Verify page was rerun
        self.mock_st_rerun.assert_called_once()
        
        # Clean up
        len_patcher.stop()

if __name__ == '__main__':
    unittest.main()