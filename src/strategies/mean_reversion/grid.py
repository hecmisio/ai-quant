"""Grid strategy implementation."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.strategies.base import BaseStrategy


@dataclass(frozen=True)
class GridParams:
    """Configuration for fixed-range grid signal generation."""

    lower_bound: float
    upper_bound: float
    grid_count: int
    price_column: str = "close"


class GridStrategy(BaseStrategy):
    """Long-only fixed-range grid strategy using DataFrame market data input.

    Input contract:
    - Accepts a time-ordered ``pandas.DataFrame``.
    - Requires a numeric price column named ``close`` by default.
    - Preserves the input index and original row order in all outputs.

    Output contract:
    - ``generate_signals`` returns the input data plus grid metadata columns,
      ``signal``, ``target_position``, and ``is_valid_signal_row``.
    - ``build_positions`` is a pass-through because target positions are
      determined directly during signal generation.
    """

    def __init__(
        self,
        lower_bound: float,
        upper_bound: float,
        grid_count: int,
        price_column: str = "close",
    ) -> None:
        self.params = GridParams(
            lower_bound=float(lower_bound),
            upper_bound=float(upper_bound),
            grid_count=int(grid_count),
            price_column=price_column,
        )
        self._validate_params()

    def _validate_params(self) -> None:
        if self.params.lower_bound >= self.params.upper_bound:
            raise ValueError("lower_bound must be less than upper_bound")
        if self.params.grid_count <= 0:
            raise ValueError("grid_count must be a positive integer")
        if not self.params.price_column:
            raise ValueError("price_column must be a non-empty string")

    def _build_grid_levels(self) -> list[float]:
        spacing = self.grid_spacing
        return [
            self.params.lower_bound + spacing * step
            for step in range(self.params.grid_count + 1)
        ]

    @property
    def grid_spacing(self) -> float:
        return (self.params.upper_bound - self.params.lower_bound) / self.params.grid_count

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

    def _bucket_for_price(self, price: float) -> int:
        if price <= self.params.lower_bound:
            return 0
        if price >= self.params.upper_bound:
            return self.params.grid_count

        offset = price - self.params.lower_bound
        bucket = int(offset / self.grid_spacing)
        return min(max(bucket, 0), self.params.grid_count - 1)

    def _position_for_bucket(self, bucket: int) -> float:
        return round((self.params.grid_count - bucket) / self.params.grid_count, 10)

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        prepared = self.prepare_data(data)
        price_series = prepared[self.params.price_column]
        grid_levels = self._build_grid_levels()
        valid_row = price_series.notna()

        bucket_values: list[int | None] = []
        bucket_lower_values: list[float | None] = []
        bucket_upper_values: list[float | None] = []
        target_positions: list[float] = []
        signals: list[str] = []

        previous_valid_target = 0.0

        for idx, price in price_series.items():
            if not valid_row.loc[idx]:
                bucket_values.append(None)
                bucket_lower_values.append(None)
                bucket_upper_values.append(None)
                target_positions.append(0.0)
                signals.append("hold")
                continue

            bucket = self._bucket_for_price(float(price))
            bucket_values.append(bucket)
            target_position = self._position_for_bucket(bucket)
            target_positions.append(target_position)

            if bucket >= self.params.grid_count:
                bucket_lower_values.append(grid_levels[-1])
                bucket_upper_values.append(None)
            else:
                bucket_lower_values.append(grid_levels[bucket])
                bucket_upper_values.append(grid_levels[bucket + 1])

            if target_position > previous_valid_target:
                signal = "buy"
            elif target_position < previous_valid_target:
                signal = "sell"
            else:
                signal = "hold"
            signals.append(signal)
            previous_valid_target = target_position

        result = prepared.copy()
        result["grid_lower_bound"] = self.params.lower_bound
        result["grid_upper_bound"] = self.params.upper_bound
        result["grid_count"] = self.params.grid_count
        result["grid_spacing"] = self.grid_spacing
        result["grid_bucket"] = pd.Series(bucket_values, index=result.index, dtype="Int64")
        result["grid_bucket_lower"] = bucket_lower_values
        result["grid_bucket_upper"] = bucket_upper_values
        result["signal"] = signals
        result["target_position"] = target_positions
        result["is_valid_signal_row"] = valid_row
        result.attrs["grid_levels"] = grid_levels
        result.attrs["grid_spacing"] = self.grid_spacing
        return result

    def build_positions(self, signals: pd.DataFrame) -> pd.DataFrame:
        if "target_position" not in signals.columns:
            raise ValueError("signals data must include 'target_position' column")
        return signals.copy()

    def run(self, data: pd.DataFrame) -> pd.DataFrame:
        """Convenience wrapper for strategy execution."""

        return self.build_positions(self.generate_signals(data))

    def get_params(self) -> dict:
        return {
            "lower_bound": self.params.lower_bound,
            "upper_bound": self.params.upper_bound,
            "grid_count": self.params.grid_count,
            "price_column": self.params.price_column,
        }
