from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from ..database import engine, Base
from .. import models

# Create database tables
# models.Base.metadata.create_all(bind=engine) # We'll do this on startup or via migrations

app = FastAPI(title="Nifty Shop Strategy API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "Nifty Shop Strategy API is running"}
