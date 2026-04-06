"""Strategy package exports.

This package separates strategy code into three layers:
- "base": the shared DataFrame-based strategy contract and output validation
- "trend": trend-following strategies such as MACD
- "mean_reversion": range-bound or mean-reversion strategies such as grid

External callers should usually import concrete strategies from this package
root unless they need direct access to a category subpackage.
"""

from .base import BaseStrategy
from .mean_reversion import GridStrategy
from .trend import MACDStrategy

__all__ = ["BaseStrategy", "GridStrategy", "MACDStrategy"]
