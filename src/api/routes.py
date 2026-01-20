from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..database import get_db
from .. import models
from . import auth, schemas
from .bot_manager import bot_manager
from datetime import timedelta

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except auth.JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/screening-logs", response_model=List[schemas.ScreeningLogResponse])
async def read_screening_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    logs = db.query(models.ScreeningLog).offset(skip).limit(limit).all()
    return logs

@router.get("/trades", response_model=List[schemas.TradeResponse])
async def read_trades(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    trades = db.query(models.Trade).offset(skip).limit(limit).all()
    return trades

@router.get("/stats")
async def read_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Calculate active investment (cost basis of current holdings)
    trades = db.query(models.Trade).all()
    holdings_dict = {}
    for trade in trades:
        symbol = trade.symbol
        if symbol not in holdings_dict:
            holdings_dict[symbol] = {"qty": 0, "cost": 0.0}
        
        action = trade.action.upper()
        if action in ["BUY", "AVERAGE"]:
            holdings_dict[symbol]["qty"] += trade.quantity
            holdings_dict[symbol]["cost"] += trade.total_cost
        elif action == "SELL":
            old_qty = holdings_dict[symbol]["qty"]
            if old_qty > 0:
                avg_price = holdings_dict[symbol]["cost"] / old_qty
                holdings_dict[symbol]["qty"] -= trade.quantity
                holdings_dict[symbol]["cost"] -= (trade.quantity * avg_price)
    
    total_cost = sum(h["cost"] for h in holdings_dict.values() if h["qty"] > 0)
    total_trades = len(trades)
    
    # Correctly find the latest screening run
    latest_run = db.query(models.ScreeningLog.date, models.ScreeningLog.time).order_by(models.ScreeningLog.timestamp.desc()).first()
    
    if latest_run:
        last_screening = db.query(models.ScreeningLog).filter(
            models.ScreeningLog.date == latest_run.date,
            models.ScreeningLog.time == latest_run.time
        ).order_by(models.ScreeningLog.rank.asc()).all()
    else:
        last_screening = []
    
    return {
        "total_trades": total_trades,
        "total_cost": total_cost,
        "last_screening": last_screening
    }

@router.post("/bot/start")
async def start_bot(data: dict, current_user: models.User = Depends(get_current_user)):
    mode = data.get("mode")
    if not mode:
        raise HTTPException(status_code=400, detail="Mode is required")
    
    success = bot_manager.start_bot(mode)
    if not success:
        raise HTTPException(status_code=400, detail="Bot is already running or invalid mode")
    
    return {"status": "started", "mode": mode}

@router.post("/bot/stop")
async def stop_bot(current_user: models.User = Depends(get_current_user)):
    success = bot_manager.stop_bot()
    if not success:
        raise HTTPException(status_code=400, detail="Bot is not running or could not be stopped")
    
    return {"status": "stopped"}
    
@router.post("/bot/input")
async def send_bot_input(data: dict, current_user: models.User = Depends(get_current_user)):
    input_text = data.get("input")
    if not input_text:
        raise HTTPException(status_code=400, detail="Input is required")
    
    success = bot_manager.send_input(input_text)
    if not success:
        raise HTTPException(status_code=400, detail="Bot is not running or could not receive input")
    
    return {"status": "sent"}

@router.get("/bot/status")
async def get_bot_status(current_user: models.User = Depends(get_current_user)):
    return bot_manager.get_status()

@router.get("/holdings", response_model=List[schemas.HoldingResponse])
async def read_holdings(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    from ..broker.zerodha_broker import ZerodhaBroker
    from ..auth import get_access_token
    from ..config import config
    
    # 1. Fetch all trades from database
    trades = db.query(models.Trade).all()
    
    # 2. Aggregate trades into holdings
    holdings_dict = {}
    for trade in trades:
        symbol = trade.symbol
        if symbol not in holdings_dict:
            holdings_dict[symbol] = {"total_qty": 0, "total_cost": 0.0}
        
        action = trade.action.upper()
        if action in ["BUY", "AVERAGE"]:
            holdings_dict[symbol]["total_qty"] += trade.quantity
            holdings_dict[symbol]["total_cost"] += trade.total_cost
        elif action == "SELL":
            # Avoid division by zero if trade history is corrupted
            old_qty = holdings_dict[symbol]["total_qty"]
            if old_qty > 0:
                # Reduce cost proportionally based on the average price before the sell
                avg_price_before = holdings_dict[symbol]["total_cost"] / old_qty
                holdings_dict[symbol]["total_qty"] -= trade.quantity
                holdings_dict[symbol]["total_cost"] -= (trade.quantity * avg_price_before)
            else:
                # Should not happen with valid bot data, but prevent negative cost
                holdings_dict[symbol]["total_qty"] -= trade.quantity

    # Filter out closed positions
    bot_holdings = []
    symbols_to_fetch = []
    for symbol, data in holdings_dict.items():
        if data["total_qty"] > 0:
            avg_price = data["total_cost"] / data["total_qty"]
            bot_holdings.append({
                "symbol": symbol,
                "quantity": data["total_qty"],
                "average_price": avg_price,
                "current_price": avg_price # Fallback
            })
            symbols_to_fetch.append(symbol)

    if not bot_holdings:
        return []

    # 3. Fetch live prices for these symbols
    access_token = get_access_token()
    if access_token:
        try:
            broker = ZerodhaBroker(api_key=config.ZERODHA_API_KEY, access_token=access_token)
            ltp_map = broker.get_ltp(symbols_to_fetch)
            
            for h in bot_holdings:
                if h["symbol"] in ltp_map:
                    h["current_price"] = ltp_map[h["symbol"]]
        except Exception as e:
            print(f"Error fetching live prices for holdings: {e}")

    return bot_holdings

@router.get("/bot/logs")
async def get_bot_logs(current_user: models.User = Depends(get_current_user)):
    return {"logs": bot_manager.get_logs()}


