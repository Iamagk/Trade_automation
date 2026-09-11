"""
candle_builder.py
Aggregates live ticks from WebSocket into 5-minute OHLCV candles.
Fires an on_candle_close callback each time a complete candle is formed.
"""

import asyncio
from datetime import datetime, time as dtime
from typing import Callable, Optional
import pandas as pd
from loguru import logger


class Candle:
    """Represents a single OHLCV candle."""

    def __init__(self, timestamp: datetime, open_price: float):
        self.timestamp = timestamp          # candle start time
        self.open = open_price
        self.high = open_price
        self.low = open_price
        self.close = open_price
        self.volume = 0
        self.tick_count = 0
        self.vwap = 0.0
        self.is_closed = False

    def update(self, price: float, volume: int = 0):
        """Feed a new tick into the candle."""
        if price > self.high:
            self.high = price
        if price < self.low:
            self.low = price
        self.close = price
        self.volume += volume
        self.tick_count += 1

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "open":      self.open,
            "high":      self.high,
            "low":       self.low,
            "close":     self.close,
            "volume":    self.volume,
            "vwap":      self.vwap,
        }

    def __repr__(self):
        return (
            f"Candle({self.timestamp} O={self.open} H={self.high} "
            f"L={self.low} C={self.close} V={self.volume} VWAP={self.vwap:.2f})"
        )


class CandleBuilder:
    """
    Builds 5-minute candles from a stream of raw ticks.

    Usage:
        builder = CandleBuilder(interval_minutes=5, on_candle_close=my_callback)
        # For each incoming tick dict from WebSocket:
        await builder.process_tick(tick)
    """

    CANDLE_INTERVAL = 5  # minutes

    def __init__(
        self,
        interval_minutes: int = 5,
        on_candle_close: Optional[Callable] = None,
    ):
        self.interval_minutes = interval_minutes
        self.on_candle_close = on_candle_close   # async callback
        self.current_candle: Optional[Candle] = None
        self.candle_history: list[Candle] = []   # completed candles
        self.df: Optional[pd.DataFrame] = None   # DataFrame for analytics

        # VWAP Anchoring (reset daily)
        self._cum_pv: float = 0.0   # Cumulative Price * Volume
        self._cum_v:  int   = 0     # Cumulative Volume

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process_tick(self, tick: dict):
        """
        Process a single tick from the SmartAPI WebSocket.

        Expected tick keys (SmartWebSocketV2 Full Snap):
          - 'last_traded_price' (int, paise — divide by 100 for ₹)
          - 'exchange_timestamp' (epoch ms)
          - 'volume_trade_for_the_day'
        """
        try:
            ltp_paise = tick.get("last_traded_price", 0)
            price = ltp_paise / 100.0
            volume = tick.get("volume_trade_for_the_day", 0)
            epoch_ms = tick.get("exchange_timestamp", 0)

            if epoch_ms:
                tick_time = datetime.fromtimestamp(epoch_ms / 1000)
            else:
                tick_time = datetime.now()

            # Only process during market hours
            if not self._is_market_hours(tick_time):
                return

            candle_start = self._candle_start_time(tick_time)

            if self.current_candle is None:
                # First tick ever
                self.current_candle = Candle(candle_start, price)
                logger.debug(f"New candle opened: {candle_start}")

            elif candle_start > self.current_candle.timestamp:
                # We've moved to a new interval — close the old candle
                await self._close_candle(price, candle_start)

            # Update current candle
            self.current_candle.update(price, volume)

            # Update VWAP (Day-anchored)
            # Use typical price (H+L+C)/3 for standard VWAP or just Close
            # Based on user description, we'll use closing price per tick or tick price
            # Since ticks don't always give incremental volume correctly, 
            # we'll use the tick's current volume if provided, or assume 1 if not.
            # However, SmartAPI usually gives cumulative volume for the day.
            # We need incremental volume to calculate VWAP correctly.
            
            # If tick gives 'volume_trade_for_the_day', we calculate delta
            v_day = tick.get("volume_trade_for_the_day", 0)
            if self._cum_v == 0:
                delta_v = v_day if v_day > 0 else 1 # fallback
            else:
                delta_v = max(0, v_day - self._cum_v)
            
            self._cum_pv += (price * delta_v)
            self._cum_v  = v_day
            
            if self._cum_v > 0:
                self.current_candle.vwap = self._cum_pv / self._cum_v
            else:
                self.current_candle.vwap = price

        except Exception as e:
            logger.exception(f"Error processing tick: {e}")

    def get_history_df(self) -> pd.DataFrame:
        """Return a DataFrame of all closed candles (useful for strategy)."""
        if not self.candle_history:
            return pd.DataFrame()
        records = [c.to_dict() for c in self.candle_history]
        return pd.DataFrame(records).set_index("timestamp")

    def get_last_n_candles(self, n: int = 10) -> list[Candle]:
        return self.candle_history[-n:]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _close_candle(self, new_open: float, new_start: datetime):
        """Close current candle, fire callback, open a new one."""
        self.current_candle.is_closed = True
        completed = self.current_candle
        self.candle_history.append(completed)
        logger.info(
            f"Candle closed — {completed}"
        )

        # Rebuild summary DataFrame
        self.df = self.get_history_df()

        # Fire strategy callback
        if self.on_candle_close:
            try:
                if asyncio.iscoroutinefunction(self.on_candle_close):
                    await self.on_candle_close(completed)
                else:
                    self.on_candle_close(completed)
            except Exception as e:
                logger.exception(f"Error in on_candle_close callback: {e}")

        # Open fresh candle for new interval
        self.current_candle = Candle(new_start, new_open)
        logger.debug(f"New candle opened: {new_start}")

    def _candle_start_time(self, ts: datetime) -> datetime:
        """Truncate a datetime to the nearest candle interval boundary."""
        minute_bucket = (ts.minute // self.interval_minutes) * self.interval_minutes
        return ts.replace(minute=minute_bucket, second=0, microsecond=0)

    @staticmethod
    def _is_market_hours(ts: datetime) -> bool:
        market_open = dtime(9, 15)
        market_close = dtime(15, 30)
        return market_open <= ts.time() <= market_close
