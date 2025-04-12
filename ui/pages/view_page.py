import streamlit as st
import os
import pandas as pd
import re
from datetime import datetime
import logging

from utils.notion_utils import (
    load_notion_config, 
    save_notion_config, 
    test_notion_connection,
    load_export_history,
    add_export_to_history,
    configure_notion_exporter
)
from ui.components.notion_export_component import integrate_with_view_page

def init_manual_search_state():
    """Inicializa os estados relacionados à busca manual."""
    if 'manual_search_mode' not in st.session_state:
        st.session_state.manual_search_mode = 'select'  # Modos: select, search, results
    if 'selected_row' not in st.session_state:
        st.session_state.selected_row = 0
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'manual_search_expanded' not in st.session_state:
        st.session_state.manual_search_expanded = False

def set_search_mode(mode):
    """Define o modo de busca."""
    st.session_state.manual_search_mode = mode
    
def display_book_search_results(results, csv_path, library_service):
    """
    Exibe os resultados da busca e permite a seleção.
    
    Args:
        results: Lista de resultados da busca
        csv_path: Caminho do arquivo CSV
        library_service: Serviço da biblioteca
    """
    st.write("### Resultados da Busca")
    
    if not results:
        st.warning("Nenhum resultado encontrado. Tente modificar os termos de busca.")
        if st.button("Voltar à Busca"):
            st.session_state.manual_search_mode = 'search'
            st.experimental_rerun()
        return
        
    st.write("Selecione o resultado que melhor corresponde ao seu livro:")
    
    # Exibir cada resultado com um botão de seleção
    for i, result in enumerate(results):
        with st.container():
            cols = st.columns([3, 1])
            with cols[0]:
                st.subheader(result.get('title', 'Título Desconhecido'))
                if result.get('subtitle'):
                    st.write(f"*{result['subtitle']}*")
                st.write(f"**Autor:** {result.get('authors', 'Desconhecido')}")
                st.write(f"**Editora:** {result.get('publisher', 'Desconhecida')}")
                st.write(f"**Publicação:** {result.get('published_date', 'Desconhecida')}")
                st.write(f"**Confiança:** {result.get('confidence', 0):.2f}")
                
                # Mostrar mais detalhes
                with st.expander("Mais detalhes"):
                    if result.get('isbn_13') or result.get('isbn_10'):
                        st.write(f"**ISBN:** {result.get('isbn_13', '')} {result.get('isbn_10', '')}")
                    if result.get('categories'):
                        st.write(f"**Categorias:** {result['categories']}")
                    if result.get('page_count'):
                        st.write(f"**Páginas:** {result['page_count']}")
                    if result.get('language'):
                        st.write(f"**Idioma:** {result['language']}")
                    if result.get('preview_link'):
                        st.write(f"**Preview:** [Link]({result['preview_link']})")
                    if result.get('volume_id'):
                        st.write(f"**ID do Volume:** {result['volume_id']}")
            
            with cols[1]:
                # Exibir capa se disponível
                if result.get('cover_link'):
                    st.image(result['cover_link'], width=150)
                
                # Botão de seleção
                if st.button(f"Selecionar", key=f"select_{i}"):
                    with st.spinner("Atualizando metadados..."):
                        success = library_service.update_book_metadata(
                            csv_path,
                            st.session_state.selected_row,
                            result
                        )
                        
                        if success:
                            st.success("Metadados atualizados com sucesso!")
                            # Resetar para o modo de seleção
                            st.session_state.manual_search_mode = 'select'
                            st.session_state.search_results = []
                            st.session_state.manual_search_expanded = False
                            st.experimental_rerun()
                        else:
                            st.error("Falha ao atualizar metadados.")
            
            st.markdown("---")
    
    # Botão para cancelar
    if st.button("Cancelar", key="cancel_results"):
        st.session_state.manual_search_mode = 'select'
        st.session_state.search_results = []
        st.experimental_rerun()

