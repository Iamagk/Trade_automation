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
                # 1. Get Historical Data for DMA (Daily)
                series = None
                
                # Try Adj Close first
                if 'Adj Close' in data.columns.get_level_values(0):
                    adj_df = data['Adj Close']
                    if ticker in adj_df.columns:
                        series = adj_df[ticker]
                
                # Fallback to Close if series is still None
                if series is None and 'Close' in data.columns.get_level_values(0):
                    close_df = data['Close']
                    if ticker in close_df.columns:
                        series = close_df[ticker]
                
                if series is None:
                    # Ticker likely failed download
                    continue

                series = series.dropna()
                if len(series) < config.DMA_PERIOD:
                    print(f"Not enough data for {ticker}")
                    continue
                
                # 2. Get accurate Real-Time LTP
                ticker_obj = yf.Ticker(ticker)
                # fast_info is much faster and more accurate for LTP than history()
                try:
                    current_price = ticker_obj.fast_info['last_price']
                except:
                    # Fallback to history 1m
                    hist_1m = ticker_obj.history(period="1d", interval="1m")
                    if not hist_1m.empty:
                        current_price = hist_1m['Close'].iloc[-1]
                    else:
                        current_price = series.iloc[-1]
                
                # Calculate 25 DMA
                dma_25 = series.rolling(window=config.DMA_PERIOD).mean().iloc[-1]
                
                if pd.isna(dma_25):
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
