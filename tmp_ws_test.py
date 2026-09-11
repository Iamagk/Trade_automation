import time
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from trading_system.execution.smartapi_login import smart_api_login
from trading_system.config.config import config
from SmartApi.smartWebSocketV2 import SmartWebSocketV2

print("Logging in...")
session = smart_api_login.login()
print("Session:", session.keys() if session else None)

def on_data(wsapp, message):
    print("DATA:", message)

def on_open(wsapp):
    print("WEBSOCKET OPENED! Sending subscribe...")
    sws.subscribe("test_id", 3, [{"exchangeType": 1, "tokens": ["99926000"]}])


def on_error(wsapp, error):
    print("WEBSOCKET ERROR:", error)

def on_close(wsapp, code, reason):
    print(f"WEBSOCKET CLOSED: code={code}, reason={reason}")

sws = SmartWebSocketV2(session['jwtToken'], config.SMARTAPI_API_KEY, config.SMARTAPI_CLIENT_ID, session['feedToken'], max_retry_attempt=0)
sws.on_data = on_data
sws.on_open = on_open
sws.on_error = on_error
sws.on_close = on_close

print("Connecting...")
sws.connect()
