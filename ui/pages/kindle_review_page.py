"""
Página de revisão e seleção interativa de livros Kindle.

Permite ao usuário filtrar, selecionar e exportar interativamente
livros da biblioteca Kindle Cloud Reader.
"""

import logging
import os
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from tempfile import gettempdir

import pandas as pd
import streamlit as st

from core.services.library_service import LibraryService
from core.services.kindle_export_history_service import KindleExportHistoryService

logger = logging.getLogger(__name__)


def render_kindle_review_page(library_service: LibraryService, temp_csv_path: str) -> None:
    """
    Renderiza página de revisão e seleção de livros Kindle.

    Args:
        library_service: Serviço de biblioteca
        temp_csv_path: Caminho para arquivo CSV temporário gerado pelo scanner
    """
    st.markdown('<div class="main-header">📚 Revisão e Seleção - Kindle Cloud Reader</div>', unsafe_allow_html=True)

    # Validar arquivo temporário
    if not os.path.exists(temp_csv_path):
        st.error("❌ Arquivo temporário não encontrado. Escaneie novamente.")
        if st.button("Voltar ao Escanear"):
            st.session_state.page = 'scan'
            st.rerun()
        return

    try:
        # Carregar dados do CSV
        df = pd.read_csv(temp_csv_path)
        logger.info(f"Carregados {len(df)} livros do CSV temporário")

        # Inicializar estado da sessão
        if 'kindle_selection_state' not in st.session_state:
            st.session_state.kindle_selection_state = {
                'selected': [False] * len(df),
                'filtered_indices': list(range(len(df))),
                'period_filter': 'Todos',
                'date_from': None,
                'date_to': None,
                'author_filter': [],
                'origin_type_filter': ['PURCHASE'],
                'read_status_filter': [0, 1, 2]  # 0: não lido, 1: em andamento, 2: concluído
            }

        # Layout com sidebar para filtros
        with st.sidebar:
            st.markdown("### 🔍 Filtros")

            # Filtro de Período
            period_options = ['Todos', 'Última semana', 'Último mês', 'Últimos 3 meses', 'Último ano', 'Personalizado']
            period = st.selectbox(
                "Período de Aquisição",
                period_options,
                index=period_options.index(st.session_state.kindle_selection_state['period_filter'])
            )
            st.session_state.kindle_selection_state['period_filter'] = period

            date_from = None
            date_to = None

            if period == 'Personalizado':
                col1, col2 = st.columns(2)
                with col1:
                    date_from = st.date_input("De", key='kindle_date_from')
                with col2:
                    date_to = st.date_input("Até", key='kindle_date_to')
                st.session_state.kindle_selection_state['date_from'] = date_from
                st.session_state.kindle_selection_state['date_to'] = date_to

            # Filtro de Autor
            unique_authors = sorted(df['Autor'].unique().tolist())
            selected_authors = st.multiselect(
                "Autores",
                unique_authors,
                default=st.session_state.kindle_selection_state['author_filter'],
                key='kindle_authors'
            )
            st.session_state.kindle_selection_state['author_filter'] = selected_authors

            # Filtro de Tipo de Origem
            origin_types = ['PURCHASE', 'FREE', 'PRIME_READING', 'UNLIMITED']
            selected_origins = st.multiselect(
                "Tipo de Origem",
                origin_types,
                default=['PURCHASE'],
                key='kindle_origins'
            )
            st.session_state.kindle_selection_state['origin_type_filter'] = selected_origins

            # Filtro de Status de Leitura
            st.markdown("#### Status de Leitura")
            col1, col2, col3 = st.columns(3)
            with col1:
                not_read = st.checkbox("Não lidos", value=True, key='kindle_not_read')
            with col2:
                in_progress = st.checkbox("Em andamento", value=True, key='kindle_in_progress')
            with col3:
                completed = st.checkbox("Concluídos", value=True, key='kindle_completed')

            read_status = []
            if not_read:
                read_status.append(0)
            if in_progress:
                read_status.append(1)
            if completed:
                read_status.append(2)
            st.session_state.kindle_selection_state['read_status_filter'] = read_status

            # Botões de seleção em massa
            st.markdown("### ⚙️ Controles de Seleção")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("✅ Todos", use_container_width=True):
                    st.session_state.kindle_selection_state['selected'] = [True] * len(df)
                    st.rerun()

            with col2:
                if st.button("❌ Nenhum", use_container_width=True):
                    st.session_state.kindle_selection_state['selected'] = [False] * len(df)
                    st.rerun()

            with col3:
                if st.button("🔄 Inverter", use_container_width=True):
                    selected = st.session_state.kindle_selection_state['selected']
                    st.session_state.kindle_selection_state['selected'] = [not s for s in selected]
                    st.rerun()

        # Aplicar filtros
        filtered_df, filtered_indices = _apply_filters(df, st.session_state.kindle_selection_state)
        st.session_state.kindle_selection_state['filtered_indices'] = filtered_indices

        # Métricas no topo
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total de Livros", len(df))

        with col2:
            st.metric("Após Filtros", len(filtered_df))

        selected_count = sum(
            st.session_state.kindle_selection_state['selected'][i]
            for i in filtered_indices
        )

        with col3:
            st.metric("Selecionados", selected_count)

        with col4:
            if len(filtered_df) > 0:
                percentage = (selected_count / len(filtered_df)) * 100
                st.metric("Percentual", f"{percentage:.1f}%")
            else:
                st.metric("Percentual", "0%")

        # Tabela de seleção
        st.markdown("### 📖 Livros")

        # Preparar dados para exibição
        display_data = []
        for idx, orig_idx in enumerate(filtered_indices):
            row = filtered_df.iloc[idx]
            display_data.append({
                'Exportar': st.session_state.kindle_selection_state['selected'][orig_idx],
                'Capa': row['URL_Capa'] if pd.notna(row['URL_Capa']) else '',
                'Título': row['Nome'],
                'Autor': row['Autor'],
                'Adquirido em': row['Data Modificação'],
                'Tipo': row['Tipo_Origem'],
                'Progresso': row['Percentual_Lido'],
                'Status': _get_book_status_emoji(row['ASIN']),
                'ASIN': row['ASIN']
            })

        display_df = pd.DataFrame(display_data)

        # Usar data_editor para seleção interativa
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            disabled=['Capa', 'Título', 'Autor', 'Adquirido em', 'Tipo', 'Progresso', 'Status', 'ASIN'],
            hide_index=True,
            key='kindle_editor'
        )

        # Atualizar estado de seleção
        for idx, orig_idx in enumerate(filtered_indices):
            st.session_state.kindle_selection_state['selected'][orig_idx] = edited_df.iloc[idx]['Exportar']

        # Preview de selecionados
        if selected_count > 0:
            with st.expander(f"👁️ Preview dos {selected_count} Livros Selecionados"):
                preview_data = []
                for orig_idx, selected in enumerate(st.session_state.kindle_selection_state['selected']):
                    if selected:
                        preview_data.append(df.iloc[orig_idx])

                if preview_data:
                    preview_df = pd.DataFrame(preview_data)
                    cols_per_row = 5
                    for i in range(0, len(preview_df), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, col in enumerate(cols):
                            if i + j < len(preview_df):
                                row = preview_df.iloc[i + j]
                                with col:
                                    if pd.notna(row['URL_Capa']) and row['URL_Capa']:
                                        st.image(row['URL_Capa'], use_container_width=True)
                                    else:
                                        st.write("📕")
                                    st.caption(f"{row['Nome'][:30]}...")
                                    st.caption(row['Data Modificação'])

        # Botão de exportação
        st.markdown("---")
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("👈 Voltar", use_container_width=True):
                # Limpar arquivo temporário
                try:
                    os.remove(temp_csv_path)
                    logger.info(f"Arquivo temporário removido: {temp_csv_path}")
                except Exception as e:
                    logger.warning(f"Erro ao remover arquivo temporário: {str(e)}")

                st.session_state.page = 'scan'
                st.rerun()

        with col2:
            if st.button(
                "📤 Exportar Selecionados",
                disabled=(selected_count == 0),
                use_container_width=True,
                type='primary'
            ):
                # Exportar livros selecionados
                success = _export_selected_books(
                    df,
                    st.session_state.kindle_selection_state['selected'],
                    library_service,
                    temp_csv_path
                )

                if success:
                    st.success(f"✅ {selected_count} livros exportados com sucesso!")
                    st.balloons()

                    # Atualizar histórico
                    _update_export_history(
                        df,
                        st.session_state.kindle_selection_state['selected']
                    )

                    # Redirecionar para página de visualização
                    st.session_state.page = 'view'
                    st.rerun()
                else:
                    st.error("❌ Erro ao exportar livros. Verifique o log.")

    except Exception as e:
        logger.error(f"Erro ao renderizar página Kindle: {str(e)}", exc_info=True)
        st.error(f"❌ Erro ao processar livros: {str(e)}")
        if st.button("Voltar"):
            st.session_state.page = 'scan'
            st.rerun()


def _apply_filters(df: pd.DataFrame, state: Dict[str, Any]) -> Tuple[pd.DataFrame, List[int]]:
    """
    Aplica filtros aos dados.

    Args:
        df: DataFrame com livros
        state: Estado contendo filtros

    Returns:
        Tupla (DataFrame filtrado, Lista de índices originais)
    """
    filtered_df = df.copy()
    indices = list(range(len(df)))

    # Filtro de período
    if state['period_filter'] != 'Todos':
        filtered_df, indices = _apply_period_filter(
            filtered_df,
            indices,
            state['period_filter'],
            state.get('date_from'),
            state.get('date_to')
        )

    # Filtro de autores
    if state['author_filter']:
        mask = filtered_df['Autor'].isin(state['author_filter'])
        filtered_df = filtered_df[mask]
        indices = [i for i, m in zip(indices, mask) if m]

    # Filtro de tipo de origem
    if state['origin_type_filter']:
        mask = filtered_df['Tipo_Origem'].isin(state['origin_type_filter'])
        filtered_df = filtered_df[mask]
        indices = [i for i, m in zip(indices, mask) if m]

    # Filtro de status de leitura
    read_status_filter = state['read_status_filter']
    mask = filtered_df['Percentual_Lido'].apply(
        lambda x: _get_read_status(x) in read_status_filter
    )
    filtered_df = filtered_df[mask]
    indices = [i for i, m in zip(indices, mask) if m]

    # Ordenar por data (mais recentes primeiro)
    sort_indices = sorted(range(len(filtered_df)), key=lambda i: filtered_df.iloc[i]['Data Modificação'], reverse=True)
    filtered_df = filtered_df.iloc[sort_indices]
    indices = [indices[i] for i in sort_indices]

    return filtered_df.reset_index(drop=True), indices


def _apply_period_filter(
    df: pd.DataFrame,
    indices: List[int],
    period: str,
    date_from: Optional[Any] = None,
    date_to: Optional[Any] = None
) -> Tuple[pd.DataFrame, List[int]]:
    """Aplica filtro de período."""
    now = datetime.now()

    if period == 'Última semana':
        cutoff = now - timedelta(days=7)
    elif period == 'Último mês':
        cutoff = now - timedelta(days=30)
    elif period == 'Últimos 3 meses':
        cutoff = now - timedelta(days=90)
    elif period == 'Último ano':
        cutoff = now - timedelta(days=365)
    elif period == 'Personalizado' and date_from and date_to:
        # Filtro personalizado
        mask = (pd.to_datetime(df['Data Modificação']) >= pd.Timestamp(date_from)) & \
               (pd.to_datetime(df['Data Modificação']) <= pd.Timestamp(date_to))
        filtered_df = df[mask]
        filtered_indices = [i for i, m in zip(indices, mask) if m]
        return filtered_df, filtered_indices
    else:
        return df, indices

    # Aplicar filtro de data
    mask = pd.to_datetime(df['Data Modificação']) >= cutoff
    filtered_df = df[mask]
    filtered_indices = [i for i, m in zip(indices, mask) if m]
    return filtered_df, filtered_indices


def _get_read_status(percentage: int) -> int:
    """
    Obtém status de leitura (0=não lido, 1=em andamento, 2=concluído).

    Args:
        percentage: Percentual lido (0-100)

    Returns:
        Status (0, 1 ou 2)
    """
    if percentage == 0:
        return 0
    elif percentage >= 100:
        return 2
    else:
        return 1


def _get_book_status_emoji(asin: str) -> str:
    """
    Obtém emoji de status do livro (novo ou já exportado).

    Args:
        asin: ASIN do livro

    Returns:
        Emoji de status
    """
    history_service = KindleExportHistoryService()
    if history_service.is_exported(asin):
        export_date = history_service.get_export_date(asin)
        if export_date:
            return f"✅ Exportado em {export_date[:10]}"
        return "✅ Exportado"
    return "🆕 Novo"


def _update_export_history(df: pd.DataFrame, selected: List[bool]) -> None:
    """
    Atualiza histórico de exportações.

    Args:
        df: DataFrame com livros
        selected: Lista de booleanos indicando seleção
    """
    try:
        history_service = KindleExportHistoryService()
        asins_to_add = []

        for idx, is_selected in enumerate(selected):
            if is_selected:
                asin = df.iloc[idx].get('ASIN')
                if asin:
                    asins_to_add.append(asin)

        if asins_to_add:
            success = history_service.add_to_history(asins_to_add)
            if success:
                logger.info(f"Histórico atualizado com {len(asins_to_add)} ASINs")
            else:
                logger.warning("Erro ao atualizar histórico")

    except Exception as e:
        logger.error(f"Erro ao atualizar histórico de exportação: {str(e)}")


def _export_selected_books(
    df: pd.DataFrame,
    selected: List[bool],
    library_service: LibraryService,
    temp_csv_path: str
) -> bool:
    """
    Exporta livros selecionados.

    Args:
        df: DataFrame com todos os livros
        selected: Lista de booleanos indicando seleção
        library_service: Serviço de biblioteca
        temp_csv_path: Caminho do CSV temporário

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        # Filtrar apenas selecionados
        selected_indices = [i for i, s in enumerate(selected) if s]
        selected_df = df.iloc[selected_indices].copy()

        if len(selected_df) == 0:
            logger.warning("Nenhum livro selecionado para exportação")
            return False

        # Converter para formato padrão do eBook Manager
        export_df = pd.DataFrame({
            'Nome': selected_df['Nome'],
            'Autor': selected_df['Autor'],
            'Formato': selected_df['Formato'],
            'Tamanho(MB)': selected_df['Tamanho(MB)'],
            'Data Modificação': selected_df['Data Modificação'],
            'Caminho': selected_df['Caminho'],
            'ASIN': selected_df['ASIN'],
            'Origem': selected_df['Origem'],
            'Tipo_Origem': selected_df['Tipo_Origem'],
            'Percentual_Lido': selected_df['Percentual_Lido'],
            'URL_Capa': selected_df['URL_Capa']
        })

        # Salvar CSV final
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_csv_path = os.path.join(gettempdir(), f"ebooks_kindle_selected_{timestamp}.csv")

        export_df.to_csv(final_csv_path, index=False, encoding='utf-8')
        logger.info(f"CSV de exportação salvo em: {final_csv_path}")

        # Armazenar caminho no estado da sessão para importação futura
        st.session_state.last_import_file = final_csv_path

        # Remover arquivo temporário
        try:
            os.remove(temp_csv_path)
            logger.info(f"Arquivo temporário removido: {temp_csv_path}")
        except Exception as e:
            logger.warning(f"Erro ao remover arquivo temporário: {str(e)}")

        return True

    except Exception as e:
        logger.error(f"Erro ao exportar livros selecionados: {str(e)}", exc_info=True)
        return False
