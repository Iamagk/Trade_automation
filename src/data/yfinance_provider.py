import yfinance as yf
import pandas as pd
from typing import List, Dict
from ..interfaces import IDataProvider, StockData
from ..config import config

class YFinanceDataProvider(IDataProvider):
    def get_nifty50_data(self, tickers: List[str]) -> Dict[str, StockData]:
        # Download data for all tickers at once
        # We need at least enough days to calculate 25 DMA + current day
        # 60 days is safe to cover weekends/holidays
        data = yf.download(tickers, period="3mo", interval="1d", progress=False)
        
        # 'Adj Close' is usually best for calculating DMAs to account for dividends/splits
        # Prepare result
        result = {}
        
        # Access using the MultiIndex (Price, Ticker) or (Ticker, Price) structure
        # yfinance normally returns (Price, Ticker) as columns.
        
        for ticker in tickers:
            try:
                # Try to get Adj Close, fall back to Close
                series = None
                
                # Check for Adj Close presence in MultiIndex columns
                if 'Adj Close' in data.columns.get_level_values(0):
                    adj_close_cols = data['Adj Close'].columns
                    if ticker in adj_close_cols:
                        series = data['Adj Close'][ticker]
                
                # Fallback to Close if Adj Close not found
                if series is None and 'Close' in data.columns.get_level_values(0):
                    close_cols = data['Close'].columns
                    if ticker in close_cols:
                        series = data['Close'][ticker]
                
                if series is None:
                    # Ticker might be delisted or download failed
                    continue

                series = series.dropna()
                if len(series) < config.DMA_PERIOD:
                    print(f"Not enough data for {ticker}")
                    continue
                
                current_price = series.iloc[-1]
                
                # Calculate 25 DMA
                dma_25 = series.rolling(window=config.DMA_PERIOD).mean().iloc[-1]
                
                # Handle NaN dma if rolling window not satisfied (should be covered by len check but safety first)
                if pd.isna(dma_25):
                    print(f"DMA calculation failed (NaN) for {ticker}")
                    continue
                
                percent_below = (current_price - dma_25) / dma_25
                
                result[ticker] = StockData(
                    symbol=ticker,
                    current_price=float(current_price),
                    dma_25=float(dma_25),
                    percent_below_dma=float(percent_below)
                )
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                
        return result
