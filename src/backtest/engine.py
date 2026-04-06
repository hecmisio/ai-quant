"""Shared execution engine for position-based strategy backtests."""

from __future__ import annotations

import pandas as pd


def run_position_backtest(
    data: pd.DataFrame,
    strategy,
    initial_capital: float = 100000.0,
    position_size: float = 1.0,
    fee_rate: float = 0.0001,
    stamp_duty_rate: float = 0.001,
    slippage_rate: float = 0.0005,
    lot_size: int = 100,
) -> pd.DataFrame:
    """Run a simple A-share style backtest for strategies with target positions."""

    _validate_backtest_params(
        initial_capital=initial_capital,
        position_size=position_size,
        fee_rate=fee_rate,
        stamp_duty_rate=stamp_duty_rate,
        slippage_rate=slippage_rate,
        lot_size=lot_size,
    )

    result = strategy.run(data).copy()
    result["daily_return"] = result["close"].pct_change().fillna(0.0)
    result["benchmark_equity"] = (1.0 + result["daily_return"]).cumprod()
    result["benchmark_capital"] = initial_capital * result["benchmark_equity"]

    target_state = result["target_position"].shift(1).fillna(0.0)

    cash = float(initial_capital)
    shares = 0
    state_rows: list[dict] = []

    for idx, row in result.iterrows():
        price = float(row["close"])
        desired_state = float(target_state.loc[idx]) * position_size
        starting_cash = cash
        starting_shares = shares

        trade_shares = 0
        trade_side = "hold"
        fee_amount = 0.0
        stamp_duty_amount = 0.0
        slippage_amount = 0.0
        trade_notional = 0.0
        execution_price = price
        order_value = 0.0

        if desired_state <= 0 and shares > 0:
            execution_price = price * (1.0 - slippage_rate)
            trade_shares = -shares
            trade_notional = abs(trade_shares) * execution_price
            fee_amount = trade_notional * fee_rate
            stamp_duty_amount = trade_notional * stamp_duty_rate
            slippage_amount = abs(trade_shares) * price * slippage_rate
            cash += trade_notional - fee_amount - stamp_duty_amount
            shares = 0
            trade_side = "sell"

        elif desired_state > 0 and shares == 0:
            execution_price = price * (1.0 + slippage_rate)
            equity_before_trade = cash
            order_value = equity_before_trade * desired_state
            max_lots = int(order_value // (execution_price * lot_size))
            candidate_shares = max_lots * lot_size

            while candidate_shares > 0:
                trade_notional = candidate_shares * execution_price
                fee_amount = trade_notional * fee_rate
                total_cost = trade_notional + fee_amount
                if total_cost <= cash + 1e-9:
                    break
                candidate_shares -= lot_size

            if candidate_shares > 0:
                trade_shares = candidate_shares
                trade_notional = trade_shares * execution_price
                fee_amount = trade_notional * fee_rate
                slippage_amount = trade_shares * price * slippage_rate
                cash -= trade_notional + fee_amount
                shares += trade_shares
                trade_side = "buy"
            else:
                trade_notional = 0.0
                fee_amount = 0.0

        holdings_value = shares * price
        strategy_capital = cash + holdings_value
        strategy_equity = strategy_capital / initial_capital

        state_rows.append(
            {
                "desired_position": desired_state,
                "cash": cash,
                "shares": shares,
                "holdings_value": holdings_value,
                "strategy_capital": strategy_capital,
                "strategy_equity": strategy_equity,
                "position_for_return": (holdings_value / strategy_capital) if strategy_capital > 0 else 0.0,
                "cash_exposure": (cash / strategy_capital) if strategy_capital > 0 else 1.0,
                "trade_side": trade_side,
                "trade_shares": trade_shares,
                "trade_notional": trade_notional,
                "execution_price": execution_price,
                "order_value": order_value,
                "fee_amount": fee_amount,
                "stamp_duty_amount": stamp_duty_amount,
                "slippage_amount": slippage_amount,
                "starting_cash": starting_cash,
                "starting_shares": starting_shares,
            }
        )

    result = pd.concat([result, pd.DataFrame(state_rows, index=result.index)], axis=1)
    result["gross_strategy_return"] = result["strategy_capital"].pct_change().fillna(
        result["strategy_capital"].iloc[0] / initial_capital - 1.0
    )
    result["trade_turnover"] = result["trade_notional"] / initial_capital
    result["fee_return"] = result["fee_amount"] / initial_capital
    result["stamp_duty_return"] = result["stamp_duty_amount"] / initial_capital
    result["slippage_return"] = result["slippage_amount"] / initial_capital
    result["strategy_return"] = result["strategy_equity"].pct_change().fillna(
        result["strategy_equity"].iloc[0] - 1.0
    )

    strategy_peak = result["strategy_equity"].cummax()
    benchmark_peak = result["benchmark_equity"].cummax()
    result["drawdown"] = result["strategy_equity"] / strategy_peak - 1.0
    result["benchmark_drawdown"] = result["benchmark_equity"] / benchmark_peak - 1.0
    result.attrs["initial_capital"] = float(initial_capital)
    result.attrs["position_size"] = float(position_size)
    result.attrs["fee_rate"] = float(fee_rate)
    result.attrs["stamp_duty_rate"] = float(stamp_duty_rate)
    result.attrs["slippage_rate"] = float(slippage_rate)
    result.attrs["lot_size"] = int(lot_size)
    result.attrs["strategy_params"] = strategy.get_params()
    return result


def _validate_backtest_params(
    *,
    initial_capital: float,
    position_size: float,
    fee_rate: float,
    stamp_duty_rate: float,
    slippage_rate: float,
    lot_size: int,
) -> None:
    if initial_capital <= 0:
        raise ValueError("initial_capital must be positive")
    if not 0 <= position_size <= 1:
        raise ValueError("position_size must be between 0 and 1")
    if fee_rate < 0:
        raise ValueError("fee_rate must not be negative")
    if stamp_duty_rate < 0:
        raise ValueError("stamp_duty_rate must not be negative")
    if slippage_rate < 0:
        raise ValueError("slippage_rate must not be negative")
    if lot_size <= 0:
        raise ValueError("lot_size must be positive")