def render_manual_search_section(df, selected_file, library_service):
    """
    Renderiza a seção de busca manual.
    
    Args:
        df: DataFrame com os dados dos ebooks
        selected_file: Caminho do arquivo CSV selecionado
        library_service: Serviço da biblioteca
    """
    # Inicializar estados para busca manual
    init_manual_search_state()
    
    # Se modo de resultados, mostrar apenas resultados
    if st.session_state.manual_search_mode == 'results':
        display_book_search_results(
            st.session_state.search_results,
            selected_file,
            library_service
        )
        return
    
    # Seção de busca manual
    with st.expander("🔍 Enriquecimento Manual", expanded=st.session_state.manual_search_expanded):
        st.session_state.manual_search_expanded = True
        
        # Modo de seleção - escolher um livro para enriquecer
        if st.session_state.manual_search_mode == 'select':
            st.write("Selecione um livro para busca manual no Google Books:")
            
            # Lista de índices com formatação legível
            if len(df) > 0:
                format_func = lambda i: f"{i}: {df.iloc[i].get('Titulo_Extraido', '') or df.iloc[i].get('Nome', '').split('.')[0]}"
                selected_index = st.selectbox(
                    "Livro:",
                    list(range(len(df))),
                    format_func=format_func,
                    index=min(st.session_state.selected_row, len(df)-1) if len(df) > 0 else 0,
                    key="book_selection"
                )
                
                # Exibir informações do livro selecionado
                if selected_index is not None:
                    selected_book = df.iloc[selected_index]
                    st.write("### Informações do Livro")
                    
                    # Título e Autor
                    titulo = selected_book.get('Titulo_Extraido', '') or selected_book.get('Nome', '').split('.')[0]
                    autor = selected_book.get('Autor_Extraido', 'Desconhecido')
                    
                    st.write(f"**Título:** {titulo}")
                    st.write(f"**Autor:** {autor}")
                    
                    # Informações adicionais se disponíveis
                    formato = selected_book.get('Formato', '')
                    if formato:
                        st.write(f"**Formato:** {formato}")
                    
                    # Botão para iniciar a busca
                    if st.button("Buscar no Google Books", key="start_search"):
                        st.session_state.selected_row = selected_index
                        st.session_state.manual_search_mode = 'search'
                        st.experimental_rerun()
            else:
                st.warning("Nenhum livro disponível para seleção.")
        
        # Modo de busca - realizar busca e mostrar resultados
        elif st.session_state.manual_search_mode == 'search':
            selected_index = st.session_state.selected_row
            
            # Verificar se o índice é válido
            if selected_index < 0 or selected_index >= len(df):
                st.error("Livro selecionado inválido.")
                st.session_state.manual_search_mode = 'select'
                st.experimental_rerun()
                return
                
            selected_book = df.iloc[selected_index]
            
            st.write("### Busca Manual no Google Books")
            
            # Extrair título e autor do livro selecionado
            default_title = selected_book.get('Titulo_Extraido', '')
            if not default_title:
                default_title = selected_book.get('Nome', '').split('.')[0]
            
            default_author = selected_book.get('Autor_Extraido', '')
            
            # Campos para editar termos de busca
            search_title = st.text_input("Título para busca:", value=default_title, key="search_title")
            search_author = st.text_input("Autor para busca:", value=default_author, key="search_author")
            
            # Botões de ação
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Buscar", key="search_button"):
                    if not search_title.strip():
                        st.error("Por favor, informe um título para busca.")
                    else:
                        with st.spinner("Buscando no Google Books..."):
                            results = library_service.manual_search_book(search_title, search_author)
                            
                            if not results:
                                st.warning("Nenhum resultado encontrado no Google Books.")
                            else:
                                st.session_state.search_results = results
                                st.session_state.manual_search_mode = 'results'
                                st.experimental_rerun()
            with col2:
                if st.button("Cancelar", key="search_cancel"):
                    st.session_state.manual_search_mode = 'select'
                    st.experimental_rerun()

