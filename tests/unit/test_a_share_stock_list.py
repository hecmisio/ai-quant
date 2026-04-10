"""Tests for A-share stock universe fetching and filtering."""

from __future__ import annotations

import pandas as pd

from src.adapters.outbound.market_data.akshare_a_share import AkShareAStockListProvider
from src.domain.market_data.a_share import (
    fetch_a_share_stock_list,
    filter_a_share_stocks,
    filter_st_stocks,
    normalize_a_share_stock_list,
)


def test_normalize_a_share_stock_list_maps_fields() -> None:
    raw = pd.DataFrame(
        {
            "code": ["600519", "300750", "830799", "900901"],
            "name": ["贵州茅台", "宁德时代", "艾融软件", "云赛B股"],
        }
    )

    result = normalize_a_share_stock_list(raw)

    assert list(result.columns) == ["symbol", "name", "exchange", "market"]
    assert result.to_dict("records") == [
        {"symbol": "600519", "name": "贵州茅台", "exchange": "SSE", "market": "MAIN"},
        {"symbol": "300750", "name": "宁德时代", "exchange": "SZSE", "market": "CHINEXT"},
        {"symbol": "830799", "name": "艾融软件", "exchange": "BSE", "market": "BSE"},
        {"symbol": "900901", "name": "云赛B股", "exchange": "SSE", "market": "B_SHARE"},
    ]


def test_filter_a_share_stocks_excludes_b_share_prefixes() -> None:
    stock_list = pd.DataFrame(
        {
            "symbol": ["600519", "900901", "000001", "200002"],
            "name": ["贵州茅台", "云赛B股", "平安银行", "万科B"],
            "exchange": ["SSE", "SSE", "SZSE", "SZSE"],
            "market": ["MAIN", "B_SHARE", "MAIN", "B_SHARE"],
        }
    )

    result = filter_a_share_stocks(stock_list)

    assert result["symbol"].tolist() == ["600519", "000001"]


def test_filter_st_stocks_excludes_st_and_star_st() -> None:
    stock_list = pd.DataFrame(
        {
            "symbol": ["600519", "000001", "000002", "300750"],
            "name": ["贵州茅台", "ST平安", "*ST万科", "宁德时代"],
            "exchange": ["SSE", "SZSE", "SZSE", "SZSE"],
            "market": ["MAIN", "MAIN", "MAIN", "CHINEXT"],
        }
    )

    result = filter_st_stocks(stock_list)

    assert result["symbol"].tolist() == ["600519", "300750"]
    assert result["name"].tolist() == ["贵州茅台", "宁德时代"]


def test_fetch_a_share_stock_list_filters_st_and_b_shares_by_default() -> None:
    def fake_fetcher() -> pd.DataFrame:
        return pd.DataFrame(
            {
                "code": ["600519", "000001", "300750", "900901", "200002"],
                "name": ["贵州茅台", "ST样本", "宁德时代", "云赛B股", "万科B"],
            }
        )

    result = fetch_a_share_stock_list(fetcher=fake_fetcher)

    assert result["symbol"].tolist() == ["600519", "300750"]


def test_fetch_a_share_stock_list_can_include_st_but_not_b_shares() -> None:
    def fake_fetcher() -> pd.DataFrame:
        return pd.DataFrame(
            {
                "code": ["600519", "000001", "200002"],
                "name": ["贵州茅台", "*ST样本", "万科B"],
            }
        )

    result = fetch_a_share_stock_list(fetcher=fake_fetcher, include_st=True)

    assert result["symbol"].tolist() == ["600519", "000001"]


def test_akshare_provider_implements_provider_port_with_custom_fetcher() -> None:
    provider = AkShareAStockListProvider(
        fetcher=lambda: pd.DataFrame({"code": ["600519", "200002"], "name": ["贵州茅台", "万科B"]})
    )

    result = provider.fetch_stock_list(include_st=False)

    assert result["symbol"].tolist() == ["600519"]
