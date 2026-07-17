"""Donchian-style momentum breakout on 1-hour candles (BTC/USD).

Entry: close breaks above the prior 20-bar high with volume >= 1.5x the
prior 20-bar average volume. Alpaca crypto is long-only, so a confirmed
breakdown below the prior 20-bar low exits the long instead of reversing
short (set allow_short=True for shortable instruments). A 2x-ATR trailing
stop protects open profits; the risk manager's hard 1-ATR stop caps the
initial loss at 1% of equity.
"""

from typing import Optional

import pandas as pd

import config
from bot.strategies.base import EXIT, LONG, SHORT, Signal, Strategy


class MomentumBreakout(Strategy):
    name = "momentum_breakout"

    def __init__(self, symbol: str, params: dict):
        super().__init__(symbol, params)
        self.period = params.get("period", 20)
        self.volume_mult = params.get("volume_mult", 1.5)
        self.trail_atr_mult = params.get("trail_atr_mult", 2.0)
        self.allow_short = params.get("allow_short", False)

    @property
    def min_bars(self) -> int:
        return max(self.period, config.ATR_PERIOD) + 5

    def evaluate(self, bars: pd.DataFrame, position) -> Optional[Signal]:
        # The breakout is measured against the `period` bars *before* the
        # bar that just closed.
        prior = bars.iloc[-(self.period + 1):-1]
        last = bars.iloc[-1]
        if len(prior) < self.period:
            return None

        breakout_high = prior["high"].max()
        breakout_low = prior["low"].min()
        avg_volume = prior["volume"].mean()
        volume_ok = avg_volume > 0 and last["volume"] >= self.volume_mult * avg_volume

        price = last["close"]

        if position is None:
            if price > breakout_high and volume_ok:
                return Signal(LONG, f"close {price:.2f} broke {self.period}-bar high "
                                    f"{breakout_high:.2f} on {last['volume']:.0f} vol "
                                    f"(avg {avg_volume:.0f})")
            if price < breakout_low and volume_ok and self.allow_short:
                return Signal(SHORT, f"close {price:.2f} broke {self.period}-bar low "
                                     f"{breakout_low:.2f} with volume confirmation")
            return None

        if position.direction == LONG and price < breakout_low and volume_ok:
            action = SHORT if self.allow_short else EXIT
            return Signal(action, f"close {price:.2f} broke {self.period}-bar low "
                                  f"{breakout_low:.2f} with volume confirmation")
        if position.direction == SHORT and price > breakout_high and volume_ok:
            return Signal(LONG, f"close {price:.2f} broke {self.period}-bar high "
                                f"{breakout_high:.2f} with volume confirmation")
        return None
