"""Common strategy interface.

A strategy is a pure function of (bars, current position) -> Signal. It never
talks to the broker; sizing, stops, and order routing belong to the risk
manager and portfolio.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import pandas as pd

LONG = "long"
SHORT = "short"
EXIT = "exit"


@dataclass
class Signal:
    action: str  # LONG, SHORT, or EXIT
    reason: str


class Strategy(ABC):
    name: str = "base"
    # ATR multiple for the trailing stop; None means no trailing stop
    # (the hard 1-ATR stop from the risk manager still applies).
    trail_atr_mult: Optional[float] = None
    allow_short: bool = True

    def __init__(self, symbol: str, params: dict):
        self.symbol = symbol
        self.params = params

    @property
    @abstractmethod
    def min_bars(self) -> int:
        """Minimum completed bars needed before evaluate() is meaningful."""

    @abstractmethod
    def evaluate(self, bars: pd.DataFrame, position) -> Optional[Signal]:
        """Return a Signal, or None when nothing should change.

        `bars` contains only completed candles, oldest first, with columns
        open/high/low/close/volume. `position` is the currently open
        bot.portfolio.Position for this symbol, or None when flat.
        """
