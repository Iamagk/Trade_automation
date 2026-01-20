from typing import List, Optional, Dict
from ..interfaces import IBroker, Holding, OrderResult
from kiteconnect import KiteConnect
import logging

class ZerodhaBroker(IBroker):
    def __init__(self, api_key: str, access_token: str):
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)

    def get_holdings(self) -> List[Holding]:
        try:
            k_holdings = self.kite.holdings()
            holdings_list = []
            for h in k_holdings:
                # Zerodha symbols usually match NSE Symbols but might need mapping if instrument_token is used
                # We typically use 'tradingsymbol'
                symbol = h['tradingsymbol'] 
                # Note: yfinance uses .NS suffix. We might need to handle this discrepancy.
                # Usually Nifty 50 tradingsymbols are just 'ITC', 'RELIANCE' etc.
                # Strategy expects 'ITC.NS'. We should append .NS if missing.
                
                if not symbol.endswith(".NS"):
                    symbol = f"{symbol}.NS"
                
                holdings_list.append(Holding(
                    symbol=symbol,
                    quantity=int(h['quantity']),
                    average_price=float(h['average_price']),
                    current_price=float(h['last_price'])
                ))
            return holdings_list
        except Exception as e:
            print(f"Error fetching holdings from Zerodha: {e}")
            return []

    def place_buy_order(self, symbol: str, quantity: int, price: Optional[float] = None, exchange: str = "NSE") -> OrderResult:
        try:
            # Round price to nearest 0.05 (tick size) if provided
            if price is not None:
                price = round(price * 20) / 20.0

            # Cleanup symbol suffix if present, regardless of exchange
            trading_symbol = symbol.replace(".NS", "").replace(".BO", "")
            
            # Place Order
            # For simplicity, using MARKET order if price is None, else LIMIT
            order_type = self.kite.ORDER_TYPE_MARKET if price is None else self.kite.ORDER_TYPE_LIMIT
            
            order_id = self.kite.place_order(
                tradingsymbol=trading_symbol,
                exchange=exchange,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY,
                quantity=quantity,
                variety=self.kite.VARIETY_REGULAR,
                order_type=order_type,
                product=self.kite.PRODUCT_CNC, # CNC for Holdings/Delivery
                price=price,
                validity=self.kite.VALIDITY_DAY
            )
            
            print(f"Order placed successfully. ID: {order_id}")
            
            return OrderResult(
                order_id=str(order_id),
                status="COMPLETE", # Ideally we check status via order_history, but assume placed = complete for now or "SUBMITTED"
                average_price=price if price else 0.0, # Approximate
                quantity=quantity,
                symbol=symbol
            )
        except Exception as e:
            print(f"Error placing order for {symbol}: {e}")
            raise e
    
    def get_available_margin(self) -> float:
        try:
            margins = self.kite.margins()
            
            # Extract equity margins
            equity_margins = margins.get('equity', {})
            available = equity_margins.get('available', {})
            
            # The user's response shows funds in:
            # 1. equity['net']
            # 2. equity['available']['live_balance']
            # 3. equity['available']['opening_balance']
            
            live_balance = available.get('live_balance', 0.0)
            net_balance = equity_margins.get('net', 0.0)
            cash_balance = available.get('cash', 0.0)
            
            final_margin = max(float(live_balance), float(net_balance), float(cash_balance))
            
            print(f"[DEBUG] Margin Check - Live: {live_balance}, Net: {net_balance}, Cash: {cash_balance} -> Using: {final_margin}")
            
            return final_margin
        except Exception as e:
            print(f"Error fetching margins: {e}")
            return 0.0

    def get_ltp(self, symbols: List[str]) -> Dict[str, float]:
        """
        Fetch Last Traded Price from Yahoo Finance.
        Zerodha API has permission restrictions for market data.
        """
        try:
            import yfinance as yf
            
            result = {}
            for symbol in symbols:
                try:
                    # Ensure symbol has .NS suffix for NSE stocks
                    yf_symbol = symbol if symbol.endswith('.NS') else f"{symbol}.NS"
                    ticker = yf.Ticker(yf_symbol)
                    
                    # Get the current price (last traded price)
                    info = ticker.info
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                    
                    if current_price:
                        result[symbol] = float(current_price)
                    else:
                        # Fallback: try to get from history
                        hist = ticker.history(period='1d')
                        if not hist.empty:
                            result[symbol] = float(hist['Close'].iloc[-1])
                except Exception as e:
                    print(f"Error fetching LTP for {symbol}: {e}")
                    continue
            
            return result
        except Exception as e:
            print(f"Error fetching LTP from Yahoo Finance: {e}")
            return {}
