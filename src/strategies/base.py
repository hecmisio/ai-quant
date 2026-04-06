"""Base interface for trading strategies."""


class BaseStrategy:
    """Minimal strategy contract for future implementations."""

    def prepare_data(self, data):
        return data

    def generate_signals(self, data):
        raise NotImplementedError

    def build_positions(self, signals):
        return signals

    def get_params(self):
        return {}
