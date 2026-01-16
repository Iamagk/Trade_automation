from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Integer, default=1) # Using integer for simplicity if needed, but Boolean is fine too

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String) # Storing as string to match existing CSV format for now, or use Date
    time = Column(String)
    symbol = Column(String, index=True)
    action = Column(String)
    quantity = Column(Integer)
    price = Column(Float)
    total_cost = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ScreeningLog(Base):
    __tablename__ = "screening_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String)
    time = Column(String)
    rank = Column(Integer)
    symbol = Column(String, index=True)
    current_price = Column(Float)
    dma_25 = Column(Float)
    percent_below_dma = Column(String) # Storing as string with % for now
    timestamp = Column(DateTime, default=datetime.utcnow)
