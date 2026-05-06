"""Trade-level analytics for completed round trips."""

from __future__ import annotations

from dataclasses import dataclass

from backtester.portfolio.order import Side, Trade


@dataclass(frozen=True)
class TradePair:
    """A paired long entry and exit trade."""

    entry: Trade
    exit: Trade
    quantity: int
    pnl: float
    return_pct: float
    holding_period_days: int


def pair_trades(trades: list[Trade]) -> list[TradePair]:
    """Pair each BUY with the next SELL and ignore unmatched trades."""
    pairs: list[TradePair] = []
    pending_buy: Trade | None = None
    for trade in trades:
        if trade.side is Side.BUY and pending_buy is None:
            pending_buy = trade
        elif trade.side is Side.SELL and pending_buy is not None:
            quantity = min(pending_buy.quantity, trade.quantity)
            pnl = (trade.price - pending_buy.price) * quantity - pending_buy.commission - trade.commission
            return_pct = (trade.price - pending_buy.price) / pending_buy.price
            holding_period_days = (trade.timestamp.date() - pending_buy.timestamp.date()).days
            pairs.append(
                TradePair(
                    entry=pending_buy,
                    exit=trade,
                    quantity=quantity,
                    pnl=pnl,
                    return_pct=return_pct,
                    holding_period_days=holding_period_days,
                )
            )
            pending_buy = None
    return pairs


def trade_summary(trades: list[Trade]) -> dict[str, object]:
    """Return numeric summary metrics for complete round-trip trades.

    Empty or unavailable numeric values are returned as 0.0 so callers can print
    or serialize the summary without special missing-value handling.
    """
    pairs = pair_trades(trades)
    if not pairs:
        return {
            "total_round_trips": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "max_win": 0.0,
            "max_loss": 0.0,
            "avg_trade_pnl": 0.0,
            "avg_return_pct": 0.0,
            "avg_holding_period_days": 0.0,
            "best_trade_pnl": 0.0,
            "worst_trade_pnl": 0.0,
        }

    pnls = [pair.pnl for pair in pairs]
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    return {
        "total_round_trips": len(pairs),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "win_rate": len(wins) / len(pairs),
        "avg_win": sum(wins) / len(wins) if wins else 0.0,
        "avg_loss": sum(losses) / len(losses) if losses else 0.0,
        "max_win": max(wins) if wins else 0.0,
        "max_loss": min(losses) if losses else 0.0,
        "avg_trade_pnl": sum(pnls) / len(pnls),
        "avg_return_pct": sum(pair.return_pct for pair in pairs) / len(pairs),
        "avg_holding_period_days": sum(pair.holding_period_days for pair in pairs) / len(pairs),
        "best_trade_pnl": max(pnls),
        "worst_trade_pnl": min(pnls),
    }
