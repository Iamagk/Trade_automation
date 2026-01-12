from typing import List, Optional, Dict
from ..interfaces import IBroker, Holding, OrderResult
from ..config import config
import uuid

class MockBroker(IBroker):
    def __init__(self, initial_holdings: List[Holding] = None):
        self.holdings: Dict[str, Holding] = {}
        if initial_holdings:
            for h in initial_holdings:
                self.holdings[h.symbol] = h
        
        self.cash_balance = config.TOTAL_CAPITAL 
        # For simplicity, we assume we start with full capital in this mock
        # Real logic would need to know actual cash balance
        
    def get_holdings(self) -> List[Holding]:
        return list(self.holdings.values())

    def place_buy_order(self, symbol: str, quantity: int, price: Optional[float] = None) -> OrderResult:
        cost = quantity * price
        
        print(f"[MOCK BROKER] Placed BUY order for {symbol}: {quantity} qty @ {price}")
        
        # Update mock holdings
        if symbol in self.holdings:
            h = self.holdings[symbol]
            new_qty = h.quantity + quantity
            new_avg = ((h.quantity * h.average_price) + (quantity * price)) / new_qty
            h.quantity = new_qty
            h.average_price = new_avg
            h.current_price = price # Update current price
        else:
            self.holdings[symbol] = Holding(
                symbol=symbol,
                quantity=quantity,
                average_price=price,
                current_price=price
            )
            
        return OrderResult(
            order_id=str(uuid.uuid4()),
            status="COMPLETE",
            average_price=price,
            quantity=quantity,
            symbol=symbol
        )
    
    def get_available_margin(self) -> float:
        return 1000000.0 # Mock infinite margin
