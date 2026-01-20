import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

@dataclass
class Config:
    ZERODHA_API_KEY: str = os.getenv("ZERODHA_API_KEY")
    ZERODHA_API_SECRET: str = os.getenv("ZERODHA_API_SECRET")
    TOTAL_CAPITAL: float = 10000.0
    NEW_ORDER_CAPITAL_LIMIT: float = 2250.0  # 75% of 3L
    AVERAGING_CAPITAL_LIMIT: float = 7500.0   # 25% of 3L
    PER_STOCK_ALLOCATION: float = 1000.0
    MAX_NEW_ORDERS_PER_DAY: int = 1
    HOLDING_DROP_THRESHOLD: float = 0.10  # 10%
    DMA_PERIOD: int = 25
    SCHEDULE_TIME: str = "15:20"  # 3:20 PM

config = Config()
