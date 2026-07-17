"""Bollinger-style mean reversion on 15-minute candles (SPY, QQQ).

Entry: close beyond `band` standard deviations from the 20-period SMA
(long below the lower band, short above the upper band).
Exit: close crosses back to the SMA. The hard 1-ATR stop from the risk
manager backstops every position; there is no trailing stop.
"""

import math
from typing import Optional

import pandas as pd

import config
from bot.indicators import rolling_std, sma
from bot.strategies.base import EXIT, LONG, SHORT, Signal, Strategy


class MeanReversion(Strategy):
    name = "mean_reversion"
    trail_atr_mult = None

    def __init__(self, symbol: str, params: dict):
        super().__init__(symbol, params)
        self.period = params.get("period", 20)
        self.band = params["band"]

    @property
    def min_bars(self) -> int:
        return max(self.period, config.ATR_PERIOD) + 5

    def evaluate(self, bars: pd.DataFrame, position) -> Optional[Signal]:
        close = bars["close"]
        mean = sma(close, self.period).iloc[-1]
        std = rolling_std(close, self.period).iloc[-1]
        price = close.iloc[-1]
        if math.isnan(mean) or math.isnan(std) or std <= 0:
            return None

        upper = mean + self.band * std
        lower = mean - self.band * std

        if position is None:
            if price < lower:
                return Signal(LONG, f"close {price:.2f} < lower band {lower:.2f} "
                                    f"({self.band} std below {mean:.2f})")
            if price > upper:
                return Signal(SHORT, f"close {price:.2f} > upper band {upper:.2f} "
                                     f"({self.band} std above {mean:.2f})")
            return None

        if position.direction == LONG and price >= mean:
            return Signal(EXIT, f"close {price:.2f} reverted to SMA {mean:.2f}")
        if position.direction == SHORT and price <= mean:
            return Signal(EXIT, f"close {price:.2f} reverted to SMA {mean:.2f}")
        return None
