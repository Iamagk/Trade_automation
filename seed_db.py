from src.database import SessionLocal, engine, Base
from src.models import User
from src.api.auth import get_password_hash
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

def seed_user():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if user already exists
        user = db.query(User).filter(User.username == "admin").first()
        if not user:
            print("Creating admin user...")
            hashed_password = get_password_hash("admin123")
            admin_user = User(
                username="admin",
                full_name="Administrator",
                hashed_password=hashed_password
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_user()
