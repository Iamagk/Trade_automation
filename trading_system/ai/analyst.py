"""
analyst.py
Gemini Decision Layer for trade verification.
"""

import google.generativeai as genai
import json
from loguru import logger
from trading_system.config.config import config

class GeminiAnalyst:
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            logger.warning("GEMINI_API_KEY not set. AI filtering will be disabled.")
            self.model = None

    async def evaluate_trade(self, symbol, data_summary):
        """
        Evaluate a trade signal using Gemini.
        data_summary: dict containing indicators, trend, and ML confidence.
        """
        if not self.model:
            return {"decision": "SKIP", "reason": "AI model not initialized"}

        prompt = f"""
        You are an expert intraday trading risk analyst. 
        Your goal is to review a trade signal for NSE Equity (Intraday) and decide if it should be executed.
        
        Capital: ₹10,000
        Symbol: {symbol}
        
        Market Data Summary:
        {json.dumps(data_summary, indent=2)}
        
        Instructions:
        1. Analyze market context (trend, indicators, ML confidence).
        2. Reject trades that are against the major trend or look like "chasing" a move.
        3. Ensure RSI isn't extremely overbought/oversold for momentum trades.
        4. Consider VWAP position.
        
        Return a JSON response exactly in this format:
        {{
            "decision": "EXECUTE" | "REJECT",
            "confidence": 0.0 to 1.0,
            "stop_loss": suggested_price,
            "take_profit": suggested_price,
            "reasoning": "one sentence explanation"
        }}
        """

        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text.strip()
            
            # Clean up JSON if model adds markdown blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
                
            result = json.loads(text)
            return result
        except Exception as e:
            logger.error(f"Error in Gemini evaluation: {e}")
            return {"decision": "REJECT", "reason": f"AI error: {str(e)}"}

analyst = GeminiAnalyst()
