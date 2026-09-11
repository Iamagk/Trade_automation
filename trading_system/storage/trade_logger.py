"""
trade_logger.py
Handles saving trades to PostgreSQL and logging structural data.
"""

from loguru import logger
from sqlalchemy.orm import Session
from datetime import datetime

from trading_system.storage.models import TradeRecord, SessionLocal
from trading_system.risk.position_manager import Position

class TradeLogger:
    def __init__(self):
        # We can also configure Loguru to write to a file here
        logger.add("logs/trading_{time:YYYY-MM-DD}.log", rotation="1 day", level="INFO")

    def log_entry(self, position: Position) -> int:
        """
        Record the entry of a trade into the DB.
        Returns the DB internal ID for later updates.
        """
        db: Session = SessionLocal()
        try:
            trade = TradeRecord(
                date=datetime.now(),
                tradingsymbol=position.tradingsymbol,
                option_type=position.option_type,
                quantity=position.quantity,
                entry_time=position.entry_time,
                entry_price=position.entry_price,
                entry_order_id=position.order_id
            )
            db.add(trade)
            db.commit()
            db.refresh(trade)
            return trade.id
        except Exception as e:
            logger.exception(f"Failed to log trade entry to DB: {e}")
            db.rollback()
            return -1
        finally:
            db.close()

    def log_exit(self, db_id: int, position: Position):
        """Update an existing trade record with exit details."""
        if db_id < 0:
            return
        
        db: Session = SessionLocal()
        try:
            trade = db.query(TradeRecord).filter(TradeRecord.id == db_id).first()
            if trade:
                trade.exit_time = position.exit_time
                trade.exit_price = position.exit_price
                trade.exit_reason = position.exit_reason
                trade.pnl = position.pnl
                db.commit()
                logger.info(f"Trade {db_id} exit saved to DB. PnL: {position.pnl:.2f}")
        except Exception as e:
            logger.exception(f"Failed to log trade exit to DB: {e}")
            db.rollback()
        finally:
            db.close()

trade_logger = TradeLogger()
