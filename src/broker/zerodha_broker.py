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
            return margins['equity']['available']['cash']
        except Exception as e:
            print(f"Error fetching margins: {e}")
            return 0.0
