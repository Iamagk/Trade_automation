import argparse
import time
import schedule
import sys
from datetime import datetime
from src.config import config
from src.data.yfinance_provider import YFinanceDataProvider
from src.broker.mock_broker import MockBroker
from src.state_manager import StateManager
from src.strategy import NiftyShopStrategy

from src.broker.zerodha_broker import ZerodhaBroker
from src.auth import get_access_token

def job(use_real_broker: bool = False, is_dry_run: bool = False):
    print(f"\n[SCHEDULER] Triggering strategy at {datetime.now()} (Real Money: {use_real_broker}, Dry Run: {is_dry_run})")
    
    # dependencies
    data_provider = YFinanceDataProvider()
    state_manager = StateManager()
    
    if use_real_broker:
        access_token = get_access_token()
        if not access_token:
            print("ERROR: No valid access token found. Please run with --login first.")
            return
        # Initialize Zerodha Broker
        # config.ZERODHA_API_KEY must be set
        if not config.ZERODHA_API_KEY:
             print("ERROR: ZERODHA_API_KEY not found in config.")
             return
             
        broker = ZerodhaBroker(config.ZERODHA_API_KEY, access_token)
    else:
        broker = MockBroker() 
    
    strategy = NiftyShopStrategy(broker, data_provider, state_manager, dry_run=is_dry_run)
    strategy.run()

def main():
    parser = argparse.ArgumentParser(description="Nifty Shop Strategy")
    parser.add_argument("--run-now", action="store_true", help="Run the strategy immediately")
    parser.add_argument("--schedule", action="store_true", help="Run in schedule mode (wait for 3:20 PM)")
    
    parser.add_argument("--login", action="store_true", help="Run interactive login flow for Zerodha")
    parser.add_argument("--real", action="store_true", help="Use REAL Money/Broker (Zerodha)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without placing orders")
    
    parser.add_argument("--test-order", type=str, help="Place a test BUY order for 1 qty of this symbol (e.g. ALTSTONE)")

    args = parser.parse_args()
    
    if args.login:
        from src.auth import login_flow
        login_flow()
        return

    if args.test_order:
        symbol = args.test_order
        print(f"\n--- TEST ORDER MODE ---")
        print(f"Target: {symbol}")
        print("This will place a REAL MARKET ORDER for 1 Quantity using your Zerodha account.")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return
            
        access_token = get_access_token()
        if not access_token:
            print("ERROR: No valid access token. Run --login first.")
            return
            
        broker = ZerodhaBroker(config.ZERODHA_API_KEY, access_token)
        print(f"Placing order for {symbol}...")
        try:
            # Try NSE First
            try:
                res = broker.place_buy_order(symbol, quantity=1, price=None, exchange="NSE")
                print(f"SUCCESS (NSE): Order placed. ID: {res.order_id}")
            except Exception as e_nse:
                error_msg = str(e_nse).lower()
                if "does not exist" in error_msg or "expired" in error_msg:
                    print(f"NSE Order failed ({e_nse}). Retrying on BSE...")
                    res = broker.place_buy_order(symbol, quantity=1, price=None, exchange="BSE")
                    print(f"SUCCESS (BSE): Order placed. ID: {res.order_id}")
                else:
                    raise e_nse

        except Exception as e:
             print(f"FAILURE: {e}")
        return

    # Configuration for the job
    use_real_broker = args.real
    is_dry_run = args.dry_run

    def scaled_job():
        job(use_real_broker, is_dry_run)

    if args.run_now:
        job(use_real_broker, is_dry_run)
    elif args.schedule:
        import pytz
        
        # Convert Configured IST Time to Local System Time
        ist_tz = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist_tz)
        
        # Parse config time (e.g. "15:20")
        h, m = map(int, config.SCHEDULE_TIME.split(':'))
        
        target_ist = now_ist.replace(hour=h, minute=m, second=0, microsecond=0)
        
        # Convert to Local Time
        target_local = target_ist.astimezone()
        local_schedule_str = target_local.strftime("%H:%M")
        
        print(f"--- Scheduler Setup ---")
        print(f"Target Time (IST): {config.SCHEDULE_TIME}")
        print(f"System Timezone:   {target_local.tzinfo}")
        print(f"Local Schedule:    {local_schedule_str}")
        print(f"-----------------------")
        print(f"Starting Scheduler. Waiting for {local_schedule_str}...")
        
        schedule.every().day.at(local_schedule_str).do(scaled_job)
        
        while True:
            schedule.run_pending()
            time.sleep(1)
            # Optional: Print heartbeat or status if needed, but keeping it silent is standard.
            # To avoid user confusion, we can rely on the logs.
    else:
        print("Please specify --run-now, --schedule, or --login")
        parser.print_help()

if __name__ == "__main__":
    main()
