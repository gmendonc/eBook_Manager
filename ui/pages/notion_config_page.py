import streamlit as st
import json
import os
from typing import Dict, Any, Optional
from core.interfaces.exporter import Exporter
from adapters.notion_adapter import NotionExporter

from utils.notion_utils import (
    load_notion_config, 
    save_notion_config, 
    test_notion_connection,
    load_export_history,
    add_export_to_history,
    configure_notion_exporter
)

def render_notion_config_page(library_service, app_state):
    """
    Renderiza a página de configuração da integração com o Notion.
    
    Args:
        library_service: Serviço da biblioteca
        app_state: Estado da aplicação
    """
    st.markdown('<div class="main-header">🔗 Configuração do Notion</div>', unsafe_allow_html=True)
    
    # Carregar configurações existentes
    config = load_notion_config()
    
    with st.container():
        st.markdown("""
        ### Sobre a Integração com o Notion
        
        Esta funcionalidade permite exportar sua biblioteca de ebooks para o Notion, criando um banco de 
        dados organizado com capas, metadados e descrições dos livros.
        
        Para configurar a integração, você precisará:
        
        1. Um **token de integração** do Notion (obtido no [site de desenvolvedores do Notion](https://www.notion.so/my-integrations))
        2. O **ID do banco de dados** que você deseja usar (ou deixe em branco para criar um novo)
        """)
    
    # Formulário de configuração
    with st.form("notion_config_form"):
        # Token de integração
        token = st.text_input(
            "Token de Integração do Notion", 
            value=config.get("token", ""),
            type="password",
            help="Você pode obter um token de integração em https://www.notion.so/my-integrations"
        )
        
        # ID do banco de dados
        database_id = st.text_input(
            "ID do Banco de Dados (opcional)", 
            value=config.get("database_id", ""),
            help="Deixe em branco para criar um novo banco de dados durante a primeira exportação"
        )
        
        # Opções avançadas
        with st.expander("Opções Avançadas"):
            # Opções para criação de páginas
            st.subheader("Opções de Conteúdo")
            include_cover = st.checkbox(
                "Incluir capa como ícone da página", 
                value=config.get("include_cover", True),
                help="A capa do livro será exibida como ícone da página no Notion"
            )
            
            include_description = st.checkbox(
                "Incluir descrição/sumário", 
                value=config.get("include_description", True),
                help="A descrição ou sumário do livro será incluído no conteúdo da página"
            )
            
            include_preview_link = st.checkbox(
                "Incluir link para prévia", 
                value=config.get("include_preview_link", True),
                help="Um link para a prévia do livro (no Google Books) será incluído na página"
            )
            
            # Opções de campos
            st.subheader("Campos no Banco de Dados")
            include_publisher = st.checkbox(
                "Incluir campo Editora", 
                value=config.get("include_publisher", True)
            )
            
            include_publication_date = st.checkbox(
                "Incluir campo Data de Publicação", 
                value=config.get("include_publication_date", True)
            )
            
            include_isbn = st.checkbox(
                "Incluir campo ISBN", 
                value=config.get("include_isbn", True)
            )
            
            include_page_count = st.checkbox(
                "Incluir campo Número de Páginas", 
                value=config.get("include_page_count", True)
            )
            
            include_language = st.checkbox(
                "Incluir campo Idioma", 
                value=config.get("include_language", True)
            )
            
            # Opções para status de leitura padrão
            st.subheader("Status de Leitura Padrão")
            default_reading_status = st.selectbox(
                "Status de leitura inicial para novos livros",
                options=["Não Lido", "Para Ler", "Lendo", "Lido", "Referência"],
                index=0 if not config.get("default_reading_status") else 
                      ["Não Lido", "Para Ler", "Lendo", "Lido", "Referência"].index(config.get("default_reading_status"))
            )
        
        # Botão para salvar configurações
        submitted = st.form_submit_button("Salvar Configurações")
        
    if submitted:
        # Criar objeto com as configurações
        new_config = {
            "token": token,
            "database_id": database_id,
            "include_cover": include_cover,
            "include_description": include_description,
            "include_preview_link": include_preview_link,
            "include_publisher": include_publisher,
            "include_publication_date": include_publication_date,
            "include_isbn": include_isbn,
            "include_page_count": include_page_count,
            "include_language": include_language,
            "default_reading_status": default_reading_status
        }
            
        # Salvar configurações
        save_notion_config(new_config)
            
        # Configurar exportador no serviço
        configure_notion_exporter(library_service, new_config)
            
        st.success("Configurações do Notion salvas com sucesso!")
            
        # Oferecer opção para testar a conexão
        if st.button("Testar Conexão"):
            if test_notion_connection(new_config):
                st.success("Conexão com o Notion estabelecida com sucesso!")
            else:
                st.error("Falha ao conectar com o Notion. Verifique o token de integração.")
    
    # Seção de instruções
    with st.expander("Como configurar a integração com o Notion"):
        st.markdown("""
        ### Passo a passo para configurar a integração com o Notion
        
        #### 1. Criar uma integração no Notion
        
        1. Acesse [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
        2. Clique em "+ Nova integração"
        3. Dê um nome para sua integração (ex: "Biblioteca de Ebooks")
        4. Selecione o workspace onde você quer usar a integração
        5. Em "Recursos", certifique-se de marcar:
           - "Conteúdo de leitura" 
           - "Conteúdo de inserção"
           - "Atualização de conteúdo"
        6. Clique em "Enviar" para criar a integração
        7. Copie o "Token interno" que aparecerá na tela
        
        #### 2. Permitir acesso à página do Notion
        
        1. Abra o Notion e navegue até a página onde você deseja criar seu banco de dados de ebooks
        2. Clique nos três pontos (...) no canto superior direito
        3. Selecione "Adicionar conexões"
        4. Encontre sua integração na lista e clique em "Confirmar"
        
        #### 3. Configurar esta integração
        
        1. Cole o token no campo "Token de Integração do Notion" acima
        2. Se quiser usar um banco de dados existente, forneça o ID. Caso contrário, deixe em branco
        3. Ajuste as opções avançadas conforme desejado
        4. Clique em "Salvar Configurações"
        
        #### 4. Como obter o ID de um banco de dados existente
        
        Se você já tem um banco de dados no Notion que deseja usar:
        
        1. Abra o banco de dados no Notion
        2. Na URL, o ID é a parte longa após o nome do workspace e antes de qualquer sinal de interrogação
           - Exemplo: https://www.notion.so/workspace/83c75a39f33b4a7b98c40a66bdf7d166?v=...
           - Neste caso, o ID é: 83c75a39f33b4a7b98c40a66bdf7d166
        """)
    
    # Histórico de exportações
    with st.expander("Histórico de Exportações"):
        # Recuperar histórico (implementação simplificada)
        export_history = load_export_history()
        
        if not export_history:
            st.info("Nenhuma exportação realizada ainda.")
        else:
            for entry in export_history:
                st.markdown(f"""
                **Data:** {entry['date']}  
                **Arquivo:** {entry['file']}  
                **Itens exportados:** {entry['items']}  
                **Status:** {'✅ Sucesso' if entry['success'] else '❌ Falha'}
                """)
                
                if not entry['success'] and entry.get('error'):
                    st.error(f"Erro: {entry['error']}")
                    
                st.markdown("---")

