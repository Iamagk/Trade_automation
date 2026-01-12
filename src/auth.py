from kiteconnect import KiteConnect
from .config import config
import os
import json

ACCESS_TOKEN_FILE = "access_token.json"

def get_access_token() -> str:
    """
    Tries to load valid access token from file.
    If missing or invalid (though validation is hard without calling API), returns None.
    User usually needs to login once per day.
    """
    if os.path.exists(ACCESS_TOKEN_FILE):
        try:
            with open(ACCESS_TOKEN_FILE, 'r') as f:
                data = json.load(f)
            return data.get("access_token")
        except Exception:
            pass
    return None

def login_flow():
    """
    Interactive Login Flow
    """
    kite = KiteConnect(api_key=config.ZERODHA_API_KEY)
    
    print("\n--- Zerodha Login ---")
    print(f"1. Open this URL in your browser:\n{kite.login_url()}")
    print("2. Login and copy the 'request_token' from the redirected URL.")
    request_token = input("Enter Request Token: ").strip()
    
    try:
        data = kite.generate_session(request_token, api_secret=config.ZERODHA_API_SECRET)
        access_token = data["access_token"]
        
        # Save to file
        with open(ACCESS_TOKEN_FILE, 'w') as f:
            json.dump(data, f, default=str)
            
        print("Login Successful! Access Token saved.")
        return access_token
    except Exception as e:
        print(f"Login failed: {e}")
        return None
