"""
gemini_strategy.py
Single-brain Gemini trading strategy for NSE/NFO.
Uses Gemini AI as the primary decision-maker for all asset types.
"""

import google.generativeai as genai
import pandas as pd
import pandas_ta as ta
import json
from datetime import datetime
from typing import Optional, List, Dict
from loguru import logger

from trading_system.data.candle_builder import Candle
from trading_system.strategy.tpb_strategy import MarketTrend, Signal
from trading_system.config.config import config

class GeminiStrategy:
    """
    Unified Gemini Trading Strategy.
    """
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in config.")
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')

        self.reasoning: str = "Gemini Brain Initialized."
        self.candle_histories: Dict[str, List[Candle]] = {} # symbol -> candles
        self.max_history = 100

    def process_candle(self, symbol: str, candle: Candle) -> Signal:
        """
        Process a candle and decide if a trade should be taken.
        """
        if symbol not in self.candle_histories:
            self.candle_histories[symbol] = []
        
        self.candle_histories[symbol].append(candle)
        if len(self.candle_histories[symbol]) > self.max_history:
            self.candle_histories[symbol].pop(0)

        if len(self.candle_histories[symbol]) < 20:
            return Signal.NONE

        # Calculate indicators
        df = self._calculate_indicators(symbol)
        
        # Ask Gemini for signal
        return self._ask_gemini_for_signal(symbol, df, candle)

    def _calculate_indicators(self, symbol: str) -> pd.DataFrame:
        records = [c.to_dict() for c in self.candle_histories[symbol]]
        df = pd.DataFrame(records)
        df['rsi'] = ta.rsi(df['close'], length=14)
        df['ema9'] = ta.ema(df['close'], length=9)
        df['ema20'] = ta.ema(df['close'], length=20)
        df['vwap_dist'] = (df['close'] - df['vwap']) / df['vwap']
        return df.tail(20)

    def _ask_gemini_for_signal(self, symbol: str, df: pd.DataFrame, current_candle: Candle) -> Signal:
        if not self.model: return Signal.NONE
        
        try:
            data_json = df.to_json(orient="records")
            prompt = f"""
            You are a master professional trader. Analyze the market for {symbol} and decide on an intraday move.
            
            Symbol: {symbol}
            Capital: ₹10,000
            
            Market Data (Last 20 candles, 5-min interval):
            {data_json}
            
            Current Stats:
            - Price: {current_candle.close}
            - VWAP: {current_candle.vwap:.2f}
            
            Instructions:
            1. Analyze trend and volatility.
            2. Decide: BUY, SELL, or NONE.
            3. Provide SL and TP levels.
            4. Goal: Daily profit with ₹100 risk per trade.
            
            Return JSON ONLY:
            {{
                "signal": "BUY" | "SELL" | "NONE",
                "reasoning": "one short sentence",
                "stop_loss": price,
                "take_profit": price
            }}
            """
            
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text: text = text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(text)
            self.reasoning = f"[{symbol}] {result.get('reasoning')}"
            
            sig_str = result.get('signal', 'NONE')
            if sig_str == "BUY":
                logger.info(f"🚀 GEMINI BUY: {symbol} | {self.reasoning}")
                self.stop_loss = result.get("stop_loss")
                self.target = result.get("take_profit")
                return Signal.BUY_CE
            elif sig_str == "SELL":
                logger.info(f"🔻 GEMINI SELL: {symbol} | {self.reasoning}")
                self.stop_loss = result.get("stop_loss")
                self.target = result.get("take_profit")
                return Signal.BUY_PE
                
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            
        return Signal.NONE
