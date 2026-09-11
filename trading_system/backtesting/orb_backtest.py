"""
orb_backtest.py
Example vectorbt backtest for the 9:15-9:45 ORB Strategy.

Usage:
  This is a structural demonstration. To run this, you need 5-minute
  historical NIFTY spot data and an approximation for option premiums.
"""

import pandas as pd
import numpy as np
import vectorbt as vbt
from loguru import logger

def fetch_historical_nifty_data(start_date: str, end_date: str) -> pd.DataFrame:
    """Mock function — replace with actual DB or CSV fetch."""
    logger.info(f"Fetching data from {start_date} to {end_date}")
    # Create fake 5-min index
    dt_index = pd.date_range(start_date, end_date, freq='5min')
    df = pd.DataFrame(index=dt_index)
    
    # Filter for market hours (9:15 - 15:30)
    df = df.between_time('09:15', '15:30')
    
    # Generate random walk prices
    np.random.seed(42)
    daily_returns = np.random.normal(0, 0.001, len(df))
    df['Close'] = 22000 * np.exp(np.cumsum(daily_returns))
    df['High'] = df['Close'] + 10
    df['Low'] = df['Close'] - 10
    
    return df

def run_orb_backtest():
    logger.info("Starting ORB Backtest Simulation")
    df = fetch_historical_nifty_data('2024-01-01', '2024-01-31')
    
    # 1. Identify daily ORB High/Low
    # Resample to daily to find first 30 mins
    
    # For a real backtest, we iterate day by day.
    # We collect rows between 9:15 and 9:45
    df['Date'] = df.index.date
    df['Time'] = df.index.time
    
    # Find max high and min low before 9:45
    orb_window = df[df.index.time <= pd.to_datetime('09:45').time()]
    daily_orb_high = orb_window.groupby('Date')['High'].max()
    daily_orb_low = orb_window.groupby('Date')['Low'].min()
    
    # Map back to main dataframe
    df['ORB_High'] = df['Date'].map(daily_orb_high)
    df['ORB_Low'] = df['Date'].map(daily_orb_low)
    
    # 2. Generate Signals
    # Ignore signals before 9:45 and after 15:00
    valid_time = (df.index.time > pd.to_datetime('09:45').time()) & (df.index.time <= pd.to_datetime('15:00').time())
    
    # Buy Call if close > ORB_High
    df['Buy_CE_Signal'] = (df['Close'] > df['ORB_High']) & valid_time
    
    # Buy Put if close < ORB_Low
    df['Buy_PE_Signal'] = (df['Close'] < df['ORB_Low']) & valid_time
    
    # Since we need to limit to 1 trade per day per direction, we take argmax
    # This is a simplified vectorbt execution ignoring complex state-machine trailing SLs
    
    entries = df['Buy_CE_Signal']
    # Force exit at end of day
    exits = df.index.time == pd.to_datetime('15:25').time()
    
    logger.info("Running VectorBT Portfolio Simulation (Calls Only Approximation)")
    portfolio = vbt.Portfolio.from_signals(
        close=df['Close'],
        entries=entries,
        exits=exits,
        init_cash=100000.0,
        fees=0.001,  # Slip & Commissions
        sl_stop=0.005, # Fixed 0.5% spot move SL
        tp_stop=0.01   # Fixed 1% spot move Target
    )
    
    metrics = portfolio.stats()
    logger.info(f"\n{metrics}")
    
    return metrics

if __name__ == "__main__":
    run_orb_backtest()
