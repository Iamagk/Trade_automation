from typing import List, Optional
from .interfaces import IBroker, IDataProvider, StockData, Holding
from .config import config
from .constants import NIFTY_50_TICKERS
from .state_manager import StateManager

class NiftyShopStrategy:
    def __init__(self, broker: IBroker, data_provider: IDataProvider, state_manager: StateManager, dry_run: bool = False):
        self.broker = broker
        self.data_provider = data_provider
        self.state_manager = state_manager
        self.dry_run = dry_run

    def run(self):
        print(f"--- Strategy Run Started ---")
        
        # 1. Screen Stocks
        print("Fetching Nifty 50 Data...")
        stock_data_map = self.data_provider.get_nifty50_data(NIFTY_50_TICKERS)
        
        # Filter stocks fallen below 25 DMA
        candidates = []
        for symbol, data in stock_data_map.items():
            if data.percent_below_dma < 0: # Fallen below
                 candidates.append(data)
        
        # Sort by fell the hardest (most negative percent_below_dma)
        candidates.sort(key=lambda x: x.percent_below_dma)
        
        # Take Top 5
        top_5 = candidates[:5]
        print(f"Top 5 candidates: {[c.symbol for c in top_5]}")

        # Log screening results
        self.state_manager.logger.log_screening_candidates(top_5)
        
        if not top_5:
            print("No stocks found below 25 DMA.")
            return

        # 2. Check Holdings
        holdings = self.broker.get_holdings()
        holdings_map = {h.symbol: h for h in holdings}
        
        holdings_symbols = set(holdings_map.keys())
        top_5_symbols = set([c.symbol for c in top_5])
        
        # "if any in holdings then skip that stock"
        # "if all 5 there, then skip all 5"
        
        new_buy_candidates = [c for c in top_5 if c.symbol not in holdings_symbols]
        
        if new_buy_candidates:
            # Place buy order for the TOP stock (Action 1)
            target = new_buy_candidates[0]
            print(f"Selected for NEW BUY: {target.symbol}")
            self._execute_buy(target, is_averaging=False)
        else:
            # All 5 are in holdings
            print("All Top 5 stocks are already in holdings.")
            # "if any price fall below 10% than your purchase price then average the stock"
            
            averaging_candidates = []
            for c in top_5:
                holding = holdings_map[c.symbol]
                # Calculate drop from purchase price
                # avg_price vs current_price
                # "fall below 10%" -> (current - avg) / avg < -0.10
                
                pct_change = (holding.current_price - holding.average_price) / holding.average_price
                print(f"Checking {c.symbol}: Avg {holding.average_price}, Curr {holding.current_price}, Change {pct_change*100:.2f}%")
                
                if pct_change < -config.HOLDING_DROP_THRESHOLD:
                    averaging_candidates.append(c)
            
            if averaging_candidates:
                # "either one, only one action per day"
                # We pick the one that fell the most? User didn't specify priority.
                # Let's pick the one that fell the most from the top 5 ranking (hardest fall from DMA) 
                # OR hardest fall from purchase price?
                # "average the stock, or place buy order, either one, only one action per day"
                # Let's pick the first valid one for simplicity or the one with biggest drop.
                
                target = averaging_candidates[0]
                print(f"Selected for AVERAGING: {target.symbol}")
                self._execute_buy(target, is_averaging=True)
            else:
                print("No holdings suitable for averaging (none dropped > 10%).")

    def _execute_buy(self, stock: StockData, is_averaging: bool):
        # Calculate quantity
        # "per day for 1 stock it will be 15000 rs"
        # User said "total capital will be 3 l rs... 225000 will be kept for new orders, and 75k will be kept for edging/averaging"
        
        amount = config.PER_STOCK_ALLOCATION
        estimated_qty = int(amount / stock.current_price)
        
        if estimated_qty <= 0:
            print(f"Price {stock.current_price} too high for allocation {amount}.")
            return

        cost = estimated_qty * stock.current_price
        
        if is_averaging:
            if self.state_manager.can_average(cost):
                print(f"Placing AVERAGE order for {stock.symbol}...")
                
                if self.dry_run:
                    print(f"[DRY RUN] Would place BUY order: {stock.symbol}, Qty: {estimated_qty} @ {stock.current_price}")
                else:
                    # Margin Check
                    available_margin = self.broker.get_available_margin()
                    if available_margin < cost:
                        print(f"CRITICAL: Insufficient funds. Required: {cost}, Available: {available_margin}. Skipping {stock.symbol}.")
                        return

                    try:
                        self.broker.place_buy_order(stock.symbol, estimated_qty, stock.current_price)
                        self.state_manager.record_averaging(
                            symbol=stock.symbol,
                            quantity=estimated_qty,
                            price=stock.current_price,
                            cost=cost,
                            message=f"Averaged {stock.symbol}: {estimated_qty} @ {stock.current_price}"
                        )
                    except Exception as e:
                        print(f"CRITICAL ERROR: Failed to average {stock.symbol}: {e}")
            else:
                print("Averaging capital limit reached. Skipping.")
        else:
            # New Buy
            if self.state_manager.can_place_new_order(cost):
                print(f"Placing NEW order for {stock.symbol}...")
                
                if self.dry_run:
                     print(f"[DRY RUN] Would place BUY order: {stock.symbol}, Qty: {estimated_qty} @ {stock.current_price}")
                else:
                    # Margin Check
                    available_margin = self.broker.get_available_margin()
                    if available_margin < cost:
                        print(f"CRITICAL: Insufficient funds. Required: {cost}, Available: {available_margin}. Skipping {stock.symbol}.")
                        return

                    try:
                        self.broker.place_buy_order(stock.symbol, estimated_qty, stock.current_price)
                        self.state_manager.record_new_order(
                            symbol=stock.symbol,
                            quantity=estimated_qty,
                            price=stock.current_price,
                            cost=cost,
                            message=f"Bought {stock.symbol}: {estimated_qty} @ {stock.current_price}"
                        )
                    except Exception as e:
                        print(f"CRITICAL ERROR: Failed to buy {stock.symbol}: {e}")
            else:
                print("New Order capital limit reached or Max Daily Orders reached. Skipping.")

