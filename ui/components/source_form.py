import streamlit as st
from typing import Dict, Any, Optional

def render_source_form(library_service):
    """
    Renderiza o formulário de adição de fonte.
    
    Args:
        library_service: Serviço da biblioteca
        
    Returns:
        Um dicionário com o resultado da adição de fonte, ou None se não foi adicionada
    """
    with st.form("add_source_form"):
        name = st.text_input("Nome da Fonte", placeholder="Ex: Meus Ebooks no iCloud")
        
        source_type = st.selectbox(
            "Tipo de Fonte",
            options=["icloud", "filesystem", "dropbox", "kindle", "kindle_cloud"],
            format_func=lambda x: {
                "icloud": "iCloud Drive",
                "filesystem": "Sistema de Arquivos Local",
                "dropbox": "Dropbox",
                "kindle": "Amazon Kindle (CSV Exportado)",
                "kindle_cloud": "Amazon Kindle Cloud Reader"
            }[x]
        )
        
        path = st.text_input(
            "Caminho",
            placeholder={"icloud": "Ex: Documents/Ebooks",
                         "filesystem": "Ex: C:/Meus Ebooks",
                         "dropbox": "Ex: /Ebooks",
                         "kindle": "Ex: biblioteca_kindle.csv",
                         "kindle_cloud": "cloud"}[source_type]
        )
        
        # Configurações específicas por tipo
        config = {}
        
        if source_type == "icloud":
            st.subheader("Credenciais do iCloud")
            st.markdown("""
            <div class="info-card">
            <p>As credenciais do iCloud serão armazenadas de forma segura usando o sistema de chaveiro do seu sistema operacional.</p>
            <p>Seus dados não serão salvos no arquivo de configuração e permanecerão protegidos.</p>
            </div>
            """, unsafe_allow_html=True)
            username = st.text_input("Email do iCloud")
            password = st.text_input("Senha do iCloud", type="password")
            save_credentials = st.checkbox("Salvar credenciais de forma segura", value=True)
            
            config = {
                "username": username,
                "password": password,
                "save_credentials": save_credentials
            }
            
        elif source_type == "dropbox":
            st.subheader("Configuração do Dropbox")
            st.markdown("Você precisa de um token de acesso do Dropbox. [Saiba mais](https://www.dropbox.com/developers/apps)")
            token = st.text_input("Token de Acesso")
            config = {"token": token}

        elif source_type == "kindle_cloud":
            st.subheader("Credenciais do Kindle Cloud Reader")
            st.markdown("""
            <div class="info-card">
            <p><strong>Como funciona:</strong></p>
            <ol>
            <li>Você fornece suas credenciais Amazon</li>
            <li>O sistema abre um navegador automatizado</li>
            <li>Faz login e extrai sua biblioteca do Kindle Cloud Reader</li>
            <li>Credenciais armazenadas de forma segura no chaveiro do sistema</li>
            </ol>
            <p><strong>Regiões suportadas:</strong> amazon.com, amazon.com.br, amazon.co.uk, amazon.de</p>
            </div>
            """, unsafe_allow_html=True)

            amazon_domain = st.selectbox(
                "Região Amazon",
                options=["amazon.com", "amazon.com.br", "amazon.co.uk", "amazon.de"],
                format_func=lambda x: {
                    "amazon.com": "🇺🇸 Amazon.com (EUA)",
                    "amazon.com.br": "🇧🇷 Amazon.com.br (Brasil)",
                    "amazon.co.uk": "🇬🇧 Amazon.co.uk (UK)",
                    "amazon.de": "🇩🇪 Amazon.de (Alemanha)"
                }[x]
            )

            email = st.text_input("Email Amazon")
            password = st.text_input("Senha Amazon", type="password")
            save_credentials = st.checkbox("Salvar credenciais de forma segura", value=True)

            config = {
                "amazon_domain": amazon_domain,
                "email": email,
                "password": password,
                "save_credentials": save_credentials
            }

        submitted = st.form_submit_button("Adicionar Fonte")
        
        if submitted:
            if not name or not path:
                st.error("Nome e caminho são obrigatórios.")
                return None
            elif source_type == "icloud" and (not username or not password):
                st.error("Credenciais do iCloud são obrigatórias.")
                return None
            elif source_type == "dropbox" and not token:
                st.error("Token do Dropbox é obrigatório.")
                return None
            elif source_type == "kindle_cloud" and (not email or not password):
                st.error("Email e senha do Kindle Cloud Reader são obrigatórios.")
                return None
            else:
                source_id, temp_credentials = library_service.add_source(name, source_type, path, config)
                
                if source_id:
                    st.success(f"Fonte '{name}' adicionada com sucesso!")

                    # Mensagem específica para iCloud
                    if source_type == "icloud" and save_credentials:
                        st.info("As credenciais do iCloud foram armazenadas de forma segura.")

                    # Mensagem específica para Kindle Cloud
                    if source_type == "kindle_cloud":
                        if save_credentials:
                            st.info("As credenciais do Kindle foram armazenadas de forma segura.")
                        st.info("Próximo passo: escaneie a fonte para carregar sua biblioteca do Kindle Cloud Reader")
                    
                    return {
                        "name": name,
                        "type": source_type,
                        "id": source_id
                    }
                else:
                    st.error("Erro ao adicionar fonte.")
                    return None
    
    return None