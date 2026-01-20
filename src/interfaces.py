from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class StockData:
    symbol: str
    current_price: float
    dma_25: float
    percent_below_dma: float

@dataclass
class OrderResult:
    order_id: str
    status: str
    average_price: float
    quantity: int
    symbol: str

@dataclass
class Holding:
    symbol: str
    quantity: int
    average_price: float
    current_price: float

class IDataProvider(ABC):
    @abstractmethod
    def get_nifty50_data(self, tickers: List[str]) -> Dict[str, StockData]:
        """
        Fetches data for the given tickers.
        Returns a dictionary mapping symbol -> StockData.
        Should calculate the 25 DMA and current price.
        """
        pass

class IBroker(ABC):
    @abstractmethod
    def get_holdings(self) -> List[Holding]:
        """
        Returns a list of current holdings.
        """
        pass

    @abstractmethod
    def place_buy_order(self, symbol: str, quantity: int, price: Optional[float] = None) -> OrderResult:
        """
        Places a buy order. If price is None, assumes Market Order.
        """
        pass
    
    @abstractmethod
    def get_available_margin(self) -> float:
        """
        Returns available cash margin.
        """
        pass

    @abstractmethod
    def get_ltp(self, symbols: List[str]) -> Dict[str, float]:
        """
        Returns a dictionary of symbol -> Last Traded Price.
        """
        pass
