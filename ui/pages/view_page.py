import streamlit as st
import os
import pandas as pd
import re
from datetime import datetime

def render_view_page(library_service, app_state):
    """
    Renders the view page for browsing the ebook library.
    
    Args:
        library_service: Service for managing the library
        app_state: Application state manager
    """
    st.markdown('<div class="main-header">📋 Visualizar Biblioteca</div>', unsafe_allow_html=True)
    
    # Encontrar arquivos CSV
    csv_files = [f for f in os.listdir() if f.endswith('.csv') and os.path.isfile(f)]
    
    if not csv_files:
        st.warning("Nenhum arquivo CSV encontrado. Escaneie suas fontes primeiro.")
        if st.button("Ir para Escaneamento"):
            app_state.change_page("scan")
            st.rerun()
    else:
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
                if st.button("Exportar para Notion"):
                    with st.spinner("Exportando para Notion..."):
                        success = library_service.export_to_notion(selected_file)
                        if success:
                            st.success("Exportação para Notion concluída com sucesso!")
                        else:
                            st.error("Erro ao exportar para Notion.")
            
            with col3:
                if st.button("Ver Dashboard"):
                    app_state.set_last_processed_file(selected_file)
                    app_state.change_page("dashboard")
                    st.rerun()
        
        except Exception as e:
            st.error(f"Erro ao carregar o arquivo: {str(e)}")