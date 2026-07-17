"""Shared technical indicators, all vectorized over pandas Series/DataFrames."""

import pandas as pd


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).mean()


def rolling_std(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).std(ddof=0)


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def atr(bars: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range with Wilder's smoothing.

    Expects columns: high, low, close.
    """
    high, low, close = bars["high"], bars["low"], bars["close"]
    prev_close = close.shift(1)
    true_range = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1.0 / period, adjust=False).mean()
