from pydantic import BaseModel
from typing import Optional, List

class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ScreeningLogResponse(BaseModel):
    id: int
    date: str
    time: str
    rank: int
    symbol: str
    current_price: float
    dma_25: float
    percent_below_dma: str

    class Config:
        from_attributes = True

class TradeResponse(BaseModel):
    id: int
    date: str
    time: str
    symbol: str
    action: str
    quantity: int
    price: float
    total_cost: float

    class Config:
        from_attributes = True
