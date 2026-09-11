"""
predictor.py
ML Prediction Engine for price direction.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import pandas_ta as ta
import yfinance as yf
from loguru import logger
import os
import joblib
from datetime import datetime, timedelta

class MLPredictor:
    def __init__(self, model_dir="models"):
        self.model_dir = model_dir
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
        self.models = {}

    def prepare_features(self, df):
        """Calculate technical indicators as features."""
        # Ensure enough data
        if len(df) < 50:
            return None
        
        # Momentum
        df['RSI'] = ta.rsi(df['close'], length=14)
        macd = ta.macd(df['close'])
        df = pd.concat([df, macd], axis=1)
        
        # Trend
        df['EMA_9'] = ta.ema(df['close'], length=9)
        df['EMA_20'] = ta.ema(df['close'], length=20)
        df['EMA_50'] = ta.ema(df['close'], length=50)
        df['VWAP'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
        
        # Volatility
        df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        bbands = ta.bbands(df['close'], length=20, std=2)
        df = pd.concat([df, bbands], axis=1)
        
        # Target: 1 if next 5-min close is higher, else 0
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
        
        return df.dropna()

    async def train_model(self, symbol):
        """Train a model for a specific symbol using historical data."""
        logger.info(f"Training model for {symbol}...")
        
        # Download data (last 60 days of 5-min candles)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=59)
        
        df = yf.download(symbol.replace("-EQ", ".NS"), start=start_date, end=end_date, interval="5m")
        if df.empty:
            logger.error(f"No data found for {symbol}")
            return
            
        df.columns = [c.lower() for c in df.columns]
        data = self.prepare_features(df)
        
        if data is None or len(data) < 100:
            logger.error(f"Insufficient data for training {symbol}")
            return

        features = ['RSI', 'MACD_12_26_9', 'EMA_9', 'EMA_20', 'EMA_50', 'ATR'] # Simplified for now
        X = data[features]
        y = data['target']
        
        model = xgb.XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1)
        model.fit(X, y)
        
        model_path = os.path.join(self.model_dir, f"{symbol}_model.joblib")
        joblib.dump(model, model_path)
        self.models[symbol] = model
        logger.info(f"Model saved for {symbol}")

    def predict(self, symbol, current_data_df):
        """Predict direction for the next candle."""
        if symbol not in self.models:
            model_path = os.path.join(self.model_dir, f"{symbol}_model.joblib")
            if os.path.exists(model_path):
                self.models[symbol] = joblib.load(model_path)
            else:
                return 0.5 # Neutral if no model

        data = self.prepare_features(current_data_df)
        if data is None or data.empty:
            return 0.5
            
        features = ['RSI', 'MACD_12_26_9', 'EMA_9', 'EMA_20', 'EMA_50', 'ATR']
        latest_X = data[features].iloc[-1:]
        
        prob = self.models[symbol].predict_proba(latest_X)[0][1]
        return prob

predictor = MLPredictor()
