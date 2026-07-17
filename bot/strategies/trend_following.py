"""EMA-cross trend following on 4-hour candles (GLD, USO).

Entry: 50-period EMA crosses above the 200-period EMA (golden cross) -> long.
The 50 EMA crossing below the 200 EMA (death cross) exits the long and opens
a short. A 3x-ATR trailing stop rides the trend; the risk manager's hard
1-ATR stop caps the initial loss at 1% of equity.
"""

import math
from typing import Optional

import pandas as pd

import config
from bot.indicators import ema
from bot.strategies.base import EXIT, LONG, SHORT, Signal, Strategy


class TrendFollowing(Strategy):
    name = "trend_following"

    def __init__(self, symbol: str, params: dict):
        super().__init__(symbol, params)
        self.fast = params.get("fast", 50)
        self.slow = params.get("slow", 200)
        self.trail_atr_mult = params.get("trail_atr_mult", 3.0)
        self.allow_short = params.get("allow_short", True)

    @property
    def min_bars(self) -> int:
        # Extra warmup bars so the slow EMA has converged reasonably.
        return self.slow + 60

    def evaluate(self, bars: pd.DataFrame, position) -> Optional[Signal]:
        close = bars["close"]
        fast = ema(close, self.fast)
        slow = ema(close, self.slow)
        prev_diff = fast.iloc[-2] - slow.iloc[-2]
        curr_diff = fast.iloc[-1] - slow.iloc[-1]
        if math.isnan(prev_diff) or math.isnan(curr_diff):
            return None

        golden_cross = prev_diff <= 0 < curr_diff
        death_cross = prev_diff >= 0 > curr_diff

        if golden_cross:
            if position is None or position.direction == SHORT:
                return Signal(LONG, f"{self.fast} EMA crossed above {self.slow} EMA "
                                    f"({fast.iloc[-1]:.2f} > {slow.iloc[-1]:.2f})")
        if death_cross:
            reason = (f"{self.fast} EMA crossed below {self.slow} EMA "
                      f"({fast.iloc[-1]:.2f} < {slow.iloc[-1]:.2f})")
            if position is not None and position.direction == LONG and not self.allow_short:
                return Signal(EXIT, reason)
            if position is None or position.direction == LONG:
                return Signal(SHORT if self.allow_short else EXIT, reason)
        return None
