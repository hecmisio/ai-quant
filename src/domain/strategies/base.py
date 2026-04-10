"""Pure strategy contract definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class BaseStrategy(ABC):
    """Shared strategy contract for DataFrame-based signal generators."""

    SIGNAL_COLUMN = "signal"
    TARGET_POSITION_COLUMN = "target_position"
    VALID_SIGNALS = frozenset({"buy", "sell", "hold"})

    def prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        return data

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    def build_positions(self, signals: pd.DataFrame) -> pd.DataFrame:
        return signals

    def run(self, data: pd.DataFrame) -> pd.DataFrame:
        signal_frame = self.generate_signals(data)
        self.validate_signal_output(signal_frame)
        positioned = self.build_positions(signal_frame)
        self.validate_position_output(positioned)
        return positioned

    @abstractmethod
    def get_params(self) -> dict:
        raise NotImplementedError

    def validate_signal_output(self, signals: pd.DataFrame) -> None:
        if not isinstance(signals, pd.DataFrame):
            raise TypeError("strategy signals must be returned as a pandas DataFrame")
        if self.SIGNAL_COLUMN not in signals.columns:
            raise ValueError(f"strategy signals must include '{self.SIGNAL_COLUMN}' column")

        signal_values = signals[self.SIGNAL_COLUMN].dropna()
        invalid_signals = sorted(set(signal_values.tolist()) - set(self.VALID_SIGNALS))
        if invalid_signals:
            raise ValueError(
                "strategy signals contain unsupported values: "
                + ", ".join(str(value) for value in invalid_signals)
            )

    def validate_position_output(self, positioned: pd.DataFrame) -> None:
        self.validate_signal_output(positioned)
        if self.TARGET_POSITION_COLUMN not in positioned.columns:
            raise ValueError(
                f"strategy position output must include '{self.TARGET_POSITION_COLUMN}' column"
            )

        numeric_positions = pd.to_numeric(positioned[self.TARGET_POSITION_COLUMN], errors="coerce")
        if numeric_positions.isna().any():
            raise ValueError("target_position column must be numeric for every row")
