import csv
import os
from datetime import datetime
from typing import List, Dict, Any
from .database import SessionLocal
from . import models

class CSVLogger:
    def __init__(self, trades_file: str = "trades.csv", screening_file: str = "screening_log.csv"):
        self.trades_file = trades_file
        self.screening_file = screening_file
        self._ensure_files()

    def _ensure_files(self):
        # Create trades file with header if not exists
        if not os.path.exists(self.trades_file):
            with open(self.trades_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Time", "Symbol", "Action", "Quantity", "Price", "Total Cost"])

        # Create screening file with header if not exists
        if not os.path.exists(self.screening_file):
            with open(self.screening_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Time", "Rank", "Symbol", "Current Price", "25 DMA", "% Below DMA"])

    def log_trade(self, symbol: str, action: str, quantity: int, price: float, total_cost: float = None):
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        if total_cost is None:
            total_cost = quantity * price

        # CSV Logging
        with open(self.trades_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                date_str,
                time_str,
                symbol,
                action,
                quantity,
                f"{price:.2f}",
                f"{total_cost:.2f}"
            ])
        
        # DB Logging
        db = SessionLocal()
        try:
            db_trade = models.Trade(
                date=date_str,
                time=time_str,
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                total_cost=total_cost
            )
            db.add(db_trade)
            db.commit()
        except Exception as e:
            print(f"Error logging trade to DB: {e}")
            db.rollback()
        finally:
            db.close()

    def log_screening_candidates(self, candidates: List[Any]): # Expecting list of StockData
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        # CSV Logging
        with open(self.screening_file, 'a', newline='') as f:
            writer = csv.writer(f)
            for i, c in enumerate(candidates, 1):
                writer.writerow([
                    date_str,
                    time_str,
                    i,
                    c.symbol,
                    f"{c.current_price:.2f}",
                    f"{c.dma_25:.2f}",
                    f"{c.percent_below_dma * 100:.2f}%"
                ])
        
        # DB Logging
        db = SessionLocal()
        try:
            for i, c in enumerate(candidates, 1):
                db_log = models.ScreeningLog(
                    date=date_str,
                    time=time_str,
                    rank=i,
                    symbol=c.symbol,
                    current_price=c.current_price,
                    dma_25=c.dma_25,
                    percent_below_dma=f"{c.percent_below_dma * 100:.2f}%"
                )
                db.add(db_log)
            db.commit()
        except Exception as e:
            print(f"Error logging screening to DB: {e}")
            db.rollback()
        finally:
            db.close()

