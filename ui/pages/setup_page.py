import streamlit as st
from ui.components.source_form import render_source_form

def render_setup_page(library_service, app_state):
    """
    Renders the setup page for configuring sources and taxonomy.
    
    Args:
        library_service: Service for managing the library
        app_state: Application state manager
    """
    st.markdown('<div class="main-header">⚙️ Configuração de Fontes</div>', unsafe_allow_html=True)
    
    # Abas para configuração
    tab1, tab2, tab3, tab4 = st.tabs(["Adicionar Fonte", "Gerenciar Fontes", "Configurar Taxonomia", "Método de Enriquecimento"])
    
    with tab1:
        st.markdown('<div class="section-header">📂 Adicionar Nova Fonte</div>', unsafe_allow_html=True)
        
        # Formulário para adicionar fonte
        result = render_source_form(library_service)
        if result:
            # Recarregar a página para mostrar a nova fonte
            st.rerun()
    
    with tab2:
        st.markdown('<div class="section-header">📋 Gerenciar Fontes</div>', unsafe_allow_html=True)
        
        sources = library_service.get_sources()
        if not sources:
            st.warning("Nenhuma fonte configurada.")
        else:
            for i, source in enumerate(sources):
                with st.expander(f"{source.name} ({source.type})"):
                    st.markdown(f"**Tipo:** {source.type}")
                    st.markdown(f"**Caminho:** {source.path}")
                    
                    last_scan = source.last_scan
                    last_scan_str = last_scan.strftime('%Y-%m-%d %H:%M:%S') if last_scan else "Nunca"
                    st.markdown(f"**Último escaneamento:** {last_scan_str}")
                    
                    if st.button(f"Remover {source.name}", key=f"remove_{i}"):
                        if library_service.remove_source(source.name):
                            st.success(f"Fonte '{source.name}' removida com sucesso!")
                            st.rerun()
                        else:
                            st.error(f"Erro ao remover fonte '{source.name}'.")
    
    with tab3:
        st.markdown('<div class="section-header">📋 Configurar Taxonomia de Temas</div>', unsafe_allow_html=True)
        
        current_path = library_service.get_taxonomy_path()
        st.markdown(f"**Caminho atual:** {current_path}")
        
        # Upload de arquivo de taxonomia
        uploaded_file = st.file_uploader("Carregar arquivo de taxonomia", type=["json"])
        
        if uploaded_file is not None:
            # Salvar o arquivo
            try:
                with open(uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Arquivo carregado: {uploaded_file.name}")
                
                # Atualizar caminho
                if library_service.set_taxonomy_path(uploaded_file.name):
                    st.success(f"Taxonomia atualizada para: {uploaded_file.name}")
                else:
                    st.error("Erro ao atualizar caminho da taxonomia.")
            except Exception as e:
                st.error(f"Erro ao salvar arquivo: {str(e)}")
                
        # Ou inserir caminho manualmente
        st.markdown("### Ou especifique o caminho manualmente")
        new_path = st.text_input("Caminho para o arquivo de taxonomia", value=current_path)
        
        if st.button("Atualizar Caminho"):
            if library_service.set_taxonomy_path(new_path):
                st.success(f"Taxonomia atualizada para: {new_path}")
            else:
                st.error("Erro ao atualizar taxonomia.")
    
    with tab4:
        st.markdown('<div class="section-header">🔧 Configurar Método de Enriquecimento</div>', unsafe_allow_html=True)
        
        # Obter métodos disponíveis
        available_enrichers = library_service.get_available_enrichers()
        active_enricher = library_service.get_active_enricher_name()
        
        if not available_enrichers:
            st.warning("Nenhum método de enriquecimento disponível.")
        else:
            # Descrições dos métodos
            enricher_descriptions = {
                'default': "Enriquecimento completo com extração de metadata e classificação de temas",
                'basic': "Enriquecimento básico (apenas extração de autor e título)",
                'external_api': "Enriquecimento com API externa (Open Library)"
            }
            
            st.markdown("### Selecione o método de enriquecimento")
            
            for enricher_name in available_enrichers:
                description = enricher_descriptions.get(enricher_name, "")
                is_active = enricher_name == active_enricher
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button(
                        "✓ Ativo" if is_active else "Ativar", 
                        key=f"activate_{enricher_name}",
                        disabled=is_active
                    ):
                        if library_service.set_active_enricher(enricher_name):
                            st.success(f"Método '{enricher_name}' ativado com sucesso!")
                            st.rerun()
                        else:
                            st.error(f"Erro ao ativar método '{enricher_name}'.")
                
                with col2:
                    st.markdown(f"**{enricher_name}**")
                    if description:
                        st.markdown(f"_{description}_")
            
            # Configurações específicas para o método External API
            if 'external_api' in available_enrichers:
                st.markdown("### Configurações da API Externa")
                api_key = st.text_input("Chave de API (opcional)", 
                                        type="password", 
                                        help="Use apenas se a API escolhida exigir uma chave")
                
                if st.button("Salvar Configuração API"):
                    if library_service.configure_external_api_enricher(api_key):
                        st.success("Configuração da API salva com sucesso!")
                    else:
                        st.error("Erro ao salvar configuração da API.")