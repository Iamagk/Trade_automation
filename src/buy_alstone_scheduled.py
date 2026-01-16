import argparse
import time
import schedule
import pytz
from datetime import datetime
from src.config import config
from src.auth import get_access_token
from src.broker.zerodha_broker import ZerodhaBroker

def execute_buy(symbol="ALSTONE"):
    print(f"\n[ACTION] Waking up to buy {symbol}...")
    
    access_token = get_access_token()
    if not access_token:
        print("ERROR: No valid access token found. Please run with --login first.")
        return

    broker = ZerodhaBroker(config.ZERODHA_API_KEY, access_token)
    
    print(f"Placing order for {symbol}...")
    try:
        # Robust Logic: Try NSE, then BSE
        try:
            res = broker.place_buy_order(symbol, quantity=1, price=None, exchange="NSE")
            print(f"SUCCESS (NSE): Order placed. ID: {res.order_id}")
        except Exception as e_nse:
            # Check for common "does not exist" errors
            error_msg = str(e_nse).lower()
            if "does not exist" in error_msg or "expired" in error_msg:
                print(f"NSE Order failed ({e_nse}). Retrying on BSE...")
                res = broker.place_buy_order(symbol, quantity=1, price=None, exchange="BSE")
                print(f"SUCCESS (BSE): Order placed. ID: {res.order_id}")
            else:
                raise e_nse

    except Exception as e:
         print(f"FAILURE: {e}")

def main():
    parser = argparse.ArgumentParser(description="Scheduled ALSTONE Buy")
    parser.add_argument("--run-now", action="store_true", help="Run immediately without waiting")
    args = parser.parse_args()

    if args.run_now:
        execute_buy()
        return

    # Scheduler Logic 
    # (Copied from main.py to ensure identical behavior)
    ist_tz = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist_tz)
    
    # Parse config time (e.g. "15:20")
    h, m = map(int, config.SCHEDULE_TIME.split(':'))
    
    target_ist = now_ist.replace(hour=h, minute=m, second=0, microsecond=0)
    
    # Check if target time has already passed for today
    # If so, do we schedule for tomorrow? User request implied "at 3:20 PM".
    # Standard scheduler logic: schedule.every().day.at(...) handles the "next run".
    # But for a one-off run script, we might just want to exit if passed?
    # User said "make another script that will buy one more share ... at 3:20 PM".
    # I'll stick to the looping scheduler to be safe (so if they start it at 3:19, it works).
    
    target_local = target_ist.astimezone()
    local_schedule_str = target_local.strftime("%H:%M")
    
    print(f"--- ALSTONE Buy Scheduler ---")
    print(f"Target Time (IST): {config.SCHEDULE_TIME}")
    print(f"System Timezone:   {target_local.tzinfo}")
    print(f"Local Schedule:    {local_schedule_str}")
    print(f"-----------------------------")
    print(f"Waiting for {local_schedule_str}...")
    
    # Use schedule lib
    schedule.every().day.at(local_schedule_str).do(execute_buy)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
