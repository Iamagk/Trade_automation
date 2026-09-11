"""
dashboard_routes.py
FastAPI control layer and monitoring dashboard for the trading engine.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from loguru import logger
from typing import List

from trading_system.storage.models import get_db, TradeRecord
from trading_system.risk.position_manager import PositionManager
from trading_system.risk.risk_rules import RiskRules
from trading_system.strategy.tpb_strategy import TPBStrategy

# Initialize the global instances that the bot engine uses
position_manager = PositionManager()
risk_rules = RiskRules()
tpb_strategy = TPBStrategy()

app = FastAPI(title="F&O Automation Engine API")

# Setup CORS for the frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "engine": "running"}

from trading_system.config.config import config

@app.get("/api/state")
def get_system_state():
    """Returns the comprehensive real-time state of the engine."""
    from trading_system.main import engine
    return {
        "engine_state": engine.position_manager.state.name,
        "running": engine.ws_client.is_connected,
        "is_started": engine.ws_client.is_started,
        "position": position_manager.get_position_summary(),
        "tpb_strategy": {
            "is_established": tpb_strategy.is_established,
            "trend": tpb_strategy.trend.value,
            "pullback_occurred": tpb_strategy.pullback_occurred,
            "signal_fired": tpb_strategy.signal_fired,
            "atm_strike": tpb_strategy.atm_strike,
            "target": tpb_strategy.target,
            "stop_loss": tpb_strategy.stop_loss,
            "reasoning": tpb_strategy.reasoning
        },
        "risk": {
            "trades_today": risk_rules.trades_today,
            "consecutive_losses": risk_rules.consecutive_losses,
            "daily_pnl": risk_rules.daily_pnl,
            "trading_halted": risk_rules.trading_halted,
            "is_simulation": config.IS_SIMULATION
        },
        "chart_data": [
            {
                "time": c.timestamp.strftime("%H:%M"),
                "price": c.close,
                "vwap": c.vwap
            } for c in engine.candle_builder.candle_history[-20:]
        ]
    }

@app.post("/api/command")
async def handle_command(payload: dict):
    """Handle general engine commands like START/STOP."""
    from trading_system.main import engine
    cmd = payload.get("command", "").upper()
    
    if cmd == "START":
        engine.start()
        return {"status": "success", "message": "Engine started"}
    elif cmd == "STOP":
        engine.stop()
        engine.ws_client.is_started = False
        return {"status": "success", "message": "Engine stopped"}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown command: {cmd}")

@app.get("/api/trades", response_model=List[dict])
def get_recent_trades(limit: int = 50, db: Session = Depends(get_db)):
    """Fetch trade history from the database."""
    trades = db.query(TradeRecord).order_by(TradeRecord.id.desc()).limit(limit).all()
    return [t.to_dict() for t in trades]

@app.post("/api/trade/manual")
async def manual_trade(signal_type: str):
    """
    Manually trigger a trade signal (BUY_CE or BUY_PE).
    This allows the user to bypass the ORB logic from the CLI.
    """
    from trading_system.main import engine
    await engine.on_signal(signal_type)
    return {"status": "success", "message": f"Manual signal {signal_type} triggered"}

@app.post("/api/trade/exit")
async def manual_exit():
    """Manually square off any open position."""
    from trading_system.main import engine
    await engine.force_exit_position("Manual exit requested via API")
    return {"status": "success", "message": "Manual exit initiated"}

@app.post("/api/simulation/toggle")
async def toggle_simulation(enabled: bool):
    """Toggle Dry Run / Simulation mode at runtime."""
    config.IS_SIMULATION = enabled
    mode = "SIMULATION (Dry Run)" if enabled else "LIVE (Real Orders)"
    logger.warning(f"Engine mode changed to: {mode}")
    return {"status": "success", "mode": mode}

@app.post("/api/kill")
def kill_switch():
    """Immediately halt trading and force square-off if in position. (Implementation delegated to main loop checking risk_rules.trading_halted)"""
    risk_rules.halt()
    return {"status": "halted", "message": "Kill switch activated. No new trades will be placed."}

@app.post("/api/recovery/tpb")
async def recover_tpb():
    """Attempt to recover today's TPB setup from historical data."""
    from trading_system.main import engine
    success = await engine.recover_history()
    if success:
        return {"status": "success", "message": "Strategy setup recovered successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to recover history. Check logs.")
