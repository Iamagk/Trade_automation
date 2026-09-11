"""
order_manager.py
Handles NSE Equity order execution via Angel One SmartAPI.
"""

import asyncio
from datetime import datetime
from typing import Optional
import redis
from SmartApi import SmartConnect
from loguru import logger
from trading_system.config.config import config
from trading_system.execution.smartapi_login import smart_api_login

class OrderManager:
    EXCHANGE = "NSE"
    PRODUCT_TYPE = "INTRADAY"
    VARIETY = "NORMAL"

    def __init__(self):
        self._redis = redis.Redis(
            host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB, decode_responses=True
        )

    async def place_equity_order(self, symbol: str, token: str, qty: int, side: str) -> Optional[dict]:
        """
        Place a MARKET order for NSE Equity.
        side: "BUY" or "SELL"
        """
        order_params = {
            "variety": self.VARIETY,
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": side,
            "exchange": self.EXCHANGE,
            "ordertype": "MARKET",
            "producttype": self.PRODUCT_TYPE,
            "duration": "DAY",
            "price": "0",
            "quantity": str(qty),
        }

        if config.IS_SIMULATION:
            logger.info(f"SIMULATION {side}: {symbol} | Qty: {qty}")
            return {
                "order_id": f"sim_{datetime.now().strftime('%H%M%S')}",
                "fill_price": 0.0, # Will be filled by LTP in simulation
                "status": "COMPLETE",
                "fill_time": datetime.now()
            }

        try:
            smart: SmartConnect = smart_api_login.smart_connect
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: smart.placeOrder(order_params))
            
            if response and response.get("status"):
                order_id = response["data"]["orderid"]
                logger.info(f"ORDER PLACED: {side} {symbol} | ID: {order_id}")
                
                # Poll for fill details
                fill_data = await self._confirm_fill(order_id)
                return {
                    "order_id": order_id,
                    "fill_price": fill_data.get("averageprice", 0.0),
                    "status": fill_data.get("status", "UNKNOWN"),
                    "fill_time": datetime.now()
                }
            else:
                logger.error(f"Order failed: {response.get('message', 'Unknown error')}")
                return None
        except Exception as e:
            logger.exception(f"Exception placing order: {e}")
            return None

    async def _confirm_fill(self, order_id: str, retries: int = 5) -> dict:
        smart: SmartConnect = smart_api_login.smart_connect
        loop = asyncio.get_event_loop()
        for _ in range(retries):
            await asyncio.sleep(1)
            try:
                book = await loop.run_in_executor(None, smart.orderBook)
                if book and book.get("status") and book.get("data"):
                    for order in book["data"]:
                        if order.get("orderid") == order_id:
                            if order.get("status") in ("complete", "COMPLETE"):
                                return order
            except Exception as e:
                logger.warning(f"Error checking fill: {e}")
        return {}

    async def get_symbol_token(self, symbol: str) -> Optional[str]:
        """Fetch token for NSE symbol."""
        try:
            smart: SmartConnect = smart_api_login.smart_connect
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, lambda: smart.searchScrip(self.EXCHANGE, symbol))
            if resp and resp.get("status") and resp.get("data"):
                return resp["data"][0]["symboltoken"]
        except Exception as e:
            logger.error(f"Error fetching token for {symbol}: {e}")
        return None
