import streamlit as st
import os
import pandas as pd
from datetime import datetime

def render_home_page(library_service, app_state):
    """
    Renders the home page with summary information and quick actions.
    
    Args:
        library_service: Service for managing the library
        app_state: Application state manager
    """
    st.markdown('<div class="main-header">📚 Gerenciador de Biblioteca de Ebooks</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Esta aplicação permite gerenciar sua biblioteca de ebooks de várias fontes, 
    enriquecer metadados, visualizar estatísticas e integrar com outras ferramentas.
    """)
    
    # Dashboard rápido - resumo da biblioteca
    st.markdown('<div class="section-header">📊 Resumo da Biblioteca</div>', unsafe_allow_html=True)
    
    # Encontrar arquivos CSV recentes
    csv_files = [f for f in os.listdir() if f.endswith('.csv') and os.path.isfile(f)]
    
    if csv_files:
        # Ordenar por data de modificação (mais recente primeiro)
        csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Verificar se há arquivos enriquecidos
        enriched_files = [f for f in csv_files if 'enriched' in f]
        if enriched_files:
            latest_file = enriched_files[0]
        else:
            latest_file = csv_files[0]
        
        try:
            df = pd.read_csv(latest_file)
            
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
                    
            st.caption(f"Dados do arquivo: {latest_file}")
            
            # Link para visualização completa
            if st.button("Ver Dashboard Completo"):
                app_state.change_page("dashboard")
                st.rerun()
                
        except Exception as e:
            st.warning(f"Não foi possível carregar o resumo da biblioteca: {str(e)}")
    else:
        st.info("Nenhum dado disponível. Escaneie suas fontes de ebooks para visualizar estatísticas.")
    
    # Fontes configuradas
    st.markdown('<div class="section-header">📂 Fontes Configuradas</div>', unsafe_allow_html=True)
    
    sources = library_service.get_sources()
    if sources:
        for source in sources:
            last_scan = source.last_scan
            last_scan_str = last_scan.strftime('%Y-%m-%d %H:%M:%S') if last_scan else "Nunca"
                    
            st.markdown(f"""
            <div class="info-card">
                <h3>{source.name}</h3>
                <p><strong>Tipo:</strong> {source.type}</p>
                <p><strong>Caminho:</strong> {source.path}</p>
                <p><strong>Último escaneamento:</strong> {last_scan_str}</p>
            </div>
            """, unsafe_allow_html=True)
            
        if st.button("Configurar Fontes"):
            app_state.change_page("setup")
            st.rerun()
    else:
        st.warning("Nenhuma fonte configurada.")
        if st.button("Adicionar Fontes"):
            app_state.change_page("setup")
            st.rerun()
    
    # Links rápidos
    st.markdown('<div class="section-header">🔗 Ações Rápidas</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Escanear Fontes"):
            app_state.change_page("scan")
            st.rerun()
            
    with col2:
        if st.button("Visualizar Biblioteca"):
            app_state.change_page("view")
            st.rerun()
            
    with col3:
        if st.button("Executar Fluxo Completo"):
            app_state.change_page("workflow")
            st.rerun()