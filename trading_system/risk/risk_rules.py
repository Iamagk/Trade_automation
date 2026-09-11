"""
risk_rules.py
Strict risk management for autonomous Equity trading.
"""

from datetime import datetime, time as dtime
from typing import Optional
from loguru import logger
from trading_system.config.config import config
from trading_system.risk.position_manager import Position

class ExitReason:
    STOP_LOSS        = "STOP_LOSS"
    TARGET           = "TARGET"
    TRAILING_SL      = "TRAILING_STOP_LOSS"
    FORCE_SQUAREOFF  = "FORCE_SQUAREOFF_3:10PM"
    KILL_SWITCH      = "KILL_SWITCH"

class RiskRules:
    def __init__(self):
        self.daily_pnl: float = 0.0
        self.consecutive_losses: int = 0
        self.trading_halted: bool = False
        self.active_positions_count: int = 0

    def calculate_quantity(self, price: float, stop_loss: float) -> int:
        """
        Calculates position size based on Risk Amount (₹100).
        Quantity = Risk / (Entry - SL)
        """
        sl_dist = abs(price - stop_loss)
        if sl_dist == 0:
            return 0
        
        qty = int(config.RISK_PER_TRADE_AMOUNT / sl_dist)
        
        # Max quantity check based on capital (₹10,000)
        max_qty = int(config.TOTAL_CAPITAL / price)
        return min(qty, max_qty)

    def can_trade(self, current_time: datetime) -> bool:
        if self.trading_halted:
            return False
            
        # 1. Market Time Check
        if current_time.time() >= dtime.fromisoformat(config.NO_NEW_TRADE_TIME):
            return False
            
        # 2. Max Daily Loss (₹300)
        if self.daily_pnl <= -config.MAX_DAILY_LOSS_AMOUNT:
            logger.warning(f"Daily loss limit hit (₹{self.daily_pnl}). Halted.")
            self.trading_halted = True
            return False
            
        # 3. Consecutive Losses (3)
        if self.consecutive_losses >= config.MAX_CONSECUTIVE_LOSSES:
            logger.warning("Max consecutive losses hit. Halted.")
            self.trading_halted = True
            return False
            
        # 4. Max Simultaneous Positions (2)
        if self.active_positions_count >= config.MAX_SIMULTANEOUS_POSITIONS:
            return False
            
        return True

    def evaluate_exit(self, position: Position, ltp: float, current_time: datetime) -> Optional[str]:
        # 1. Auto Square-off at 3:10 PM
        square_off_time = dtime.fromisoformat(config.AUTO_SQUARE_OFF_TIME)
        if current_time.time() >= square_off_time:
            return ExitReason.FORCE_SQUAREOFF

        # 2. Target Hit
        if position.option_type == "CE": # Proxy for LONG/BUY
            if ltp >= position.target: return ExitReason.TARGET
            if ltp <= position.stop_loss: return ExitReason.STOP_LOSS
        else: # Proxy for SHORT/SELL
            if ltp <= position.target: return ExitReason.TARGET
            if ltp >= position.stop_loss: return ExitReason.STOP_LOSS

        return None

    def record_trade_result(self, pnl: float):
        self.daily_pnl += pnl
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        self.active_positions_count -= 1
        logger.info(f"Recorded Result: PnL={pnl:.2f}, DailyPnL={self.daily_pnl:.2f}")

    def reset_for_new_day(self):
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.trading_halted = False
        self.active_positions_count = 0
