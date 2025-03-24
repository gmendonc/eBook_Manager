import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
from datetime import datetime
import streamlit as st
from wordcloud import WordCloud
import nltk
from nltk.corpus import stopwords
import altair as alt
import logging

logger = logging.getLogger(__name__)

# Verificar se os recursos do NLTK estão disponíveis
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    try:
        nltk.download('stopwords', quiet=True)
    except:
        logging.warning("Não foi possível baixar stopwords do NLTK")

@st.cache_data
def load_data(file_path):
    """
    Carrega dados de um arquivo CSV.
    
    Args:
        file_path: Caminho para o arquivo CSV
        
    Returns:
        DataFrame pandas ou None em caso de erro
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        logger.error(f"Erro ao carregar o arquivo: {str(e)}")
        return None

def process_data(df):
    """
    Processa e limpa os dados do DataFrame.
    
    Args:
        df: DataFrame pandas com dados de ebooks
        
    Returns:
        DataFrame processado e limpo
    """
    # Criar cópia para não modificar o original
    df_clean = df.copy()
    
    # Renomear colunas se necessário
    columns_mapping = {
        'Titulo_Extraido': 'Titulo',
        'Autor_Extraido': 'Autor',
        'Titulo': 'Titulo',
        'Autor': 'Autor'
    }
    
    # Aplicar mapeamento apenas para colunas que existem
    for old_col, new_col in columns_mapping.items():
        if old_col in df_clean.columns and old_col != new_col:
            if new_col not in df_clean.columns:
                df_clean[new_col] = df_clean[old_col]
            elif df_clean[new_col].isna().all() and not df_clean[old_col].isna().all():
                df_clean[new_col] = df_clean[old_col]
    
    # Se não tem coluna de título, extrair do nome do arquivo
    if 'Titulo' not in df_clean.columns:
        if 'Nome' in df_clean.columns:
            df_clean['Titulo'] = df_clean['Nome'].apply(lambda x: os.path.splitext(x)[0] if isinstance(x, str) else x)
    
    # Se não tem coluna de autor, usar "Desconhecido"
    if 'Autor' not in df_clean.columns:
        df_clean['Autor'] = "Desconhecido"
    
    # Converter tamanho para numérico
    if 'Tamanho(MB)' in df_clean.columns:
        df_clean['Tamanho(MB)'] = pd.to_numeric(df_clean['Tamanho(MB)'], errors='coerce')
    
    # Extrair ano da data de modificação, se disponível
    if 'Data Modificação' in df_clean.columns:
        df_clean['Ano'] = df_clean['Data Modificação'].apply(extract_year)
    
    # Processar temas (poderiam estar em diferentes formatos)
    theme_columns = [col for col in df_clean.columns if 'tema' in col.lower() or 'temas' in col.lower()]
    if theme_columns:
        # Usar a primeira coluna de temas encontrada
        theme_col = theme_columns[0]
        if 'Temas' not in df_clean.columns:
            df_clean['Temas'] = df_clean[theme_col]
    
    return df_clean

def extract_year(date_str):
    """
    Extrai o ano de uma string de data.
    
    Args:
        date_str: String com data
        
    Returns:
        Ano como inteiro ou None
    """
    if pd.isna(date_str):
        return None
    
    try:
        # Tentar vários formatos comuns
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
                
        # Tentar extrair apenas o ano com regex
        year_match = re.search(r'(\d{4})', str(date_str))
        if year_match:
            year = int(year_match.group(1))
            if 1900 <= year <= datetime.now().year:
                return year
                
    except Exception as e:
        logger.error(f"Erro ao extrair ano: {str(e)}")
        
    return None

def generate_wordcloud(text_series):
    """
    Gera uma nuvem de palavras a partir de uma série de textos.
    
    Args:
        text_series: Série pandas com textos
        
    Returns:
        Objeto WordCloud
    """
    text = ' '.join(text_series.dropna().astype(str))
    
    # Remover stopwords
    try:
        stop_words = set(stopwords.words('english') + stopwords.words('portuguese'))
    except:
        stop_words = set()
    
    # Criar nuvem de palavras
    try:
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
    except Exception as e:
        logger.error(f"Erro ao gerar nuvem de palavras: {str(e)}")
        return None

def create_format_distribution_chart(df):
    """
    Cria um gráfico de distribuição de formatos.
    
    Args:
        df: DataFrame pandas processado
        
    Returns:
        Figura matplotlib
    """
    if 'Formato' not in df.columns:
        return None
        
    try:
        format_counts = df['Formato'].value_counts()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        format_counts.plot(kind='bar', ax=ax, color='skyblue')
        plt.xticks(rotation=45)
        plt.ylabel('Quantidade')
        plt.tight_layout()
        
        return fig
    except Exception as e:
        logger.error(f"Erro ao criar gráfico de distribuição de formatos: {str(e)}")
        return None

def create_year_distribution_chart(df):
    """
    Cria um gráfico de distribuição por ano.
    
    Args:
        df: DataFrame pandas processado
        
    Returns:
        Figura matplotlib ou None se não houver dados
    """
    if 'Ano' not in df.columns:
        return None
        
    try:
        year_counts = df['Ano'].dropna().astype(int).value_counts().sort_index()
        
        if year_counts.empty:
            return None
            
        fig, ax = plt.subplots(figsize=(10, 6))
        year_counts.plot(kind='line', marker='o', ax=ax, color='green')
        plt.ylabel('Quantidade')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return fig
    except Exception as e:
        logger.error(f"Erro ao criar gráfico de distribuição por ano: {str(e)}")
        return None

def create_size_distribution_chart(df):
    """
    Cria um gráfico de distribuição de tamanho.
    
    Args:
        df: DataFrame pandas processado
        
    Returns:
        Figura matplotlib
    """
    if 'Tamanho(MB)' not in df.columns:
        return None
        
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(df['Tamanho(MB)'].dropna(), bins=20, kde=True, ax=ax, color='purple')
        plt.xlabel('Tamanho (MB)')
        plt.ylabel('Frequência')
        plt.tight_layout()
        
        return fig
    except Exception as e:
        logger.error(f"Erro ao criar gráfico de distribuição de tamanho: {str(e)}")
        return None

def create_top_authors_chart(df, top_n=10):
    """
    Cria um gráfico interativo dos principais autores.
    
    Args:
        df: DataFrame pandas processado
        top_n: Número de autores a exibir
        
    Returns:
        Gráfico Altair
    """
    if 'Autor' not in df.columns:
        return None
        
    try:
        author_counts = df['Autor'].value_counts().head(top_n)
        
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
        
        return chart
    except Exception as e:
        logger.error(f"Erro ao criar gráfico de principais autores: {str(e)}")
        return None

def create_format_pie_chart(df):
    """
    Cria um gráfico de pizza para formatos.
    
    Args:
        df: DataFrame pandas processado
        
    Returns:
        Figura matplotlib
    """
    if 'Formato' not in df.columns:
        return None
        
    try:
        format_counts = df['Formato'].value_counts()
        
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(format_counts, labels=format_counts.index, autopct='%1.1f%%', 
               startangle=90, shadow=True, explode=[0.05] * len(format_counts))
        plt.axis('equal')
        
        return fig
    except Exception as e:
        logger.error(f"Erro ao criar gráfico de pizza para formatos: {str(e)}")
        return None

def extract_themes_from_column(df, theme_column='Temas'):
    """
    Extrai temas de uma coluna de temas.
    
    Args:
        df: DataFrame pandas
        theme_column: Nome da coluna de temas
        
    Returns:
        Lista de temas
    """
    if theme_column not in df.columns:
        return []
        
    all_themes = []
    
    for themes in df[theme_column].dropna():
        if isinstance(themes, str):
            # Split por vírgula ou ponto e vírgula
            theme_list = re.split(r'[,;]', themes)
            all_themes.extend([t.strip() for t in theme_list if t.strip()])
    
    return all_themes

def create_themes_chart(df, top_n=15):
    """
    Cria um gráfico interativo dos principais temas.
    
    Args:
        df: DataFrame pandas processado
        top_n: Número de temas a exibir
        
    Returns:
        Gráfico Altair
    """
    # Extrair temas
    all_themes = extract_themes_from_column(df)
    
    if not all_themes:
        return None
        
    try:
        theme_counts = pd.Series(all_themes).value_counts().head(top_n)
        
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
        
        return chart
    except Exception as e:
        logger.error(f"Erro ao criar gráfico de temas: {str(e)}")
        return None

def apply_filters(df, format_filter=None, author_filter=None, theme_filter=None):
    """
    Aplica filtros ao DataFrame.
    
    Args:
        df: DataFrame pandas
        format_filter: Filtro de formato
        author_filter: Filtro de autor
        theme_filter: Filtro de tema
        
    Returns:
        DataFrame filtrado
    """
    filtered_df = df.copy()
    
    # Aplicar filtro de formato
    if format_filter and format_filter != 'Todos' and 'Formato' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Formato'] == format_filter]
    
    # Aplicar filtro de autor
    if author_filter and author_filter != 'Todos' and 'Autor' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Autor'] == author_filter]
    
    # Aplicar filtro de tema
    if theme_filter and theme_filter != 'Todos' and 'Temas' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Temas'].str.contains(theme_filter, na=False)]
    
    return filtered_df

def get_unique_values_from_column(df, column, include_all=True):
    """
    Obtém valores únicos de uma coluna.
    
    Args:
        df: DataFrame pandas
        column: Nome da coluna
        include_all: Se deve incluir a opção "Todos"
        
    Returns:
        Lista de valores únicos
    """
    if column not in df.columns:
        return ['Todos'] if include_all else []
        
    values = sorted(df[column].dropna().unique().tolist())
    
    if include_all:
        return ['Todos'] + values
    else:
        return values

def get_unique_themes(df, column='Temas'):
    """
    Obtém temas únicos de uma coluna de temas.
    
    Args:
        df: DataFrame pandas
        column: Nome da coluna de temas
        
    Returns:
        Lista de temas únicos
    """
    if column not in df.columns:
        return ['Todos']
        
    # Extrair temas únicos de toda a coluna
    all_themes = set()
    for themes in df[column].dropna():
        if isinstance(themes, str):
            theme_list = re.split(r'[,;]', themes)
            all_themes.update([t.strip() for t in theme_list if t.strip()])
    
    if all_themes:
        return ['Todos'] + sorted(all_themes)
    else:
        return ['Todos']