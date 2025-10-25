"""
Serviço para gerenciar histórico de exportações Kindle.

Mantém registro de quais livros já foram exportados para evitar
duplicação e permitir que usuário saiba quais livros já foram
sincronizados com o eBook Manager.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple

logger = logging.getLogger(__name__)


class KindleExportHistoryService:
    """
    Gerencia histórico de exportações Kindle.

    Persiste ASINs de livros já exportados em um arquivo JSON
    e fornece métodos para consultar e atualizar o histórico.
    """

    HISTORY_FILE = Path("data") / "kindle_export_history.json"

    def __init__(self):
        """Inicializa o serviço de histórico."""
        self._ensure_history_file()

    def _ensure_history_file(self) -> None:
        """Cria arquivo de histórico se não existir."""
        if not self.HISTORY_FILE.exists():
            self.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            self._save_history({
                "exported_asins": [],
                "export_dates": {}
            })
            logger.info(f"Arquivo de histórico criado em: {self.HISTORY_FILE}")

    def _load_history(self) -> Dict[str, any]:
        """
        Carrega histórico do arquivo.

        Returns:
            Dicionário com histórico ou estrutura padrão se erro
        """
        try:
            if self.HISTORY_FILE.exists():
                with open(self.HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Erro ao carregar histórico: {str(e)}")

        return {
            "exported_asins": [],
            "export_dates": {}
        }

    def _save_history(self, history: Dict[str, any]) -> bool:
        """
        Salva histórico no arquivo.

        Args:
            history: Dicionário com histórico

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            self.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {str(e)}")
            return False

    def add_to_history(self, asins: List[str]) -> bool:
        """
        Adiciona ASINs ao histórico de exportação.

        Args:
            asins: Lista de ASINs para adicionar

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            history = self._load_history()
            now = datetime.now().isoformat()

            for asin in asins:
                if asin not in history["exported_asins"]:
                    history["exported_asins"].append(asin)
                    history["export_dates"][asin] = now

            return self._save_history(history)

        except Exception as e:
            logger.error(f"Erro ao adicionar ao histórico: {str(e)}")
            return False

    def is_exported(self, asin: str) -> bool:
        """
        Verifica se um livro já foi exportado.

        Args:
            asin: ASIN do livro

        Returns:
            True se já foi exportado, False caso contrário
        """
        history = self._load_history()
        return asin in history.get("exported_asins", [])

    def get_exported_asins(self) -> Set[str]:
        """
        Obtém conjunto de ASINs já exportados.

        Returns:
            Set com ASINs exportados
        """
        history = self._load_history()
        return set(history.get("exported_asins", []))

    def get_export_date(self, asin: str) -> Optional[str]:
        """
        Obtém data de exportação de um livro.

        Args:
            asin: ASIN do livro

        Returns:
            ISO timestamp ou None se não encontrado
        """
        history = self._load_history()
        return history.get("export_dates", {}).get(asin)

    def get_all_history(self) -> Dict[str, any]:
        """
        Obtém histórico completo.

        Returns:
            Dicionário com histórico completo
        """
        return self._load_history()

    def clear_history(self) -> bool:
        """
        Limpa todo o histórico.

        Returns:
            True se sucesso, False caso contrário
        """
        return self._save_history({
            "exported_asins": [],
            "export_dates": {}
        })

    def get_statistics(self) -> Dict[str, any]:
        """
        Obtém estatísticas do histórico.

        Returns:
            Dicionário com estatísticas
        """
        history = self._load_history()
        exported_asins = history.get("exported_asins", [])

        return {
            "total_exported": len(exported_asins),
            "first_export": self._get_first_export_date(history),
            "last_export": self._get_last_export_date(history),
            "exports_by_date": self._get_exports_by_date(history)
        }

    @staticmethod
    def _get_first_export_date(history: Dict[str, any]) -> Optional[str]:
        """Obtém data da primeira exportação."""
        dates = history.get("export_dates", {}).values()
        if dates:
            return min(dates)
        return None

    @staticmethod
    def _get_last_export_date(history: Dict[str, any]) -> Optional[str]:
        """Obtém data da última exportação."""
        dates = history.get("export_dates", {}).values()
        if dates:
            return max(dates)
        return None

    @staticmethod
    def _get_exports_by_date(history: Dict[str, any]) -> Dict[str, int]:
        """Conta exportações por data."""
        counts = {}
        for date_iso in history.get("export_dates", {}).values():
            date_str = date_iso.split("T")[0]  # Extrair apenas a data
            counts[date_str] = counts.get(date_str, 0) + 1
        return counts
