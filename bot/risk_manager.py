"""Position sizing, stop placement, and the cross-instrument correlation filter.

Sizing rule: a 1-ATR adverse move must equal RISK_PER_TRADE (1%) of account
equity, so qty = (equity * 1%) / ATR. Because of that sizing, the hard stop
placed 1 ATR from entry caps the loss on any trade at 1% of equity. The
per-strategy ATR trailing stops only ever tighten that stop — whichever stop
is tighter wins, so the 1% maximum loss always holds.
"""

import logging
import math
from typing import Dict, Optional

import config
from bot.strategies.base import LONG, SHORT

log = logging.getLogger("bot.risk")


class RiskManager:
    def __init__(self,
                 risk_per_trade: float = config.RISK_PER_TRADE,
                 max_notional_pct: float = config.MAX_POSITION_NOTIONAL_PCT):
        self.risk_per_trade = risk_per_trade
        self.max_notional_pct = max_notional_pct

    def position_size(self, equity: float, atr: float, price: float,
                      fractional: bool) -> float:
        """Quantity such that a 1 ATR move against us costs risk_per_trade of
        equity, capped so the notional never exceeds max_notional_pct of equity.
        """
        if atr is None or math.isnan(atr) or atr <= 0 or price <= 0 or equity <= 0:
            return 0.0
        qty = (equity * self.risk_per_trade) / atr
        max_qty = (equity * self.max_notional_pct) / price
        if qty > max_qty:
            log.info("Sizing capped by notional limit: %.4f -> %.4f", qty, max_qty)
            qty = max_qty
        if fractional:
            return math.floor(qty * 1e6) / 1e6  # 6 dp, rounded down
        return float(math.floor(qty))

    def initial_stop(self, entry_price: float, atr: float, direction: str) -> float:
        """Hard stop 1 ATR from entry = 1% of equity given the sizing rule."""
        if direction == LONG:
            return entry_price - atr
        return entry_price + atr

    def update_trailing_stop(self, position, price: float, atr: float,
                             mult: Optional[float]) -> None:
        """Ratchet the stop in the trade's favor; never loosen it."""
        if mult is None or atr is None or math.isnan(atr) or atr <= 0:
            return
        if position.direction == LONG:
            candidate = price - mult * atr
            if position.stop_price is None or candidate > position.stop_price:
                position.stop_price = candidate
        else:
            candidate = price + mult * atr
            if position.stop_price is None or candidate < position.stop_price:
                position.stop_price = candidate

    def correlation_blocks(self, symbol: str, action: str,
                           positions: Dict[str, object]) -> bool:
        """True when the risk-on correlation filter forbids this entry.

        If every symbol in CORRELATION_FILTER["if_all_long"] is already long,
        new longs on the blocked symbol are rejected.
        """
        flt = config.CORRELATION_FILTER
        if action != LONG or symbol != flt["blocked_symbol"]:
            return False
        for gate_symbol in flt["if_all_long"]:
            pos = positions.get(gate_symbol)
            if pos is None or pos.direction != LONG:
                return False
        return True
