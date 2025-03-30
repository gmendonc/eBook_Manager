import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
import altair as alt
from datetime import datetime
from wordcloud import WordCloud
import nltk
from nltk.corpus import stopwords
from typing import Dict, Any, List, Optional

def render_dashboard_page(library_service, app_state):
    """
    Renders the dashboard page with visualizations and analytics for the eBook library.
    
    Args:
        library_service: Service for managing the library
        app_state: Application state manager
    """
    st.markdown('<div class="main-header">📊 Dashboard da Biblioteca</div>', unsafe_allow_html=True)
    
    # Find CSV files
    csv_files = [f for f in os.listdir() if f.endswith('.csv') and os.path.isfile(f)]
    
    if not csv_files:
        st.warning("Nenhum arquivo CSV encontrado. Escaneie suas fontes primeiro.")
        if st.button("Ir para Escaneamento"):
            app_state.change_page("scan")
            st.rerun()
        return
    
    # Sort files
    csv_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # Prioritize enriched files
    enriched_files = [f for f in csv_files if 'enriched' in f]
    if enriched_files:
        files_to_display = enriched_files + [f for f in csv_files if f not in enriched_files]
    else:
        files_to_display = csv_files
        
    # Prioritize last processed file if available
    if app_state.last_processed_file in files_to_display:
        default_index = files_to_display.index(app_state.last_processed_file)
    else:
        default_index = 0
        
    selected_file = st.selectbox(
        "Selecione um arquivo para análise", 
        files_to_display,
        index=default_index
    )
    
    try:
        # Load and process data
        df = load_data(selected_file)
        if df is None or df.empty:
            st.warning("Não foi possível carregar os dados ou o arquivo está vazio.")
            return
            
        df_processed = process_data(df)
        
        # Show basic information
        st.markdown('<div class="section-header">📊 Informações da Biblioteca</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Ebooks", len(df_processed))
        
        with col2:
            if 'Tamanho(MB)' in df_processed.columns:
                df_processed['Tamanho(MB)'] = pd.to_numeric(df_processed['Tamanho(MB)'], errors='coerce')
                total_size = df_processed['Tamanho(MB)'].sum()
                st.metric("Tamanho Total", f"{total_size:.2f} MB")
            else:
                st.metric("Tamanho Total", "N/D")
        
        with col3:
            if 'Autor' in df_processed.columns:
                unique_authors = df_processed['Autor'].nunique()
                st.metric("Autores Únicos", unique_authors)
            else:
                st.metric("Autores Únicos", "N/D")
        
        # Tabs for different visualizations
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Estatísticas", "👥 Autores", "📑 Formatos e Temas", "🔍 Explorar"])
        
        with tab1:
            display_statistics(df_processed)
        
        with tab2:
            display_author_analysis(df_processed)
        
        with tab3:
            display_format_theme_analysis(df_processed)
        
        with tab4:
            display_data_explorer(df_processed)
            
    except Exception as e:
        st.error(f"Erro ao processar dados para o dashboard: {str(e)}")

def load_data(file_path):
    """
    Loads data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Pandas DataFrame or None if error
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {str(e)}")
        return None

def process_data(df):
    """
    Processes and cleans data from the DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Processed DataFrame
    """
    # Create a copy to avoid modifying the original
    df_clean = df.copy()
    
    # Rename columns if needed
    columns_mapping = {
        'Titulo_Extraido': 'Titulo',
        'Autor_Extraido': 'Autor',
        'Titulo': 'Titulo',
        'Autor': 'Autor'
    }
    
    # Apply mapping only for columns that exist
    for old_col, new_col in columns_mapping.items():
        if old_col in df_clean.columns and old_col != new_col:
            if new_col not in df_clean.columns:
                df_clean[new_col] = df_clean[old_col]
            elif df_clean[new_col].isna().all() and not df_clean[old_col].isna().all():
                df_clean[new_col] = df_clean[old_col]
    
    # If no title column, extract from filename
    if 'Titulo' not in df_clean.columns:
        if 'Nome' in df_clean.columns:
            df_clean['Titulo'] = df_clean['Nome'].apply(lambda x: os.path.splitext(x)[0] if isinstance(x, str) else x)
    
    # If no author column, use "Unknown"
    if 'Autor' not in df_clean.columns:
        df_clean['Autor'] = "Desconhecido"
    
    # Convert size to numeric
    if 'Tamanho(MB)' in df_clean.columns:
        df_clean['Tamanho(MB)'] = pd.to_numeric(df_clean['Tamanho(MB)'], errors='coerce')
    
    # Extract year from modification date if available
    if 'Data Modificação' in df_clean.columns:
        df_clean['Ano'] = df_clean['Data Modificação'].apply(extract_year)
    
    # Process themes (could be in different formats)
    theme_columns = [col for col in df_clean.columns if 'tema' in col.lower() or 'temas' in col.lower()]
    if theme_columns:
        # Use first theme column found
        theme_col = theme_columns[0]
        if 'Temas' not in df_clean.columns:
            df_clean['Temas'] = df_clean[theme_col]
    
    return df_clean

def extract_year(date_str):
    """
    Extracts the year from a date string.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        Year as integer or None if not found
    """
    if pd.isna(date_str):
        return None
    
    try:
        # Try various common formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%Y'
        ]
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(str(date_str), fmt)
                return date_obj.year
            except ValueError:
                continue
                
        # Try to extract just the year with regex
        year_match = re.search(r'(\d{4})', str(date_str))
        if year_match:
            year = int(year_match.group(1))
            if 1900 <= year <= datetime.now().year:
                return year
                
    except Exception:
        pass
        
    return None

def generate_wordcloud(text_series):
    """
    Generates a word cloud from a text series.
    
    Args:
        text_series: Series of text to generate word cloud from
        
    Returns:
        WordCloud object
    """
    text = ' '.join(text_series.dropna().astype(str))
    
    # Remove stopwords
    try:
        # Download stopwords if not already downloaded
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        stop_words = set(stopwords.words('english') + stopwords.words('portuguese'))
    except:
        stop_words = set()
    
    # Create word cloud
    wordcloud = WordCloud(
        width=800, 
        height=400, 
        background_color='white',
        max_words=150,
        stopwords=stop_words,
        contour_width=3,
        contour_color='steelblue'
    ).generate(text)
    
    return wordcloud

def display_statistics(df):
    """
    Displays general statistics about the eBook library.
    
    Args:
        df: Processed DataFrame
    """
    st.subheader("Estatísticas Gerais")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Format distribution
        if 'Formato' in df.columns:
            format_counts = df['Formato'].value_counts()
            
            st.subheader("Distribuição por Formato")
            fig, ax = plt.subplots(figsize=(10, 6))
            format_counts.plot(kind='bar', ax=ax, color='skyblue')
            plt.xticks(rotation=45)
            plt.ylabel('Quantidade')
            plt.tight_layout()
            st.pyplot(fig)
            
        # Year distribution (if available)
        if 'Ano' in df.columns:
            year_counts = df['Ano'].dropna().astype(int).value_counts().sort_index()
            
            if not year_counts.empty:
                st.subheader("Distribuição por Ano")
                fig, ax = plt.subplots(figsize=(10, 6))
                year_counts.plot(kind='line', marker='o', ax=ax, color='green')
                plt.ylabel('Quantidade')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                st.pyplot(fig)
    
    with col2:
        # Size distribution
        if 'Tamanho(MB)' in df.columns:
            st.subheader("Distribuição de Tamanho")
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.histplot(df['Tamanho(MB)'].dropna(), bins=20, kde=True, ax=ax, color='purple')
            plt.xlabel('Tamanho (MB)')
            plt.ylabel('Frequência')
            plt.tight_layout()
            st.pyplot(fig)
            
        # Top 5 largest eBooks
        if 'Tamanho(MB)' in df.columns and 'Titulo' in df.columns:
            st.subheader("Top 5 Maiores Ebooks")
            top_size = df.sort_values('Tamanho(MB)', ascending=False).head(5)[['Titulo', 'Tamanho(MB)']]
            
            # Create horizontal bar chart
            fig, ax = plt.subplots(figsize=(10, 5))
            bars = ax.barh(top_size['Titulo'], top_size['Tamanho(MB)'], color='orange')
            ax.set_xlabel('Tamanho (MB)')
            ax.invert_yaxis()  # Invert to have largest on top
            
            # Add values to bars
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{width:.1f} MB', 
                        ha='left', va='center')
                
            plt.tight_layout()
            st.pyplot(fig)

def display_author_analysis(df):
    """
    Displays author-related analyses.
    
    Args:
        df: Processed DataFrame
    """
    st.subheader("Análise de Autores")
    
    if 'Autor' not in df.columns:
        st.warning("Dados de autor não disponíveis.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top 10 authors by quantity
        author_counts = df['Autor'].value_counts().head(10)
        
        st.subheader("Top 10 Autores por Quantidade")
        
        # Create chart with Altair for better interactivity
        author_df = pd.DataFrame({
            'Autor': author_counts.index,
            'Quantidade': author_counts.values
        })
        
        chart = alt.Chart(author_df).mark_bar().encode(
            x='Quantidade:Q',
            y=alt.Y('Autor:N', sort='-x'),
            color=alt.Color('Quantidade:Q', scale=alt.Scale(scheme='blues')),
            tooltip=['Autor', 'Quantidade']
        ).properties(height=300)
        
        st.altair_chart(chart, use_container_width=True)
    
    with col2:
        # Author word cloud
        if len(df['Autor'].dropna()) > 5:
            st.subheader("Nuvem de Palavras - Autores")
            wordcloud = generate_wordcloud(df['Autor'])
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
        
        # Top authors by total size
        if 'Tamanho(MB)' in df.columns:
            author_size = df.groupby('Autor')['Tamanho(MB)'].sum().sort_values(ascending=False).head(10)
            
            st.subheader("Top 10 Autores por Volume (MB)")
            
            author_size_df = pd.DataFrame({
                'Autor': author_size.index,
                'Tamanho Total (MB)': author_size.values
            })
            
            chart = alt.Chart(author_size_df).mark_bar().encode(
                x='Tamanho Total (MB):Q',
                y=alt.Y('Autor:N', sort='-x'),
                color=alt.Color('Tamanho Total (MB):Q', scale=alt.Scale(scheme='oranges')),
                tooltip=['Autor', 'Tamanho Total (MB)']
            ).properties(height=300)
            
            st.altair_chart(chart, use_container_width=True)

def display_format_theme_analysis(df):
    """
    Displays format and theme analyses.
    
    Args:
        df: Processed DataFrame
    """
    st.subheader("Análise de Formatos e Temas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Format pie chart
        if 'Formato' in df.columns:
            format_counts = df['Formato'].value_counts()
            
            st.subheader("Distribuição de Formatos")
            
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.pie(format_counts, labels=format_counts.index, autopct='%1.1f%%', 
                   startangle=90, shadow=True, explode=[0.05] * len(format_counts))
            plt.axis('equal')
            st.pyplot(fig)
            
        # Format by year (if available)
        if 'Formato' in df.columns and 'Ano' in df.columns:
            # Filter rows with valid year
            df_with_year = df.dropna(subset=['Ano']).copy()
            df_with_year['Ano'] = df_with_year['Ano'].astype(int)
            
            if not df_with_year.empty:
                format_year = pd.crosstab(df_with_year['Ano'], df_with_year['Formato'])
                
                st.subheader("Evolução de Formatos por Ano")
                
                fig, ax = plt.subplots(figsize=(10, 6))
                format_year.plot(kind='bar', stacked=True, ax=ax, cmap='viridis')
                plt.xlabel('Ano')
                plt.ylabel('Quantidade')
                plt.xticks(rotation=45)
                plt.legend(title='Formato')
                plt.tight_layout()
                st.pyplot(fig)
    
    with col2:
        # Theme analysis (if available)
        if 'Temas' in df.columns:
            # Process themes (could be list, comma-separated string, etc.)
            all_themes = []
            
            for themes in df['Temas'].dropna():
                if isinstance(themes, str):
                    # Split by comma or semicolon
                    theme_list = re.split(r'[,;]', themes)
                    all_themes.extend([t.strip() for t in theme_list if t.strip()])
            
            if all_themes:
                theme_counts = pd.Series(all_themes).value_counts().head(15)
                
                st.subheader("Top 15 Temas")
                
                theme_df = pd.DataFrame({
                    'Tema': theme_counts.index,
                    'Quantidade': theme_counts.values
                })
                
                chart = alt.Chart(theme_df).mark_bar().encode(
                    x='Quantidade:Q',
                    y=alt.Y('Tema:N', sort='-x'),
                    color=alt.Color('Quantidade:Q', scale=alt.Scale(scheme='greenblue')),
                    tooltip=['Tema', 'Quantidade']
                ).properties(height=400)
                
                st.altair_chart(chart, use_container_width=True)
                
                # Theme word cloud
                st.subheader("Nuvem de Palavras - Temas")
                wordcloud = generate_wordcloud(pd.Series(all_themes))
                
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
            else:
                st.info("Não foram encontrados temas nos dados.")
        else:
            st.info("Dados de temas não disponíveis. Execute o enriquecedor de ebooks para adicionar temas.")

def display_data_explorer(df):
    """
    Displays an interactive data explorer.
    
    Args:
        df: Processed DataFrame
    """
    st.subheader("Explorador de Dados")
    
    # Filters
    st.markdown("**Filtros**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'Formato' in df.columns:
            formats = ['Todos'] + sorted(df['Formato'].dropna().unique().tolist())
            selected_format = st.selectbox("Formato", formats)
            if selected_format != 'Todos':
                df = df[df['Formato'] == selected_format]
    
    with col2:
        if 'Autor' in df.columns:
            # Get unique authors and sort
            authors = ['Todos'] + sorted(df['Autor'].dropna().unique().tolist())
            selected_author = st.selectbox("Autor", authors)
            if selected_author != 'Todos':
                df = df[df['Autor'] == selected_author]
    
    with col3:
        if 'Temas' in df.columns:
            # Extract unique themes
            all_themes = set()
            for themes in df['Temas'].dropna():
                if isinstance(themes, str):
                    theme_list = re.split(r'[,;]', themes)
                    all_themes.update([t.strip() for t in theme_list if t.strip()])
            
            themes = ['Todos'] + sorted(list(all_themes))
            selected_theme = st.selectbox("Tema", themes)
            if selected_theme != 'Todos':
                df = df[df['Temas'].str.contains(selected_theme, na=False)]
    
    # Show filtered data
    st.markdown(f"Mostrando **{len(df)}** ebooks")
    
    # Column selection for display
    default_columns = ['Titulo', 'Autor', 'Formato', 'Tamanho(MB)']
    available_columns = [col for col in df.columns if col in df.columns]
    
    # Use only available columns among defaults
    display_columns = [col for col in default_columns if col in available_columns]
    
    # Add more columns if needed
    if 'Temas' in available_columns and 'Temas' not in display_columns:
        display_columns.append('Temas')
        
    if 'Data Modificação' in available_columns and 'Data Modificação' not in display_columns:
        display_columns.append('Data Modificação')
    
    # Display paginated table
    st.dataframe(df[display_columns], use_container_width=True)
    
    # Download option
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download dados filtrados como CSV",
        data=csv,
        file_name=f"ebooks_filtrados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )