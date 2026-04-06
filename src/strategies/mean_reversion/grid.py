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
    - Accepts a time-ordered "pandas.DataFrame".
    - Requires a numeric price column named "close" by default.
    - Preserves the input index and original row order in all outputs.

    Output contract:
    - "generate_signals" returns the input data plus grid metadata columns,
      "signal", "target_position", and "is_valid_signal_row".
    - "build_positions" is a pass-through because target positions are
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

    def _bucket_bounds(
        self, bucket: int, grid_levels: list[float]
    ) -> tuple[float, float | None]:
        if bucket >= self.params.grid_count:
            return grid_levels[-1], None
        return grid_levels[bucket], grid_levels[bucket + 1]

    def _signal_for_target_change(
        self, previous_valid_target: float, current_target: float
    ) -> str:
        if current_target > previous_valid_target:
            return "buy"
        if current_target < previous_valid_target:
            return "sell"
        return "hold"

    def _fallback_row_state(self) -> dict[str, int | float | None | str]:
        return {
            "grid_bucket": None,
            "grid_bucket_lower": None,
            "grid_bucket_upper": None,
            "target_position": 0.0,
            "signal": "hold",
        }

    def _row_state_for_price(
        self, price: float, previous_valid_target: float, grid_levels: list[float]
    ) -> dict[str, int | float | None | str]:
        bucket = self._bucket_for_price(price)
        target_position = self._position_for_bucket(bucket)
        bucket_lower, bucket_upper = self._bucket_bounds(bucket, grid_levels)
        signal = self._signal_for_target_change(previous_valid_target, target_position)
        return {
            "grid_bucket": bucket,
            "grid_bucket_lower": bucket_lower,
            "grid_bucket_upper": bucket_upper,
            "target_position": target_position,
            "signal": signal,
        }

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
                row_state = self._fallback_row_state()
                bucket_values.append(row_state["grid_bucket"])
                bucket_lower_values.append(row_state["grid_bucket_lower"])
                bucket_upper_values.append(row_state["grid_bucket_upper"])
                target_positions.append(float(row_state["target_position"]))
                signals.append(str(row_state["signal"]))
                continue

            row_state = self._row_state_for_price(
                float(price), previous_valid_target, grid_levels
            )
            bucket_values.append(int(row_state["grid_bucket"]))
            bucket_lower_values.append(float(row_state["grid_bucket_lower"]))
            bucket_upper_values.append(row_state["grid_bucket_upper"])
            target_position = float(row_state["target_position"])
            target_positions.append(target_position)
            signals.append(str(row_state["signal"]))
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
        self.validate_signal_output(signals)
        if self.TARGET_POSITION_COLUMN not in signals.columns:
            raise ValueError("signals data must include 'target_position' column")
        return signals.copy()

    def get_params(self) -> dict:
        return {
            "lower_bound": self.params.lower_bound,
            "upper_bound": self.params.upper_bound,
            "grid_count": self.params.grid_count,
            "price_column": self.params.price_column,
        }
