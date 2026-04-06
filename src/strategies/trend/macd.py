"""MACD trend strategy implementation."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.strategies.base import BaseStrategy


@dataclass(frozen=True)
class MACDParams:
    """Configuration for MACD indicator and signal generation."""

    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9
    zero_axis_filter: bool = False
    price_column: str = "close"


class MACDStrategy(BaseStrategy):
    """Long-only MACD strategy using DataFrame market data input.

    Input contract:
    - Accepts a time-ordered "pandas.DataFrame".
    - Requires a numeric price column named "close" by default.
    - Preserves the input index and original row order in all outputs.

    Output contract:
    - "generate_signals" returns the input data plus "dif", "dea",
      "histogram", "signal", and "is_valid_signal_row".
    - "build_positions" adds "target_position" with long-only states "0" or "1".
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        zero_axis_filter: bool = False,
        price_column: str = "close",
    ) -> None:
        self.params = MACDParams(
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            zero_axis_filter=zero_axis_filter,
            price_column=price_column,
        )
        self._validate_params()

    def _validate_params(self) -> None:
        if self.params.fast_period <= 0:
            raise ValueError("fast_period must be a positive integer")
        if self.params.slow_period <= 0:
            raise ValueError("slow_period must be a positive integer")
        if self.params.signal_period <= 0:
            raise ValueError("signal_period must be a positive integer")
        if self.params.fast_period >= self.params.slow_period:
            raise ValueError("fast_period must be less than slow_period")
        if not self.params.price_column:
            raise ValueError("price_column must be a non-empty string")

    def prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(data, pd.DataFrame):
            raise TypeError("data must be a pandas DataFrame")
        if self.params.price_column not in data.columns:
            raise ValueError(f"input data must include '{self.params.price_column}' column")

        prepared = data.copy()
        prepared[self.params.price_column] = pd.to_numeric(
            prepared[self.params.price_column], errors="coerce"
        )
        return prepared

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        prepared = self.prepare_data(data)
        close = prepared[self.params.price_column]

        fast_ema = close.ewm(
            span=self.params.fast_period,
            adjust=False,
            min_periods=self.params.fast_period,
        ).mean()
        slow_ema = close.ewm(
            span=self.params.slow_period,
            adjust=False,
            min_periods=self.params.slow_period,
        ).mean()
        dif = fast_ema - slow_ema
        dea = dif.ewm(
            span=self.params.signal_period,
            adjust=False,
            min_periods=self.params.signal_period,
        ).mean()
        histogram = dif - dea

        valid_row = close.notna() & dif.notna() & dea.notna() & histogram.notna()
        prev_dif = dif.shift(1)
        prev_dea = dea.shift(1)

        buy_mask = valid_row & (prev_dif <= prev_dea) & (dif > dea)
        if self.params.zero_axis_filter:
            buy_mask &= dif >= 0
        sell_mask = valid_row & (prev_dif >= prev_dea) & (dif < dea)

        signals = pd.Series("hold", index=prepared.index, dtype="object")
        signals.loc[buy_mask] = "buy"
        signals.loc[sell_mask] = "sell"

        result = prepared.copy()
        result["dif"] = dif
        result["dea"] = dea
        result["histogram"] = histogram
        result["signal"] = signals
        result["is_valid_signal_row"] = valid_row
        return result

    def build_positions(self, signals: pd.DataFrame) -> pd.DataFrame:
        if "signal" not in signals.columns:
            raise ValueError("signals data must include 'signal' column")

        signal_frame = signals.copy()
        valid_row = signal_frame.get("is_valid_signal_row")
        if valid_row is None:
            valid_row = pd.Series(True, index=signal_frame.index, dtype="bool")

        current_position = 0
        positions = []
        for idx, signal in signal_frame["signal"].items():
            if not bool(valid_row.loc[idx]):
                current_position = 0
            elif signal == "buy":
                current_position = 1
            elif signal == "sell":
                current_position = 0
            positions.append(current_position)

        signal_frame["target_position"] = positions
        return signal_frame

    def run(self, data: pd.DataFrame) -> pd.DataFrame:
        """Convenience wrapper for strategy execution."""

        return self.build_positions(self.generate_signals(data))

    def get_params(self) -> dict:
        return {
            "fast_period": self.params.fast_period,
            "slow_period": self.params.slow_period,
            "signal_period": self.params.signal_period,
            "zero_axis_filter": self.params.zero_axis_filter,
            "price_column": self.params.price_column,
        }
