import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional

def render_scan_page(library_service, app_state):
    """
    Renderiza a página de escaneamento.
    
    Args:
        library_service: Serviço da biblioteca
        app_state: Estado da aplicação
    """
    st.markdown('<div class="main-header">🔍 Escanear Fontes</div>', unsafe_allow_html=True)
    
    sources = library_service.get_sources()
    
    if not sources:
        st.warning("Nenhuma fonte configurada.")
        if st.button("Adicionar Fontes"):
            app_state.change_page("setup")
            st.rerun()
        return
    
    st.markdown("""
    Selecione uma fonte para escanear ou escaneie todas as fontes de uma vez.
    O processo pode levar algum tempo dependendo do tamanho da biblioteca.
    """)
    
    # Opção para escanear todas as fontes
    if st.button("Escanear Todas as Fontes"):
        with st.spinner("Escaneando todas as fontes..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            csv_paths = []
            for i, source in enumerate(sources):
                progress = i / len(sources)
                progress_bar.progress(progress)
                status_text.text(f"Escaneando {source.name}...")
                
                csv_path = library_service.scan_source(source.name)
                if csv_path:
                    csv_paths.append(csv_path)
                    app_state.add_scan_result(
                        source.name,
                        True,
                        f"Escaneamento concluído: {csv_path}",
                        csv_path
                    )
                else:
                    app_state.add_scan_result(
                        source.name,
                        False,
                        f"Erro ao escanear {source.name}"
                    )
                    
            progress_bar.progress(1.0)
            status_text.text("Escaneamento concluído!")
            
            if csv_paths:
                st.success(f"Escaneamento concluído para {len(csv_paths)} fontes!")
                
                if len(csv_paths) > 1:
                    if st.button("Mesclar Resultados"):
                        with st.spinner("Mesclando resultados..."):
                            merged_path = library_service.merge_libraries(csv_paths)
                            if merged_path:
                                st.success(f"Mesclagem concluída! Arquivo: {merged_path}")
                                app_state.set_last_processed_file(merged_path)
                                
                                if st.button("Enriquecer Dados"):
                                    app_state.change_page("workflow")
                                    st.rerun()
            else:
                st.error("Não foi possível escanear nenhuma fonte.")
    
    # Interface para escanear uma fonte específica
    st.markdown('<div class="section-header">📂 Escanear Fonte Específica</div>', unsafe_allow_html=True)
    
    source_names = [source.name for source in sources]
    selected_source = st.selectbox("Selecione uma fonte", source_names)
    
    if st.button(f"Escanear {selected_source}"):
        with st.spinner(f"Escaneando {selected_source}..."):
            csv_path = library_service.scan_source(selected_source)
            
            if csv_path:
                st.success(f"Escaneamento concluído! Arquivo: {csv_path}")
                app_state.add_scan_result(
                    selected_source,
                    True,
                    f"Escaneamento concluído: {csv_path}",
                    csv_path
                )
                app_state.set_last_processed_file(csv_path)
                
                # Oferecer opções para próximos passos
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Enriquecer Dados"):
                        with st.spinner("Enriquecendo dados..."):
                            enriched_path = library_service.enrich_csv(csv_path)
                            if enriched_path:
                                st.success(f"Dados enriquecidos! Arquivo: {enriched_path}")
                                app_state.set_last_processed_file(enriched_path)
                with col2:
                    if st.button("Visualizar Dados"):
                        app_state.change_page("view")
                        st.rerun()
                        
            else:
                st.error(f"Erro ao escanear {selected_source}")
                app_state.add_scan_result(
                    selected_source,
                    False,
                    f"Erro ao escanear {selected_source}"
                )
    
    # Exibir resultados anteriores
    scan_results = app_state.scan_results
    if scan_results:
        st.markdown('<div class="section-header">📋 Resultados Recentes</div>', unsafe_allow_html=True)
        
        for source_name, result in scan_results.items():
            status_color = "green" if result["status"] == "success" else "red"
            st.markdown(
                f"<div style='padding: 10px; border-left: 5px solid {status_color}; background-color: #f0f0f0;'>"
                f"<strong>{source_name}:</strong> {result['message']}"
                f"</div>",
                unsafe_allow_html=True
            )