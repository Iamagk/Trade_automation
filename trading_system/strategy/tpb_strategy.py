"""
tpb_strategy.py
Trend Pullback Breakout (TPB) strategy logic.
1. Observe 9:15-9:30 range to determine trend.
2. Wait for pullback to VWAP.
3. Enter on confirmation candle.
"""

from datetime import datetime, time as dtime
from enum import Enum
from typing import Optional, List
from loguru import logger

from trading_system.data.candle_builder import Candle
from trading_system.config.config import config


class MarketTrend(Enum):
    BULLISH  = "BULLISH"
    BEARISH  = "BEARISH"
    SIDEWAYS = "SIDEWAYS"
    UNKNOWN  = "UNKNOWN"


class Signal(Enum):
    NONE    = "NONE"
    BUY_CE  = "BUY_CE"
    BUY_PE  = "BUY_PE"


class TPBStrategy:
    """
    Implements the Trend Pullback Breakout strategy.
    """
    
    OBSERVATION_END = dtime(9, 30)
    NO_NEW_TRADE_TIME = dtime(14, 30)
    STRIKE_STEP = 50

    def __init__(self):
        self.trend: MarketTrend = MarketTrend.UNKNOWN
        self.is_established: bool = False
        self.signal_fired: bool = False
        self.pullback_occurred: bool = False
        self.atm_strike: Optional[int] = None
        self.target: Optional[float] = None
        self.stop_loss: Optional[float] = None
        self.reasoning: str = "Initializing strategy..."
        
        self._observation_candles: List[Candle] = []

    def process_candle(self, candle: Candle) -> Signal:
        """
        Feed a closed 5-minute candle.
        """
        now = candle.timestamp.time()
        
        # 1. Observation Phase (9:15 - 9:30)
        if now < self.OBSERVATION_END:
            self._observation_candles.append(candle)
            self.reasoning = f"Observation phase ({now.strftime('%H:%M')}). Waiting for 9:30 trend establishment."
            return Signal.NONE
            
        # 2. Establish Trend at 9:30
        if not self.is_established and now >= self.OBSERVATION_END:
            self._establish_trend()
            return Signal.NONE
            
        # 3. Guard: No trade if sideways or already fired
        if self.trend == MarketTrend.SIDEWAYS:
            self.reasoning = "Market is SIDEWAYS (move < 0.05% from open). No high-probability setup."
            return Signal.NONE
            
        if self.signal_fired:
            self.reasoning = f"Trade already executed today at {self.atm_strike}. Monitoring positions."
            return Signal.NONE
            
        # 4. Guard: No new trades after cutoff
        if now >= self.NO_NEW_TRADE_TIME:
            return Signal.NONE
            
        # 5. Trading Logic
        return self._evaluate_signal(candle)

    def _establish_trend(self):
        """Determine trend based on 9:15-9:30 candles."""
        if not self._observation_candles:
            self.trend = MarketTrend.SIDEWAYS
            self.is_established = True
            return

        last_candle = self._observation_candles[-1]
        first_candle = self._observation_candles[0]
        
        # Trend Criteria:
        # Bullish: Close > VWAP and Close > Opening price of the day
        # Bearish: Close < VWAP and Close < Opening price of the day
        
        price_change = last_candle.close - first_candle.open
        vwap_diff = last_candle.close - last_candle.vwap
        
        # Simple threshold for "sideways" - e.g., if move is less than 0.05%
        threshold = first_candle.open * 0.0005 
        
        if abs(price_change) < threshold:
            self.trend = MarketTrend.SIDEWAYS
            self.reasoning = f"Trend established as SIDEWAYS. Price move ({price_change:.1f}) below threshold ({threshold:.1f})."
        elif price_change > 0 and vwap_diff > 0:
            self.trend = MarketTrend.BULLISH
            self.reasoning = f"Trend confirmed BULLISH. Price is {price_change:.1f} pts above open and above VWAP."
        elif price_change < 0 and vwap_diff < 0:
            self.trend = MarketTrend.BEARISH
            self.reasoning = f"Trend confirmed BEARISH. Price is {abs(price_change):.1f} pts below open and below VWAP."
        else:
            self.trend = MarketTrend.SIDEWAYS
            self.reasoning = "Trend inconclusive (Price vs VWAP conflict). Staying SIDEWAYS for safety."
            
        self.is_established = True
        logger.info(f"TPB Trend Established: {self.trend.value} | {self.reasoning}")

    def _evaluate_signal(self, candle: Candle) -> Signal:
        """
        Detect pullback to VWAP and continuation.
        """
        close = candle.close
        vwap = candle.vwap
        
        # Check for Pullback (Price moves closer to VWAP)
        # For Bullish: Pullback is when Price comes down toward VWAP
        # For Bearish: Pullback is when Price comes up toward VWAP
        
        dist_to_vwap = abs(close - vwap) / vwap
        
        if dist_to_vwap < 0.0015: # Pullback criteria: within 0.15% of VWAP
            self.pullback_occurred = True
            self.reasoning = f"Pullback to VWAP detected (dist: {dist_to_vwap:.2%}). Waiting for {self.trend.value} continuation."
            logger.debug(f"TPB Pullback detected at {candle.timestamp}: distance={dist_to_vwap:.4%}")
            return Signal.NONE
            
        # If pullback happened, look for continuation
        if self.pullback_occurred:
            if self.trend == MarketTrend.BULLISH:
                self.reasoning = f"Pullback occurred. Waiting for Bullish candle above VWAP (Curr: {close:.1f})."
                # Continuation: Bullish candle (close > open) and closing above VWAP
                if candle.close > candle.open and candle.close > vwap:
                    self.reasoning = f"BULLISH CONTINUATION confirmed! Buying CE at strike {int(round(close/50)*50)}."
                    logger.info(f"TPB BULLISH SIGNAL: continuation confirmed at {close:.2f}")
                    return self._fire_signal(Signal.BUY_CE, candle)
            
            elif self.trend == MarketTrend.BEARISH:
                self.reasoning = f"Pullback occurred. Waiting for Bearish candle below VWAP (Curr: {close:.1f})."
                # Continuation: Bearish candle (close < open) and closing below VWAP
                if candle.close < candle.open and candle.close < vwap:
                    self.reasoning = f"BEARISH CONTINUATION confirmed! Buying PE at strike {int(round(close/50)*50)}."
                    logger.info(f"TPB BEARISH SIGNAL: continuation confirmed at {close:.2f}")
                    return self._fire_signal(Signal.BUY_PE, candle)
        else:
            self.reasoning = f"Trend is {self.trend.value}. Market is extended (dist to VWAP: {dist_to_vwap:.2%}). Waiting for pullback."
                    
        return Signal.NONE

    def _fire_signal(self, sig: Signal, candle: Candle) -> Signal:
        self.signal_fired = True
        price = candle.close
        self.atm_strike = int(round(price / self.STRIKE_STEP) * self.STRIKE_STEP)
        
        # Simple Target/SL calculation:
        # Bullish: SL below candle low, Target 1:1.5 or fixed pts
        if sig == Signal.BUY_CE:
            self.stop_loss = candle.low - 5 # 5 pt buffer
            self.target = price + (price - self.stop_loss) * 1.5
        else:
            self.stop_loss = candle.high + 5
            self.target = price - (self.stop_loss - price) * 1.5
            
        return sig

    def reset(self):
        self.trend = MarketTrend.UNKNOWN
        self.is_established = False
        self.signal_fired = False
        self.pullback_occurred = False
        self._observation_candles.clear()
        logger.info("TPB Strategy reset for new day")
