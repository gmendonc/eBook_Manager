import json
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from core.domain.source import Source

class ConfigRepository:
    """Repositório para gerenciar configurações do aplicativo."""
    
    def __init__(self, config_path: str = "ebook_manager_config.json"):
        """
        Inicializa o repositório de configuração.
        
        Args:
            config_path: Caminho para o arquivo de configuração
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> Dict[str, Any]:
        """
        Carrega a configuração do arquivo.
        
        Returns:
            Dicionário com as configurações ou configuração padrão se não existir
        """
        if not os.path.exists(self.config_path):
            return self.create_default_config()
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Converter dados de fontes para objetos Source
            if 'sources' in config and isinstance(config['sources'], list):
                config['sources'] = [Source.from_dict(source) for source in config['sources']]
                
            self.logger.info(f"Configuração carregada: {len(config.get('sources', []))} fontes")
            return config
                
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração: {str(e)}")
            return self.create_default_config()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Salva a configuração no arquivo.
        
        Args:
            config: Dicionário com as configurações
            
        Returns:
            True se a configuração foi salva com sucesso
        """
        try:
            # Preparar para serialização
            serializable_config = dict(config)
            
            # Converter objetos Source para dicionários
            if 'sources' in serializable_config:
                sources_list = serializable_config['sources']
                # Check if sources is a non-empty list containing Source objects
                if (isinstance(sources_list, list) and sources_list and hasattr(sources_list[0], 'to_dict')):
                    serializable_config['sources'] = [
                        source.to_dict() for source in sources_list
                    ]
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_config, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"Configuração salva em {self.config_path}")
            return True
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar configuração: {str(e)}")
            return False
    
    def create_default_config(self) -> Dict[str, Any]:
        """
        Cria uma configuração padrão.
        
        Returns:
            Dicionário com a configuração padrão
        """
        config = {
            'sources': [],
            'taxonomy_path': "taxonomia_temas.json"
        }
        
        self.save_config(config)
        self.logger.info("Configuração padrão criada")
        return config
    
    def get_sources(self) -> List[Source]:
        """
        Obtém a lista de fontes configuradas.
        
        Returns:
            Lista de objetos Source
        """
        config = self.load_config()
        return config.get('sources', [])
    
    def get_source_by_id(self, source_id: str) -> Optional[Source]:
        """
        Obtém uma fonte pelo ID.
        
        Args:
            source_id: ID da fonte
            
        Returns:
            Objeto Source ou None se não encontrado
        """
        for source in self.get_sources():
            if source.id == source_id:
                return source
        return None
    
    def get_source_by_name(self, source_name: str) -> Optional[Source]:
        """
        Obtém uma fonte pelo nome.
        
        Args:
            source_name: Nome da fonte
            
        Returns:
            Objeto Source ou None se não encontrado
        """
        for source in self.get_sources():
            if source.name == source_name:
                return source
        return None
    
    def add_source(self, source: Source) -> bool:
        """
        Adiciona uma nova fonte à configuração.
        
        Args:
            source: Objeto Source para adicionar
            
        Returns:
            True se a fonte foi adicionada com sucesso
        """
        config = self.load_config()
        sources = config.get('sources', [])
        
        # Verificar se já existe uma fonte com este nome
        for i, existing_source in enumerate(sources):
            if existing_source.name == source.name:
                # Atualizar fonte existente
                sources[i] = source
                config['sources'] = sources
                return self.save_config(config)
        
        # Adicionar nova fonte
        sources.append(source)
        config['sources'] = sources
        return self.save_config(config)
    
    def remove_source(self, source_name: str) -> bool:
        """
        Remove uma fonte da configuração.
        
        Args:
            source_name: Nome da fonte a remover
            
        Returns:
            True se a fonte foi removida com sucesso
        """
        config = self.load_config()
        sources = config.get('sources', [])
        
        for i, source in enumerate(sources):
            if source.name == source_name:
                del sources[i]
                config['sources'] = sources
                return self.save_config(config)
                
        self.logger.warning(f"Fonte '{source_name}' não encontrada")
        return False
    
    def update_source_scan_time(self, source_id: str) -> bool:
        """
        Atualiza o timestamp de último escaneamento de uma fonte.
        
        Args:
            source_id: ID da fonte
            
        Returns:
            True se a atualização foi bem-sucedida
        """
        config = self.load_config()
        sources = config.get('sources', [])
        
        for i, source in enumerate(sources):
            if source.id == source_id:
                sources[i].last_scan = datetime.now()
                config['sources'] = sources
                return self.save_config(config)
                
        return False
    
    def get_taxonomy_path(self) -> str:
        """
        Obtém o caminho do arquivo de taxonomia.
        
        Returns:
            Caminho para o arquivo de taxonomia
        """
        config = self.load_config()
        return config.get('taxonomy_path', "taxonomia_temas.json")
    
    def set_taxonomy_path(self, path: str) -> bool:
        """
        Define o caminho do arquivo de taxonomia.
        
        Args:
            path: Novo caminho para o arquivo de taxonomia
            
        Returns:
            True se a atualização foi bem-sucedida
        """
        config = self.load_config()
        config['taxonomy_path'] = path
        return self.save_config(config)