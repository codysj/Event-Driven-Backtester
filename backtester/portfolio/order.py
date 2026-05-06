"""Order and trade primitives for portfolio simulation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Side(Enum):
    """Order or trade direction."""

    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class Order:
    """Intent to buy or sell a quantity of shares."""

    ticker: str
    side: Side
    quantity: int
    timestamp: datetime


@dataclass(frozen=True)
class Trade:
    """Executed order with fill price and commission."""

    ticker: str
    side: Side
    quantity: int
    price: float
    commission: float
    timestamp: datetime

    @property
    def cost(self) -> float:
        """Return cash impact where positive values are cash outflows."""
        gross_value = self.quantity * self.price
        if self.side is Side.BUY:
            return gross_value + self.commission
        return -(gross_value - self.commission)

