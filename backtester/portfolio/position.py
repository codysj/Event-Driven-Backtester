"""Mutable position state for a single ticker."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Position:
    """Current holdings and average entry price for one ticker."""

    ticker: str
    quantity: int
    avg_entry_price: float

    def update_on_buy(self, additional_qty: int, price: float) -> None:
        """Increase the position and recompute weighted average entry price."""
        if additional_qty <= 0:
            msg = "additional_qty must be positive."
            raise ValueError(msg)
        if price <= 0:
            msg = "price must be positive."
            raise ValueError(msg)

        current_value = self.quantity * self.avg_entry_price
        additional_value = additional_qty * price
        new_quantity = self.quantity + additional_qty
        self.quantity = new_quantity
        self.avg_entry_price = (current_value + additional_value) / new_quantity

    def update_on_sell(self, sell_qty: int) -> None:
        """Reduce the position without changing average entry price."""
        if sell_qty <= 0:
            msg = "sell_qty must be positive."
            raise ValueError(msg)
        if sell_qty > self.quantity:
            msg = "sell_qty cannot exceed current position quantity."
            raise ValueError(msg)

        self.quantity -= sell_qty

