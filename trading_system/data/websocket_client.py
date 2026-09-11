import json
import asyncio
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from trading_system.config.config import config
from trading_system.execution.smartapi_login import smart_api_login
from loguru import logger

class TradingWebSocket:
    def __init__(self, tick_callback=None):
        self.sws = None
        self.tick_callback = tick_callback
        self.tokens = ["99926000"] # NIFTY Spot Token
        self.exchange_type = 1 # NSE_CM
        self.is_connected = False
        self.is_started = False
        self.loop = asyncio.get_event_loop()

    def on_data(self, wsapp, data):
        """Callback for receiving tick data"""
        if self.tick_callback:
            if asyncio.iscoroutinefunction(self.tick_callback):
                asyncio.run_coroutine_threadsafe(self.tick_callback(data), self.loop)
            else:
                self.tick_callback(data)

    def on_open(self, wsapp):
        logger.info("✅ WebSocket connection successfully established")
        self.is_connected = True
        self.subscribe()

    def on_error(self, wsapp, error):
        logger.error(f"WebSocket error: {error}")
        self.is_connected = False

    def on_close(self, wsapp, code, reason):
        logger.warning(f"❌ WebSocket closed. wsapp: {wsapp}, Code: {code}, Reason: {reason}")
        self.is_connected = False
        # Do not immediately set is_started = False to allow the library's internal reconnect to try

    def subscribe(self):
        try:
            correlation_id = "trading_bot_v1"
            action = 1 # Subscribe
            mode = 3 # Quote and Full Snap (contains LTP)
            
            token_list = [{"exchangeType": self.exchange_type, "tokens": self.tokens}]
            self.sws.subscribe(correlation_id, mode, token_list)
            logger.info(f"Subscribed to tokens: {self.tokens}")
        except Exception as e:
            logger.exception(f"Error subscribing to tokens: {e}")

    def connect(self):
        try:
            # Prevent multiple concurrent connection attempts
            if self.is_connected:
                logger.warning("WebSocket already connected")
                return
            
            self.is_started = True
            logger.info("🚀 Initiating SmartAPI WebSocket handshake...")
            
            def wrapper():
                try:
                    session = smart_api_login.get_session()
                    jwt_token = session['jwtToken']
                    client_code = config.SMARTAPI_CLIENT_ID
                    feed_token = session['feedToken']
                    api_key = config.SMARTAPI_API_KEY

                    self.sws = SmartWebSocketV2(jwt_token, api_key, client_code, feed_token)
                    
                    self.sws.on_open = self.on_open
                    self.sws.on_data = self.on_data
                    self.sws.on_error = self.on_error
                    self.sws.on_close = self.on_close

                    logger.info(f"📡 WebSocket thread started with client: {client_code}")
                    self.sws.connect()
                except Exception as ex:
                    logger.error(f"❌ WebSocket connection crashed during handshake: {ex}")
                    self.is_connected = False
                    self.is_started = False

            self.loop.run_in_executor(None, wrapper)
        except Exception as e:
            self.is_started = False
            logger.exception(f"💥 Fatal error initiating WebSocket: {e}")

    def disconnect(self):
        self.is_started = False
        if self.sws:
            try:
                self.sws.close_connection()
            except:
                pass
            self.is_connected = False
            logger.info("WebSocket connection closed by user")

# Singleton instance or factory can be used here
# websocket_client = TradingWebSocket()
