import logging
import time
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import pandas as pd
from core.domain.source import Source
from core.repositories.config_repository import ConfigRepository
from core.services.credential_service import CredentialService
from core.services.scan_service import ScanService
from core.services.enrich_service import EnrichService
from core.services.export_service import ExportService

class LibraryService:
    """Serviço principal da biblioteca de ebooks."""
    
    def __init__(
        self, 
        config_repository: ConfigRepository,
        credential_service: CredentialService,
        scan_service: ScanService,
        enrich_service: EnrichService,
        export_service: ExportService
    ):
        """
        Inicializa o serviço da biblioteca.
        
        Args:
            config_repository: Repositório de configuração
            credential_service: Serviço de credenciais
            scan_service: Serviço de escaneamento
            enrich_service: Serviço de enriquecimento
            export_service: Serviço de exportação
        """
        self.config_repository = config_repository
        self.credential_service = credential_service
        self.scan_service = scan_service
        self.enrich_service = enrich_service
        self.export_service = export_service
        self.logger = logging.getLogger(__name__)
    
    def get_sources(self) -> List[Source]:
        """
        Obtém a lista de fontes configuradas.
        
        Returns:
            Lista de objetos Source
        """
        return self.config_repository.get_sources()
    
    def get_source_by_name(self, source_name: str) -> Optional[Source]:
        """
        Obtém uma fonte pelo nome.
        
        Args:
            source_name: Nome da fonte
            
        Returns:
            Objeto Source ou None se não encontrado
        """
        return self.config_repository.get_source_by_name(source_name)
    
    def add_source(self, name: str, type_name: str, path: str, config: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Adiciona uma nova fonte com tratamento seguro de credenciais.
        
        Args:
            name: Nome da fonte
            type_name: Tipo de fonte (icloud, filesystem, dropbox, kindle)
            path: Caminho da fonte
            config: Configurações específicas
            
        Returns:
            Tupla com (ID da fonte, credenciais temporárias)
        """
        # Gerar ID único para a fonte
        source_id = f"{name}_{int(time.time())}"
        
        # Configuração limpa para armazenamento
        clean_config = config.copy() if config else {}
        
        # Credenciais temporárias que não serão armazenadas na configuração
        temp_credentials = {}
        
        # Tratar caso especial do iCloud
        if type_name == "icloud" and config:
            # Extrair credenciais antes de salvar na configuração
            username = config.get("username")
            password = config.get("password")
            save_credentials = config.get("save_credentials", False)
            
            # Remover credenciais da configuração que será salva
            if "username" in clean_config:
                del clean_config["username"]
            if "password" in clean_config:
                del clean_config["password"]
            if "save_credentials" in clean_config:
                del clean_config["save_credentials"]
            
            if username and password and save_credentials:
                # Salvar credenciais no serviço seguro
                self.credential_service.save_credentials(source_id, username, password)
                
            # Manter apenas para uso temporário nesta sessão
            if username and password:
                temp_credentials = {"username": username, "password": password}
        
        # Criar objeto Source
        source = Source(
            id=source_id,
            name=name,
            type=type_name,
            path=path,
            config=clean_config
        )
        
        # Adicionar aos sources e salvar
        success = self.config_repository.add_source(source)
        
        if not success:
            self.logger.error(f"Erro ao adicionar fonte '{name}'")
            # Limpar credenciais armazenadas em caso de erro
            if type_name == "icloud":
                self.credential_service.delete_credentials(source_id)
                
        return source_id, temp_credentials
    
    def remove_source(self, source_name: str) -> bool:
        """
        Remove uma fonte e suas credenciais armazenadas.
        
        Args:
            source_name: Nome da fonte
            
        Returns:
            True se a fonte foi removida com sucesso
        """
        source = self.get_source_by_name(source_name)
        if source:
            # Remover credenciais se existirem
            self.credential_service.delete_credentials(source.id)
            
            # Remover fonte da configuração
            return self.config_repository.remove_source(source_name)
            
        return False
    
    def scan_source(self, source_name: str) -> Optional[str]:
        """
        Escaneia uma fonte com suporte a credenciais seguras.
        
        Args:
            source_name: Nome da fonte
            
        Returns:
            Caminho para o arquivo CSV gerado ou None em caso de erro
        """
        source = self.get_source_by_name(source_name)
        if not source:
            self.logger.error(f"Fonte '{source_name}' não encontrada")
            return None
        
        # Realizar escaneamento
        csv_path = self.scan_service.scan_source(source)
        
        # Atualizar timestamp de último escaneamento
        if csv_path:
            self.config_repository.update_source_scan_time(source.id)
            
        return csv_path
    
    def scan_all_sources(self) -> List[str]:
        """
        Escaneia todas as fontes configuradas.
        
        Returns:
            Lista de caminhos para os arquivos CSV gerados
        """
        csv_paths = []
        for source in self.get_sources():
            csv_path = self.scan_source(source.name)
            if csv_path:
                csv_paths.append(csv_path)
                
        return csv_paths
    
    # Enrichers
    def get_available_enrichers(self) -> List[str]:
        """
        Obtém a lista de enriquecedores disponíveis.
    
        Returns:
            Lista de nomes de enriquecedores
        """
        return self.enrich_service.get_available_enrichers()

    def get_active_enricher_name(self) -> Optional[str]:
        """
        Obtém o nome do enriquecedor ativo.

        Returns:
            Nome do enriquecedor ativo ou None se nenhum estiver ativo
        """
        return self.enrich_service.active_enricher_name

    def set_active_enricher(self, name: str) -> bool:
        """
        Define o enriquecedor ativo.

        Args:
            name: Nome do enriquecedor a ser ativado

        Returns:
            True se o enriquecedor foi ativado com sucesso
        """
        return self.enrich_service.set_active_enricher(name)

    def configure_external_api_enricher(self, api_key: str) -> bool:
        """
        Configura o enriquecedor de API externa.
    
        Args:
            api_key: Chave de API para o serviço externo
        
        Returns:
            True se a configuração foi bem-sucedida
        """
        try:
            # Verificar se o enriquecedor está registrado
            if 'external_api' not in self.enrich_service.enricher_registry:
                return False
            
            # Atualizar a chave de API
            enricher = self.enrich_service.enricher_registry['external_api']
            enricher.api_key = api_key
        
            return True
        except Exception as e:
            self.logger.error(f"Erro ao configurar enriquecedor de API externa: {str(e)}")
            return False
    
    def enrich_csv(self, csv_path: str, enricher_name: Optional[str] = None) -> Optional[str]:
        """
        Enriquece os dados de um arquivo CSV.
    
        Args:
            csv_path: Caminho para o arquivo CSV
            enricher_name: Nome do enriquecedor a ser usado (opcional)
        
        Returns:
            Caminho para o CSV enriquecido ou None em caso de erro
        """
        taxonomy_path = self.config_repository.get_taxonomy_path()
        return self.enrich_service.enrich(csv_path, taxonomy_path, enricher_name)
    
    def export_to_notion(self, csv_path: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Exports data to Notion.
        
        Args:
            csv_path: Path to the CSV file
            config: Configuration for Notion export
            
        Returns:
            True if export was successful
        """
        from adapters.notion.factory import NotionExporterFactory
    
        exporter = NotionExporterFactory.create_exporter(config or {})
        return exporter.export(csv_path, config)
    
    def merge_libraries(self, csv_paths: List[str], output_path: Optional[str] = None) -> Optional[str]:
        """
        Mescla várias bibliotecas de ebooks em um único CSV.
        
        Args:
            csv_paths: Lista de caminhos para arquivos CSV
            output_path: Caminho opcional para o arquivo de saída
            
        Returns:
            Caminho para o CSV mesclado ou None em caso de erro
        """
        if not output_path:
            output_path = f"ebooks_merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
        try:
            self.logger.info(f"Mesclando {len(csv_paths)} bibliotecas")
            
            all_ebooks = []
            
            for csv_path in csv_paths:
                try:
                    df = pd.read_csv(csv_path)
                    # Adicionar coluna para identificar a fonte
                    source_name = os.path.basename(csv_path).replace('.csv', '')
                    df['Fonte'] = source_name
                    
                    all_ebooks.append(df)
                except Exception as e:
                    self.logger.warning(f"Erro ao ler {csv_path}: {str(e)}")
            
            if not all_ebooks:
                self.logger.error("Nenhum arquivo CSV válido encontrado")
                return None
                
            # Mesclar todos os DataFrames
            merged_df = pd.concat(all_ebooks, ignore_index=True)
            
            # Remover duplicatas com base no título e autor
            if 'Titulo_Extraido' in merged_df.columns and 'Autor_Extraido' in merged_df.columns:
                merged_df = merged_df.drop_duplicates(subset=['Titulo_Extraido', 'Autor_Extraido'])
            else:
                # Se não tiver esses campos, usar o nome do arquivo
                merged_df = merged_df.drop_duplicates(subset=['Nome'])
                
            # Salvar arquivo mesclado
            merged_df.to_csv(output_path, index=False, encoding='utf-8')
            
            self.logger.info(f"Mesclagem concluída: {len(merged_df)} ebooks únicos salvos em {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Erro ao mesclar bibliotecas: {str(e)}")
            return None
    
    def set_taxonomy_path(self, taxonomy_path: str) -> bool:
        """
        Define o caminho do arquivo de taxonomia.
        
        Args:
            taxonomy_path: Novo caminho para o arquivo de taxonomia
            
        Returns:
            True se a atualização foi bem-sucedida
        """
        return self.config_repository.set_taxonomy_path(taxonomy_path)
    
    def get_taxonomy_path(self) -> str:
        """
        Obtém o caminho do arquivo de taxonomia.
        
        Returns:
            Caminho para o arquivo de taxonomia
        """
        return self.config_repository.get_taxonomy_path()
    
    # Add these methods to the LibraryService class in core/services/library_service.py

    def configure_enricher_api_key(self, enricher_name: str, api_key: str) -> bool:
        """
        Configures an API key for a specific enricher.
    
        This is a generic method that can be used for any enricher that requires an API key.
    
        Args:
            enricher_name: Name of the enricher to configure
            api_key: API key to set
        
        Returns:
            True if the configuration was successful
        """
        try:
            # Verify that the enricher is registered
            if enricher_name not in self.enrich_service.enricher_registry:
                self.logger.error(f"Enricher '{enricher_name}' not registered")
                return False
        
            # Access the enricher from the registry
            enricher = self.enrich_service.enricher_registry[enricher_name]
        
            # Set the API key
            enricher.api_key = api_key
        
            # Save API key in configuration for persistence
            self._save_enricher_config(enricher_name, api_key)
        
            self.logger.info(f"API key configured for {enricher_name} enricher")
            return True
        except Exception as e:
            self.logger.error(f"Error configuring {enricher_name} enricher: {str(e)}")
            return False

    def configure_external_api_enricher(self, api_key: str) -> bool:
        """
        Configures the External API enricher.
    
        Args:
            api_key: API key for the External API
        
        Returns:
            True if the configuration was successful
        """
        return self.configure_enricher_api_key('external_api', api_key)

    def configure_google_books_enricher(self, api_key: str) -> bool:
        """
        Configures the Google Books enricher.
    
        Args:
            api_key: API key for the Google Books API
        
        Returns:
            True if the configuration was successful
        """
        return self.configure_enricher_api_key('google_books', api_key)

    def _save_enricher_config(self, enricher_name: str, api_key: str) -> bool:
        """
        Saves enricher configuration for persistence.
    
        This method saves the API key to the configuration repository
        so it can be retrieved when the application restarts.
    
        Args:
            enricher_name: Name of the enricher
            api_key: API key to save
        
        Returns:
            True if saving was successful
        """
        try:
            # Load current configuration
            config = self.config_repository.load_config()
        
            # Ensure 'enrichers' section exists
            if 'enrichers' not in config:
                config['enrichers'] = {}
        
            # Add or update the API key
            config_key = f"{enricher_name}_api_key"
            config['enrichers'][config_key] = api_key
        
            # Save the updated configuration
            return self.config_repository.save_config(config)
        except Exception as e:
            self.logger.error(f"Error saving enricher configuration: {str(e)}")
            return False
        

    def manual_search_book(self, title: str, author: Optional[str] = None, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Realiza uma busca manual por um livro no Google Books.
        
        Args:
            title: Título do livro a ser buscado
            author: Nome do autor (opcional)
            max_results: Número máximo de resultados a retornar
            
        Returns:
            Lista de dicionários com metadados de livros
        """
        try:
            # Verificar se o GoogleBooksEnricher está disponível
            if 'google_books' not in self.enrich_service.enricher_registry:
                self.logger.error("Google Books enricher não disponível")
                return []
                
            enricher = self.enrich_service.enricher_registry['google_books']
            
            # Buscar livro
            results = enricher.search_book_multiple_results(title, author, max_results)
            
            # Converter objetos BookMetadata para dicionários
            result_dicts = []
            for book in results:
                result_dicts.append({
                    'title': book.title,
                    'subtitle': book.subtitle,
                    'authors': ', '.join(book.authors) if book.authors else '',
                    'publisher': book.publisher,
                    'published_date': book.published_date,
                    'isbn_10': book.isbn_10,
                    'isbn_13': book.isbn_13,
                    'page_count': book.page_count,
                    'categories': ', '.join(book.categories) if book.categories else '',
                    'language': book.language,
                    'preview_link': book.preview_link,
                    'cover_link': book.cover_link,
                    'confidence': book.match_confidence,
                    'volume_id': book.volume_id  # Incluir ID do volume
                })
                
            return result_dicts
        except Exception as e:
            self.logger.error(f"Erro na busca manual de livro: {str(e)}")
            return []

    def get_book_by_id(self, volume_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém metadados de um livro específico do Google Books pelo ID.
        
        Args:
            volume_id: ID do volume no Google Books
            
        Returns:
            Dicionário com metadados do livro ou None se não encontrado
        """
        try:
            # Verificar se o GoogleBooksEnricher está disponível
            if 'google_books' not in self.enrich_service.enricher_registry:
                self.logger.error("Google Books enricher não disponível")
                return None
                
            enricher = self.enrich_service.enricher_registry['google_books']
            
            # Obter livro pelo ID
            book = enricher.get_book_by_id(volume_id)
            if not book:
                return None
                
            # Converter objeto BookMetadata para dicionário
            return {
                'title': book.title,
                'subtitle': book.subtitle,
                'authors': ', '.join(book.authors) if book.authors else '',
                'publisher': book.publisher,
                'published_date': book.published_date,
                'isbn_10': book.isbn_10,
                'isbn_13': book.isbn_13,
                'page_count': book.page_count,
                'categories': ', '.join(book.categories) if book.categories else '',
                'language': book.language,
                'preview_link': book.preview_link,
                'cover_link': book.cover_link,
                'confidence': book.match_confidence,
                'volume_id': book.volume_id
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter livro por ID: {str(e)}")
            return None

    def update_book_metadata(self, csv_path: str, row_index: int, metadata: Dict[str, Any]) -> bool:
        """
        Atualiza os metadados de um livro específico em um arquivo CSV.
        
        Args:
            csv_path: Caminho para o arquivo CSV
            row_index: Índice da linha a ser atualizada
            metadata: Novos metadados a serem aplicados
            
        Returns:
            True se a atualização foi bem-sucedida
        """
        try:
            # Ler o arquivo CSV
            df = pd.read_csv(csv_path)
            
            if row_index < 0 or row_index >= len(df):
                self.logger.error(f"Índice de linha inválido: {row_index}")
                return False
                
            # Mapear campos de metadados para colunas do DataFrame
            field_mappings = {
                'title': 'GB_Titulo',
                'subtitle': 'GB_Subtitulo',
                'authors': 'GB_Autores',
                'publisher': 'GB_Editora',
                'published_date': 'GB_Data_Publicacao',
                'isbn_10': 'GB_ISBN10',
                'isbn_13': 'GB_ISBN13',
                'page_count': 'GB_Paginas',
                'categories': 'GB_Categorias',
                'language': 'GB_Idioma',
                'preview_link': 'GB_Preview_Link',
                'cover_link': 'GB_Capa_Link',
                'confidence': 'GB_Confianca_Match',
                'volume_id': 'GB_Volume_ID'
            }
            
            # Atualizar campos
            for src_field, dest_field in field_mappings.items():
                if src_field in metadata and metadata[src_field] is not None:
                    # Garantir que a coluna existe
                    if dest_field not in df.columns:
                        df[dest_field] = None
                        
                    df.at[row_index, dest_field] = metadata[src_field]
            
            # Marcar como busca manual
            if 'GB_Status_Busca' not in df.columns:
                df['GB_Status_Busca'] = None
            df.at[row_index, 'GB_Status_Busca'] = 'Manual'
            
            # Atualizar também campos extraídos para compatibilidade
            if 'Titulo_Extraido' in df.columns and 'title' in metadata:
                df.at[row_index, 'Titulo_Extraido'] = metadata['title']
            if 'Autor_Extraido' in df.columns and 'authors' in metadata:
                df.at[row_index, 'Autor_Extraido'] = metadata['authors']
            
            # Adicionar timestamp de atualização
            if 'GB_Atualizado_Em' not in df.columns:
                df['GB_Atualizado_Em'] = None
            
            from datetime import datetime
            df.at[row_index, 'GB_Atualizado_Em'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Salvar o CSV atualizado
            df.to_csv(csv_path, index=False)
            
            self.logger.info(f"Metadados atualizados para linha {row_index} em {csv_path}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao atualizar metadados do livro: {str(e)}")
            return False