import csv
import os
from datetime import datetime
from typing import List, Dict, Any

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

    def log_trade(self, symbol: str, action: str, quantity: int, price: float):
        now = datetime.now()
        with open(self.trades_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S"),
                symbol,
                action,
                quantity,
                f"{price:.2f}",
                f"{quantity * price:.2f}"
            ])

    def log_screening_candidates(self, candidates: List[Any]): # Expecting list of StockData
        now = datetime.now()
        with open(self.screening_file, 'a', newline='') as f:
            writer = csv.writer(f)
            for i, c in enumerate(candidates, 1):
                writer.writerow([
                    now.strftime("%Y-%m-%d"),
                    now.strftime("%H:%M:%S"),
                    i,
                    c.symbol,
                    f"{c.current_price:.2f}",
                    f"{c.dma_25:.2f}",
                    f"{c.percent_below_dma * 100:.2f}%"
                ])