def render_view_page(library_service, app_state):
    """Renderiza a página de visualização da biblioteca."""
    # Configuração do logger
    logger = logging.getLogger(__name__)
    
    st.markdown('<div class="main-header">📋 Visualizar Biblioteca</div>', unsafe_allow_html=True)
    
    # Encontrar arquivos CSV
    csv_files = [f for f in os.listdir() if f.endswith('.csv') and os.path.isfile(f)]
    
    if not csv_files:
        st.warning("Nenhum arquivo CSV encontrado. Escaneie suas fontes primeiro.")
        if st.button("Ir para Escaneamento"):
            app_state.change_page("scan")
            st.rerun()
        return
    
    # Ordenar por data de modificação (mais recente primeiro)
    csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # Priorizar o último arquivo processado, se houver
    if app_state.last_processed_file in csv_files:
        default_index = csv_files.index(app_state.last_processed_file)
    else:
        default_index = 0
        
    selected_file = st.selectbox(
        "Selecione um arquivo para visualizar", 
        csv_files,
        index=default_index
    )
    
    try:
        df = pd.read_csv(selected_file)
        
        # Informações básicas
        st.markdown('<div class="section-header">📊 Informações Básicas</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Ebooks", len(df))
        
        with col2:
            if 'Tamanho(MB)' in df.columns:
                df['Tamanho(MB)'] = pd.to_numeric(df['Tamanho(MB)'], errors='coerce')
                total_size = df['Tamanho(MB)'].sum()
                st.metric("Tamanho Total", f"{total_size:.2f} MB")
            else:
                st.metric("Tamanho Total", "N/D")
        
        with col3:
            if 'Autor' in df.columns or 'Autor_Extraido' in df.columns:
                autor_col = 'Autor' if 'Autor' in df.columns else 'Autor_Extraido'
                unique_authors = df[autor_col].nunique()
                st.metric("Autores Únicos", unique_authors)
            else:
                st.metric("Autores Únicos", "N/D")
        
        # Render manual search section
        render_manual_search_section(df, selected_file, library_service)
        
        # Visualização dos dados
        st.markdown('<div class="section-header">📋 Dados</div>', unsafe_allow_html=True)
        
        # Opções de filtro
        st.markdown('<div class="subsection-header">🔍 Filtros</div>', unsafe_allow_html=True)
        
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            if 'Formato' in df.columns:
                formats = ['Todos'] + sorted(df['Formato'].dropna().unique().tolist())
                selected_format = st.selectbox("Formato", formats)
                if selected_format != 'Todos':
                    df = df[df['Formato'] == selected_format]
        
        with filter_col2:
            author_col = None
            if 'Autor' in df.columns:
                author_col = 'Autor'
            elif 'Autor_Extraido' in df.columns:
                author_col = 'Autor_Extraido'
                
            if author_col:
                authors = ['Todos'] + sorted(df[author_col].dropna().unique().tolist())
                selected_author = st.selectbox("Autor", authors)
                if selected_author != 'Todos':
                    df = df[df[author_col] == selected_author]
        
        with filter_col3:
            if 'Temas' in df.columns:
                # Extrair temas únicos de toda a coluna
                all_themes = set()
                for themes in df['Temas'].dropna():
                    if isinstance(themes, str):
                        theme_list = re.split(r'[,;]', themes)
                        all_themes.update([t.strip() for t in theme_list if t.strip()])
                
                if all_themes:
                    themes = ['Todos'] + sorted(all_themes)
                    selected_theme = st.selectbox("Tema", themes)
                    if selected_theme != 'Todos':
                        df = df[df['Temas'].str.contains(selected_theme, na=False)]
        
        # Adicionar filtro para status de busca do Google Books
        if 'GB_Status_Busca' in df.columns:
            gb_statuses = ['Todos'] + sorted(df['GB_Status_Busca'].dropna().unique().tolist())
            selected_status = st.selectbox("Status Google Books", gb_statuses)
            if selected_status != 'Todos':
                df = df[df['GB_Status_Busca'] == selected_status]
        
        # Exibir dados
        st.dataframe(df, use_container_width=True)
        
        # Opção para download
        st.download_button(
            label="📥 Download como CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f"biblioteca_ebooks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # Opções adicionais
        st.markdown('<div class="section-header">🔧 Opções Adicionais</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Enriquecer Dados"):
                with st.spinner("Enriquecendo dados..."):
                    enriched_path = library_service.enrich_csv(selected_file)
                    if enriched_path:
                        # Show toast notification
                        st.toast("✅ Enriquecimento concluído!", icon="✅")
                        st.success(f"Dados enriquecidos! Arquivo: {enriched_path}")
                        app_state.set_last_processed_file(enriched_path)
                        # Recarregar a página para mostrar o novo arquivo
                        st.rerun()
                    else:
                        st.error("Erro ao enriquecer dados.")
        
        with col2:
            # 1. Adicionar variável de controle no session_state se não existir
            if "show_notion_export_panel" not in st.session_state:
                st.session_state.show_notion_export_panel = False
            if st.button("Exportar para Notion"):
                st.write("DEBUG: Botão Exportar para Notion clicado")
                print("DEBUG: Botão Exportar para Notion clicado") # Print no console
                logger.info("Iniciando exportação para o Notion.")
                st.session_state.show_notion_export_panel = True
            # 3. Mostrar o painel de exportação se o estado indicar que deve ser mostrado
            if st.session_state.show_notion_export_panel:
                
                # Importar o repositório de configuração
                from core.repositories.notion_config_repository import NotionConfigRepository
        
                # Carregar a configuração do repositório
                config = NotionConfigRepository.load_config()
                print(f"DEBUG: Configuração carregada: {config}")
        
                # Verificar se temos configuração suficiente
                has_valid_config = (
                    config.get("token") and 
                    (config.get("database_id") or config.get("page_id"))
                )

                with st.expander("Exportação para o Notion", expanded=True):
                    # Botão para fechar o painel
                    if st.button("× Fechar", key="close_notion_panel"):
                        st.session_state.show_notion_export_panel = False
                        st.rerun()
        
                    if not has_valid_config:
                        st.warning("Integração com o Notion não configurada. Por favor, configure primeiro.")
            
                        # Redirecionar para a página de configuração do Notion
                        if st.button("Configurar Notion"):
                            app_state.change_page("notion_config")
                            st.rerun()
                    else:
                        # Mostrar um resumo da configuração atual
                        st.write("**Configuração atual:**")
                        token = config.get("token", "")
                        masked_token = f"{token[:4]}...{token[-4:]}"
                        st.write(f"- Token: {masked_token}")
                
                        if config.get("database_id"):
                            st.write(f"- Base de dados: {config.get('database_id')}")
                        elif config.get("page_id"):
                            st.write(f"- Página para criar base: {config.get('page_id')}")
                            st.write(f"- Nome da base: {config.get('database_name', 'Biblioteca de Ebooks')}")

                        print("DEBUG: Pronto para iniciar exportação") # Print no console
                        # Botão para iniciar a exportação
                        if st.button("Iniciar Exportação", key="start_export"):
                            logger.info("Botão de iniciar exportação clicado")
                            print("DEBUG: Botão iniciar exportação clicado") # Print no console
                            with st.spinner("Exportando para Notion..."):
                                # Preparar configuração completa
                                export_config = {
                                    "token": config.get("token", ""),
                                    "database_id": config.get("database_id", ""),
                                    "page_id": config.get("page_id", ""),
                                    "database_name": config.get("database_name", "Biblioteca de Ebooks"),
                                    "create_database_if_not_exists": bool(config.get("page_id"))
                                }

                                # Log antes de chamar a exportação
                                print(f"DEBUG: Chamando export_to_notion com config: {export_config}")

                                try:                    
                                    # Executar a exportação
                                    success = library_service.export_to_notion(selected_file, export_config)
                        
                                    if success:
                                        st.success("Exportação para Notion concluída com sucesso!")
                                        logger.info("Exportação para o Notion concluída com sucesso.")
                                        print("DEBUG: Exportação para o Notion concluída com sucesso.") # Print no console
                                    else:
                                        st.error("Erro ao exportar para Notion. Verifique os logs para mais detalhes.")
                                        logger.error("Erro durante a exportação para o Notion.")
                                        print("DEBUG: Erro durante a exportação para o Notion.") # Print no console
                                        import traceback
                                        logger.debug("Detalhes do erro:", exc_info=True)
                            
                                        # Mostrar dicas para solução de problemas
                                        st.info("""
                                        **Dicas para solução de problemas:**
                                        1. Verifique se o token de integração está correto
                                        2. Confirme que a página/base de dados foi compartilhada com a integração
                                        3. Verifique se a base de dados tem a estrutura correta
                                        4. Confira os logs para detalhes do erro
                                        """)
                                except Exception as e:
                                    print(f"DEBUG ERROR: {str(e)}")
                                    st.error(f"Erro durante a exportação: {str(e)}")
                        print("DEBUG: Saída da execução do botão de exportação") # Print no console
        
        with col3:
            if st.button("Ver Dashboard"):
                app_state.set_last_processed_file(selected_file)
                app_state.change_page("dashboard")
                st.rerun()
    
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {str(e)}")
        st.rerun()