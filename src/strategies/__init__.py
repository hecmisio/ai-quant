"""Strategy package exports.

This package separates strategy code into three layers:
- "base": the shared DataFrame-based strategy contract and output validation

Concrete strategy implementations have been removed for now. The package
currently exposes only the shared base contract.
"""

from .base import BaseStrategy

__all__ = ["BaseStrategy"]
