"""
position_manager.py
State machine for tracking a single open options position.

States:
  IDLE                  — no position, awaiting ORB establishment
  WAITING_FOR_BREAKOUT  — ORB established, watching for breakout signal
  IN_POSITION           — an option is bought, monitoring P&L
  EXITED                — trade closed (SL / Target / Trailing / Force)

Transitions:
  IDLE → WAITING_FOR_BREAKOUT     when ORBLevels.is_established becomes True
  WAITING_FOR_BREAKOUT → IN_POSITION   on BUY_CE or BUY_PE signal
  IN_POSITION → EXITED            on SL hit, Target hit, Trailing SL hit,
                                  3:20 PM force square-off, or kill switch
  EXITED → IDLE                   at next trading day reset()
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import redis
from loguru import logger

from trading_system.config.config import config


class PositionState(Enum):
    IDLE                 = "IDLE"
    WAITING_FOR_BREAKOUT = "WAITING_FOR_BREAKOUT"
    IN_POSITION          = "IN_POSITION"
    EXITED               = "EXITED"


@dataclass
class Position:
    tradingsymbol:  str
    symboltoken:    str
    option_type:    str          # "CE" or "PE"
    entry_price:    float
    quantity:       int
    entry_time:     datetime
    order_id:       str
    last_price:     float = 0.0

    # Risk levels (set by RiskRules after entry)
    stop_loss:      float = 0.0
    target:         float = 0.0
    trailing_sl:    float = 0.0   # current trailing SL price

    # Exit tracking
    exit_price:     Optional[float] = None
    exit_time:      Optional[datetime] = None
    exit_reason:    Optional[str] = None
    pnl:            float = 0.0

    @property
    def is_open(self) -> bool:
        return self.exit_price is None

    def realised_pnl(self, exit_px: float) -> float:
        return (exit_px - self.entry_price) * self.quantity

    def unrealised_pnl(self, ltp: float) -> float:
        return (ltp - self.entry_price) * self.quantity


class PositionManager:
    """Manages the lifecycle of a daily trade position."""

    _REDIS_KEY = "position_state"

    def __init__(self):
        self._redis = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            decode_responses=True,
        )
        self.state:    PositionState       = PositionState.IDLE
        self.position: Optional[Position]  = None
        self._sync_state_to_redis()

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def mark_orb_ready(self):
        """ORB levels have been established — start watching for breakout."""
        if self.state == PositionState.IDLE:
            self._transition(PositionState.WAITING_FOR_BREAKOUT)

    def open_position(self, pos: Position):
        """A fill was confirmed — record the open position."""
        if self.state != PositionState.WAITING_FOR_BREAKOUT:
            logger.warning(
                f"Attempted to open position from invalid state: {self.state}"
            )
            return
        self.position = pos
        self._transition(PositionState.IN_POSITION)
        logger.info(
            f"POSITION OPENED — {pos.tradingsymbol} qty={pos.quantity} "
            f"@ {pos.entry_price:.2f} | SL={pos.stop_loss:.2f} "
            f"Target={pos.target:.2f}"
        )

    def close_position(
        self,
        exit_price: float,
        reason: str,
    ):
        """Mark the position as closed."""
        if self.state != PositionState.IN_POSITION or not self.position:
            return
        self.position.exit_price  = exit_price
        self.position.exit_time   = datetime.now()
        self.position.exit_reason = reason
        self.position.pnl         = self.position.realised_pnl(exit_price)
        self._transition(PositionState.EXITED)
        logger.info(
            f"POSITION CLOSED — {self.position.tradingsymbol} "
            f"exit={exit_price:.2f} reason={reason} "
            f"PnL={self.position.pnl:.2f}"
        )

    def reset_for_new_day(self):
        """Call this at start of each trading day."""
        self.position = None
        self._transition(PositionState.IDLE)
        self._redis.delete(self._REDIS_KEY)
        logger.info("PositionManager reset for new trading day")

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def is_idle(self)              -> bool: return self.state == PositionState.IDLE
    @property
    def is_waiting(self)           -> bool: return self.state == PositionState.WAITING_FOR_BREAKOUT
    @property
    def is_in_position(self)       -> bool: return self.state == PositionState.IN_POSITION
    @property
    def is_exited(self)            -> bool: return self.state == PositionState.EXITED

    def get_position_summary(self) -> dict:
        if not self.position:
            return {"state": self.state.value, "position": None}
        p = self.position
        return {
            "state":          self.state.value,
            "tradingsymbol":  p.tradingsymbol,
            "option_type":    p.option_type,
            "entry_price":    p.entry_price,
            "quantity":       p.quantity,
            "stop_loss":      p.stop_loss,
            "target":         p.target,
            "trailing_sl":    p.trailing_sl,
            "exit_price":     p.exit_price,
            "ltp":            p.last_price if p.is_open else p.exit_price,
            "pnl":            p.unrealised_pnl(p.last_price) if p.is_open else p.pnl
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _transition(self, new_state: PositionState):
        old = self.state
        self.state = new_state
        self._sync_state_to_redis()
        logger.info(f"State transition: {old.value} → {new_state.value}")

    def _sync_state_to_redis(self):
        """Persist state to Redis for crash recovery / dashboard reads."""
        try:
            self._redis.set(self._REDIS_KEY, self.state.value)
        except Exception as e:
            logger.warning(f"Redis sync failed: {e}")

    def reconcile_from_redis(self):
        """On restart, read the last known state from Redis."""
        try:
            stored = self._redis.get(self._REDIS_KEY)
            if stored:
                self.state = PositionState(stored)
                logger.info(f"Reconciled state from Redis: {self.state.value}")
        except Exception as e:
            logger.warning(f"Could not reconcile state from Redis: {e}")
