import streamlit as st
from datetime import datetime

def render_workflow_page(library_service, app_state):
    """
    Renders the workflow page for executing the complete ebook processing workflow.
    
    Args:
        library_service: Service for managing the library
        app_state: Application state manager
    """
    st.markdown('<div class="main-header">🔄 Fluxo de Trabalho Completo</div>', unsafe_allow_html=True)
    
    st.markdown("""
    O fluxo de trabalho completo executa as seguintes etapas:
    1. Escanear todas as fontes configuradas
    2. Mesclar os resultados em um único arquivo
    3. Enriquecer os metadados dos ebooks
    4. Opcionalmente, exportar para o Notion
    """)
    
    sources = library_service.get_sources()
    
    if not sources:
        st.warning("Nenhuma fonte configurada. Adicione fontes primeiro.")
        if st.button("Configurar Fontes"):
            app_state.change_page("setup")
            st.rerun()
    else:
        # Iniciar fluxo
        if st.button("Iniciar Fluxo Completo"):
            st.markdown('<div class="section-header">⏳ Progresso</div>', unsafe_allow_html=True)
            
            # Criar placeholders para status
            scan_status = st.empty()
            merge_status = st.empty()
            enrich_status = st.empty()
            notion_status = st.empty()
            
            # Barra de progresso geral
            progress_bar = st.progress(0)
            
            # 1. Escanear todas as fontes
            scan_status.markdown("🔍 **Escaneando fontes...**")
            
            csv_paths = []
            for i, source in enumerate(sources):
                source_status = st.empty()
                source_status.markdown(f"Escaneando {source.name}...")
                
                csv_path = library_service.scan_source(source.name)
                if csv_path:
                    csv_paths.append(csv_path)
                    source_status.markdown(f"✅ {source.name} escaneado com sucesso.")
                else:
                    source_status.markdown(f"❌ Erro ao escanear {source.name}.")
                
                # Atualizar progresso
                progress = (i + 1) / (len(sources) * 3 + 1)  # +1 para mesclagem
                progress_bar.progress(progress)
            
            if not csv_paths:
                scan_status.markdown("❌ **Nenhum ebook encontrado.**")
                progress_bar.progress(1.0)
                st.error("Falha no fluxo de trabalho: Nenhum ebook encontrado.")
                return
                
            scan_status.markdown("✅ **Escaneamento concluído.**")
            
            # 2. Mesclar resultados
            merge_status.markdown("🔄 **Mesclando bibliotecas...**")
            
            merged_path = library_service.merge_libraries(csv_paths)
            if not merged_path:
                merge_status.markdown("❌ **Falha ao mesclar bibliotecas.**")
                progress_bar.progress(1.0)
                st.error("Falha no fluxo de trabalho: Erro ao mesclar bibliotecas.")
                return
                
            merge_status.markdown("✅ **Mesclagem concluída.**")
            
            # Atualizar progresso
            progress = (len(sources) + 1) / (len(sources) * 3 + 1)
            progress_bar.progress(progress)
            
            # 3. Enriquecer dados
            enrich_status.markdown("🔍 **Enriquecendo metadados...**")

            # Permitir a seleção do método de enriquecimento
            available_enrichers = library_service.get_available_enrichers()
            active_enricher = library_service.get_active_enricher_name()

            enricher_name = st.selectbox(
                "Método de enriquecimento:",
                options=available_enrichers,
                index=available_enrichers.index(active_enricher) if active_enricher in available_enrichers else 0
            )
            
            enriched_path = library_service.enrich_csv(merged_path, enricher_name)
            if not enriched_path:
                enrich_status.markdown("❌ **Falha ao enriquecer dados.**")
                progress_bar.progress(1.0)
                st.error("Falha no fluxo de trabalho: Erro ao enriquecer dados.")
                return
                
            enrich_status.markdown("✅ **Enriquecimento concluído.**")
            app_state.set_last_processed_file(enriched_path)
            
            # Atualizar progresso para quase completo
            progress = 0.9
            progress_bar.progress(progress)
            
            # 4. Exportar para o Notion (opcional)
            export_notion = st.checkbox("Exportar para o Notion", value=False)
            
            if export_notion:
                notion_status.markdown("🔄 **Exportando para o Notion...**")
                
                success = library_service.export_to_notion(enriched_path)
                if success:
                    notion_status.markdown("✅ **Exportação para o Notion concluída.**")
                else:
                    notion_status.markdown("❌ **Falha ao exportar para o Notion.**")
            else:
                notion_status.markdown("⏸️ **Exportação para o Notion ignorada.**")
            
            # Fluxo concluído
            progress_bar.progress(1.0)
            
            st.markdown('<div class="success-message">🎉 Fluxo de trabalho concluído com sucesso!</div>', unsafe_allow_html=True)
            
            # Opções para próximos passos
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Visualizar Biblioteca"):
                    app_state.change_page("view")
                    st.rerun()
                    
            with col2:
                if st.button("Ver Dashboard"):
                    app_state.change_page("dashboard")
                    st.rerun()