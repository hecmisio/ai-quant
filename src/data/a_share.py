"""Utilities for fetching and normalizing the A-share stock universe."""

from __future__ import annotations

import re
from typing import Any, Callable

import pandas as pd


STOCK_LIST_COLUMNS = ["symbol", "name", "exchange", "market"]
B_SHARE_PREFIXES = ("900", "200")
_ST_NAME_PATTERN = re.compile(r"^\*?ST", re.IGNORECASE)


def _load_akshare() -> Any:
    try:
        import akshare as ak  # type: ignore
    except ImportError as exc:
        raise RuntimeError("akshare is required to fetch the A-share stock list") from exc
    return ak


def infer_exchange(symbol: str) -> str:
    """Infer the exchange code from a mainland China security symbol."""

    code = str(symbol).strip()
    if code.startswith(("600", "601", "603", "605", "688", "689", "900")):
        return "SSE"
    if code.startswith(("000", "001", "002", "003", "200", "300", "301")):
        return "SZSE"
    if code.startswith(
        (
            "430",
            "440",
            "830",
            "831",
            "832",
            "833",
            "834",
            "835",
            "836",
            "837",
            "838",
            "839",
            "870",
            "871",
            "872",
            "873",
            "874",
            "875",
            "876",
            "877",
            "878",
            "879",
            "880",
            "881",
            "882",
            "883",
            "884",
            "885",
            "886",
            "887",
            "888",
            "889",
            "920",
        )
    ):
        return "BSE"
    return "UNKNOWN"


def infer_market(symbol: str, exchange: str | None = None) -> str:
    """Infer a coarse-grained market bucket for an A-share symbol."""

    code = str(symbol).strip()
    exchange_code = exchange or infer_exchange(code)
    if exchange_code == "SSE":
        if code.startswith("688"):
            return "STAR"
        if code.startswith("900"):
            return "B_SHARE"
        return "MAIN"
    if exchange_code == "SZSE":
        if code.startswith(("300", "301")):
            return "CHINEXT"
        if code.startswith("200"):
            return "B_SHARE"
        return "MAIN"
    if exchange_code == "BSE":
        return "BSE"
    return "UNKNOWN"


def _resolve_raw_columns(frame: pd.DataFrame) -> tuple[str, str]:
    code_candidates = ("code", "symbol", "证券代码", "股票代码")
    name_candidates = ("name", "简称", "名称", "股票简称", "证券简称")

    code_column = next((column for column in code_candidates if column in frame.columns), None)
    name_column = next((column for column in name_candidates if column in frame.columns), None)
    if code_column is None or name_column is None:
        raise ValueError(f"unable to map AkShare stock list columns: {list(frame.columns)}")
    return code_column, name_column


def normalize_a_share_stock_list(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Normalize the raw AkShare A-share list to stable project-facing columns."""

    code_column, name_column = _resolve_raw_columns(raw_data)
    normalized = pd.DataFrame(
        {
            "symbol": raw_data[code_column].astype(str).str.strip(),
            "name": raw_data[name_column].astype(str).str.strip(),
        }
    )
    normalized = normalized[normalized["symbol"] != ""].copy()
    normalized["exchange"] = normalized["symbol"].map(infer_exchange)
    normalized["market"] = normalized.apply(
        lambda row: infer_market(row["symbol"], row["exchange"]),
        axis=1,
    )
    return normalized[STOCK_LIST_COLUMNS].drop_duplicates(ignore_index=True)


def is_b_share(symbol: str) -> bool:
    """Return whether a symbol belongs to the historical B-share code ranges."""

    code = str(symbol).strip()
    return code.startswith(B_SHARE_PREFIXES)


def filter_a_share_stocks(stock_list: pd.DataFrame) -> pd.DataFrame:
    """Keep only A-share symbols and drop B-share code ranges."""

    filtered = stock_list[~stock_list["symbol"].map(is_b_share)].copy()
    return filtered.reset_index(drop=True)


def is_st_stock(name: str) -> bool:
    """Return whether a stock name is flagged as ST or *ST."""

    normalized_name = str(name).strip().replace(" ", "").upper()
    return bool(_ST_NAME_PATTERN.match(normalized_name))


def filter_st_stocks(stock_list: pd.DataFrame) -> pd.DataFrame:
    """Remove ST and *ST stocks from a normalized stock list."""

    filtered = stock_list[~stock_list["name"].map(is_st_stock)].copy()
    return filtered.reset_index(drop=True)


def fetch_a_share_stock_list(
    *,
    include_st: bool = False,
    fetcher: Callable[[], pd.DataFrame] | None = None,
) -> pd.DataFrame:
    """Fetch, normalize, and optionally filter the A-share stock universe."""

    resolved_fetcher = fetcher
    if resolved_fetcher is None:
        ak = _load_akshare()
        resolved_fetcher = ak.stock_info_a_code_name

    raw_data = resolved_fetcher()
    normalized = normalize_a_share_stock_list(raw_data)
    normalized = filter_a_share_stocks(normalized)
    if include_st:
        return normalized
    return filter_st_stocks(normalized)
