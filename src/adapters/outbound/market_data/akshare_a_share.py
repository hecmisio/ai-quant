"""AkShare adapter for the A-share stock-list provider port."""

from __future__ import annotations

from typing import Any, Callable

import pandas as pd

from src.domain.market_data.a_share import fetch_a_share_stock_list


def _load_akshare() -> Any:
    try:
        import akshare as ak  # type: ignore
    except ImportError as exc:
        raise RuntimeError("akshare is required to fetch the A-share stock list") from exc
    return ak


class AkShareAStockListProvider:
    """Adapter that fetches the normalized A-share stock list from AkShare."""

    def __init__(self, fetcher: Callable[[], pd.DataFrame] | None = None):
        self._fetcher = fetcher

    def fetch_stock_list(self, *, include_st: bool = False) -> pd.DataFrame:
        resolved_fetcher = self._fetcher
        if resolved_fetcher is None:
            ak = _load_akshare()
            resolved_fetcher = ak.stock_info_a_code_name
        return fetch_a_share_stock_list(include_st=include_st, fetcher=resolved_fetcher)
