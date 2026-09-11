"""
main.py
Single-Agent Autonomous Gemini Trading Engine.
"""

import asyncio
from datetime import datetime
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from loguru import logger

from trading_system.config.config import config
from trading_system.data.websocket_client import TradingWebSocket
from trading_system.data.candle_builder import CandleBuilder, Candle
from trading_system.strategy.gemini_strategy import GeminiStrategy, Signal
from trading_system.execution.order_manager import OrderManager
from trading_system.risk.position_manager import PositionManager, Position
from trading_system.risk.risk_rules import RiskRules

class TradingEngine:
    def __init__(self):
        self.strategy = GeminiStrategy()
        self.order_manager = OrderManager()
        self.risk_rules = RiskRules()
        self.position_manager = PositionManager()
        self.ws_client = TradingWebSocket(tick_callback=self.on_tick)
        
        self.symbol_to_token = {}
        self.token_to_symbol = {}
        self.candle_builders = {}

    async def on_tick(self, tick: dict):
        token = tick.get("token")
        symbol = self.token_to_symbol.get(token)
        if not symbol: return
        
        builder = self.candle_builders.get(symbol)
        if builder: await builder.process_tick(tick)
        
        # Risk monitoring
        if self.position_manager.is_in_position and self.position_manager.position.tradingsymbol == symbol:
            ltp = tick.get("last_traded_price", 0) / 100.0
            exit_reason = self.risk_rules.evaluate_exit(self.position_manager.position, ltp, datetime.now())
            if exit_reason:
                await self.exit_position(exit_reason, ltp)

    async def on_candle_close(self, symbol: str, candle: Candle):
        logger.info(f"Candle closed for {symbol}: {candle.close}")
        
        if not self.risk_rules.can_trade(datetime.now()): return
        if self.position_manager.is_in_position: return

        sig = self.strategy.process_candle(symbol, candle)
        if sig != Signal.NONE:
            await self.execute_trade(symbol, sig, candle)

    async def execute_trade(self, symbol, sig, candle):
        side = "BUY" if sig == Signal.BUY_CE else "SELL"
        sl = self.strategy.stop_loss
        tp = self.strategy.target
        
        qty = self.risk_rules.calculate_quantity(candle.close, sl)
        if qty <= 0: return

        logger.info(f"🚀 EXECUTING {side} for {symbol} | Qty: {qty} | SL: {sl} | TP: {tp}")
        
        fill = await self.order_manager.buy_option(symbol, self.symbol_to_token[symbol], qty, "CE" if side == "BUY" else "PE")
        
        if fill:
            pos = Position(
                tradingsymbol=symbol,
                symboltoken=self.symbol_to_token[symbol],
                option_type="CE" if side == "BUY" else "PE",
                entry_price=fill["fill_price"] if fill["fill_price"] > 0 else candle.close,
                quantity=qty,
                entry_time=fill["fill_time"],
                order_id=fill["order_id"]
            )
            pos.stop_loss = sl
            pos.target = tp
            self.position_manager.open_position(pos)
            self.risk_rules.active_positions_count += 1

    async def exit_position(self, reason, ltp):
        pos = self.position_manager.position
        logger.info(f"🏁 EXITING {pos.tradingsymbol} | Reason: {reason} | Price: {ltp}")
        
        await self.order_manager.exit_order(pos.tradingsymbol, pos.symboltoken, pos.quantity)
        
        # Calculate PnL
        pnl = (ltp - pos.entry_price) * pos.quantity if pos.option_type == "CE" else (pos.entry_price - ltp) * pos.quantity
        self.position_manager.close_position(ltp, reason)
        self.risk_rules.record_trade_result(pnl)

    async def start(self):
        # Setup Universe
        for symbol in config.TRADING_UNIVERSE:
            pure = symbol.split("-")[0]
            token = await self.order_manager.get_symbol_token(pure)
            if token:
                self.symbol_to_token[symbol] = token
                self.token_to_symbol[token] = symbol
                self.candle_builders[symbol] = CandleBuilder(
                    interval_minutes=5,
                    on_candle_close=lambda c, s=symbol: self.on_candle_close(s, c)
                )
        
        # Add NIFTY for context or options
        nifty_token = "99926000"
        self.symbol_to_token["NIFTY"] = nifty_token
        self.token_to_symbol[nifty_token] = "NIFTY"
        self.candle_builders["NIFTY"] = CandleBuilder(
            interval_minutes=5,
            on_candle_close=lambda c, s="NIFTY": self.on_candle_close(s, c)
        )

        self.ws_client.tokens = list(self.symbol_to_token.values())
        self.ws_client.connect()

engine = TradingEngine()
app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await engine.start()
    yield
    engine.ws_client.disconnect()

app.router.lifespan_context = lifespan

@app.get("/")
async def root():
    return {
        "status": "online",
        "daily_pnl": engine.risk_rules.daily_pnl,
        "in_position": engine.position_manager.is_in_position,
        "reasoning": engine.strategy.reasoning
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)
