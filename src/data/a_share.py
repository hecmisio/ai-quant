"""Compatibility facade for A-share market-data helpers."""

from src.adapters.outbound.market_data.akshare_a_share import AkShareAStockListProvider
from src.domain.market_data.a_share import (
    STOCK_LIST_COLUMNS,
    filter_a_share_stocks,
    filter_st_stocks,
    infer_exchange,
    infer_market,
    is_b_share,
    is_st_stock,
    normalize_a_share_stock_list,
)


def fetch_a_share_stock_list(*, include_st: bool = False, fetcher=None):
    provider = AkShareAStockListProvider(fetcher=fetcher)
    return provider.fetch_stock_list(include_st=include_st)
