import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Config(BaseSettings):
    # Angel One SmartAPI Credentials
    SMARTAPI_API_KEY: str = os.getenv("SMARTAPI_API_KEY", "")
    SMARTAPI_HISTORIC_KEY: str = os.getenv("SMARTAPI_HISTORIC_KEY", "")
    SMARTAPI_CLIENT_ID: str = os.getenv("SMARTAPI_CLIENT_ID", "")
    SMARTAPI_PASSWORD: str = os.getenv("SMARTAPI_PASSWORD", "")
    SMARTAPI_TOTP_TOKEN: str = os.getenv("SMARTAPI_TOTP_TOKEN", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    IS_SIMULATION: bool = os.getenv("IS_SIMULATION", "true").lower() == "true"

    # Database Configuration
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "trading_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "trading_password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "trading_db")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))

    # Cache Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # Trading Parameters (₹10,000 Equity Focus)
    TOTAL_CAPITAL: float = 10000.0
    RISK_PER_TRADE_AMOUNT: float = 100.0  # ₹100 risk per trade
    MAX_DAILY_LOSS_AMOUNT: float = 300.0  # ₹300 max daily loss
    MAX_CONSECUTIVE_LOSSES: int = 3
    MAX_SIMULTANEOUS_POSITIONS: int = 2
    
    # Timing
    AUTO_SQUARE_OFF_TIME: str = "15:10"
    NO_NEW_TRADE_TIME: str = "14:30"

    # Liquid NSE Equity Universe
    TRADING_UNIVERSE: list = [
        "RELIANCE-EQ", "HDFCBANK-EQ", "ICICIBANK-EQ", "INFY-EQ",
        "TCS-EQ", "SBIN-EQ", "TATAMOTORS-EQ", "AXISBANK-EQ",
        "ITC-EQ", "LT-EQ"
    ]

    # APP Configuration
    PORT: int = int(os.getenv("PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

config = Config()
