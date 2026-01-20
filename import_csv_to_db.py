import csv
import os
from datetime import datetime
from src.database import SessionLocal, engine, Base
from src.models import Trade, ScreeningLog

def import_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Import Trades
        if os.path.exists("trades.csv"):
            with open("trades.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Check if trade already exists (simplistic check)
                    exists = db.query(Trade).filter(
                        Trade.date == row['Date'],
                        Trade.symbol == row['Symbol'],
                        Trade.time == row['Time']
                    ).first()
                    
                    if not exists:
                        trade = Trade(
                            date=row['Date'],
                            time=row['Time'],
                            symbol=row['Symbol'],
                            action=row['Action'],
                            quantity=int(row['Quantity']),
                            price=float(row['Price']),
                            total_cost=float(row['Total Cost'])
                        )
                        db.add(trade)
            print("Trades imported successfully.")

        # Import Screening Logs
        if os.path.exists("screening_log.csv"):
            with open("screening_log.csv", "r") as f:
                # No header in screening_log.csv based on preview
                # Format: Date,Time,Rank,Symbol,Price,25DMA,PercentBelow
                reader = csv.reader(f)
                for row in reader:
                    if not row: continue
                    # row: ['2026-01-19', '12:00:02', '1', 'ITC.NS', '332.65', '370.65', '-10.25%']
                    exists = db.query(ScreeningLog).filter(
                        ScreeningLog.date == row[0],
                        ScreeningLog.time == row[1],
                        ScreeningLog.symbol == row[3]
                    ).first()
                    
                    if not exists:
                        log = ScreeningLog(
                            date=row[0],
                            time=row[1],
                            rank=int(row[2]),
                            symbol=row[3],
                            current_price=float(row[4]),
                            dma_25=float(row[5]),
                            percent_below_dma=row[6]
                        )
                        db.add(log)
            print("Screening logs imported successfully.")
            
        db.commit()
    except Exception as e:
        print(f"Error during import: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_data()
