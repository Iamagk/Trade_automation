"""
models.py
SQLAlchemy models for persisting trade history and daily metrics to PostgreSQL.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from trading_system.config.config import config

Base = declarative_base()

class TradeRecord(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    
    tradingsymbol = Column(String(50), nullable=False)
    option_type = Column(String(10), nullable=False)  # CE or PE
    quantity = Column(Integer, nullable=False)
    
    entry_time = Column(DateTime, nullable=False)
    entry_price = Column(Float, nullable=False)
    entry_order_id = Column(String(50), nullable=False)
    
    exit_time = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)
    exit_order_id = Column(String(50), nullable=True)
    exit_reason = Column(String(50), nullable=True)
    
    pnl = Column(Float, default=0.0)
    
    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "tradingsymbol": self.tradingsymbol,
            "option_type": self.option_type,
            "quantity": self.quantity,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "entry_price": self.entry_price,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_price": self.exit_price,
            "pnl": self.pnl,
            "exit_reason": self.exit_reason
        }

class DailyMetrics(Base):
    __tablename__ = "daily_metrics"

    date = Column(DateTime, primary_key=True, default=datetime.utcnow)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    net_pnl = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    orb_high = Column(Float, nullable=True)
    orb_low = Column(Float, nullable=True)

# ------------------------------------------------------------------
# Database Setup
# ------------------------------------------------------------------

DATABASE_URL = (
    f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}"
    f"@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
