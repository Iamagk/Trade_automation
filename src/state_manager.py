import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List
from .config import config

STATE_FILE = "strategy_state.json"

@dataclass
class DailyState:
    date: str
    used_new_capital: float
    used_avg_capital: float
    orders_placed_count: int
    actions_log: List[str]

from .csv_logger import CSVLogger

class StateManager:
    def __init__(self, filepath: str = STATE_FILE):
        self.filepath = filepath
        self.state = self._load_state()
        self.logger = CSVLogger()

    def _load_state(self) -> DailyState:
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    
                # Reset state if it's a new day
                if data.get('date') != today_str:
                    return self._create_new_state(today_str)
                
                return DailyState(**data)
            except Exception as e:
                print(f"Error loading state: {e}. creating new state.")
                return self._create_new_state(today_str)
        else:
            return self._create_new_state(today_str)

    def _create_new_state(self, date_str: str) -> DailyState:
        return DailyState(
            date=date_str,
            used_new_capital=0.0,
            used_avg_capital=0.0,
            orders_placed_count=0,
            actions_log=[]
        )

    def save_state(self):
        with open(self.filepath, 'w') as f:
            json.dump(asdict(self.state), f, indent=4)

    def _daily_limit_reached(self) -> bool:
        return self.state.orders_placed_count >= config.MAX_NEW_ORDERS_PER_DAY

    def can_place_new_order(self, estimated_cost: float) -> bool:
        if self._daily_limit_reached():
             return False
        
        if (self.state.used_new_capital + estimated_cost) > config.NEW_ORDER_CAPITAL_LIMIT:
            return False
            
        return True

    def can_average(self, estimated_cost: float) -> bool:
        if self._daily_limit_reached():
             return False

        if (self.state.used_avg_capital + estimated_cost) > config.AVERAGING_CAPITAL_LIMIT:
            return False
        return True

    def record_new_order(self, symbol: str, quantity: int, price: float, cost: float, message: str):
        self.state.used_new_capital += cost
        self.state.orders_placed_count += 1
        self.state.actions_log.append(message)
        self.save_state()
        self.logger.log_trade(symbol, "BUY", quantity, price)

    def record_averaging(self, symbol: str, quantity: int, price: float, cost: float, message: str):
        self.state.used_avg_capital += cost
        # "only one action per day"
        self.state.orders_placed_count += 1 
        self.state.actions_log.append(message)
        self.save_state()
        self.logger.log_trade(symbol, "AVERAGE", quantity, price)
    
    def record_sell(self, symbol: str, quantity: int, price: float, revenue: float, message: str):
        """Record a sell transaction"""
        # "only one action per day"
        self.state.orders_placed_count += 1
        self.state.actions_log.append(message)
        self.save_state()
        self.logger.log_trade(symbol, "SELL", quantity, price, total_cost=revenue)

