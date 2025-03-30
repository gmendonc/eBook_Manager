# Criar um arquivo tests/test_enrichers.py

import unittest
import os
import tempfile
import pandas as pd
import shutil
from core.interfaces.enricher import Enricher
from core.services.enrich_service import EnrichService
from adapters.enrichers.basic_enricher import BasicEnricher
from adapters.enrichers.default_enricher import DefaultEnricher
from adapters.enrichers.external_api_enricher import ExternalAPIEnricher

class TestEnrichers(unittest.TestCase):
    def setUp(self):
        # Criar diretório temporário
        self.temp_dir = tempfile.mkdtemp()
        
        # Criar um CSV de teste
        self.test_csv = os.path.join(self.temp_dir, "test_ebooks.csv")
        self.test_data = [
            {
                "Nome": "Author1 - Book1.epub",
                "Formato": "EPUB",
                "Tamanho(MB)": 1.5,
                "Data Modificação": "2023-01-01 10:00:00",
                "Caminho": "/path/to/book1.epub"
            },
            {
                "Nome": "Book2 (Author2).pdf",
                "Formato": "PDF",
                "Tamanho(MB)": 2.5,
                "Data Modificação": "2023-01-02 10:00:00",
                "Caminho": "/path/to/book2.pdf"
            }
        ]
        
        df = pd.DataFrame(self.test_data)
        df.to_csv(self.test_csv, index=False)
        
        # Criar o serviço de enriquecimento
        self.enrich_service = EnrichService()
        
        # Registrar os enriquecedores
        self.basic_enricher = BasicEnricher()
        self.default_enricher = DefaultEnricher()
        self.external_api_enricher = ExternalAPIEnricher()
        
        self.enrich_service.register_enricher('basic', self.basic_enricher)
        self.enrich_service.register_enricher('default', self.default_enricher)
        self.enrich_service.register_enricher('external_api', self.external_api_enricher)
    
    def tearDown(self):
        # Remover diretório temporário
        shutil.rmtree(self.temp_dir)
    
    def test_basic_enricher(self):
        # Ativar o enriquecedor básico
        self.enrich_service.set_active_enricher('basic')
        
        # Enriquecer o CSV
        enriched_path = self.enrich_service.enrich(self.test_csv)
        
        # Verificar se o arquivo foi criado
        self.assertTrue(os.path.exists(enriched_path))
        
        # Carregar o CSV enriquecido
        df = pd.read_csv(enriched_path)
        
        # Verificar se os dados foram enriquecidos corretamente
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['Autor_Extraido'], 'Author1')
        self.assertEqual(df.iloc[0]['Titulo_Extraido'], 'Book1')
        self.assertEqual(df.iloc[1]['Autor_Extraido'], 'Author2')
        self.assertEqual(df.iloc[1]['Titulo_Extraido'], 'Book2')
    
    def test_set_active_enricher(self):
        # Verificar se o enriquecedor ativo é definido corretamente
        self.enrich_service.set_active_enricher('basic')
        self.assertEqual(self.enrich_service.active_enricher_name, 'basic')
        
        self.enrich_service.set_active_enricher('default')
        self.assertEqual(self.enrich_service.active_enricher_name, 'default')
        
        # Tentar definir um enriquecedor inexistente
        result = self.enrich_service.set_active_enricher('nonexistent')
        self.assertFalse(result)
        self.assertEqual(self.enrich_service.active_enricher_name, 'default')
    
    def test_get_available_enrichers(self):
        # Verificar se os enriquecedores disponíveis são retornados corretamente
        available = self.enrich_service.get_available_enrichers()
        self.assertEqual(set(available), {'basic', 'default', 'external_api'})

if __name__ == '__main__':
    unittest.main()