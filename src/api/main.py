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

from . import auth
from ..database import engine, Base, SessionLocal

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed default user if not exists
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == "admin").first()
        if not user:
            print("Seeding default admin user...")
            hashed_pw = auth.get_password_hash("admin123")
            new_user = models.User(username="admin", hashed_password=hashed_pw)
            db.add(new_user)
            db.commit()
            print("Default admin user created.")
    except Exception as e:
        print(f"Error seeding user: {e}")
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Nifty Shop Strategy API is running"}
