"""Database seeding script."""

from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, Base
from backend.models import User
from backend.auth import get_password_hash


def seed_admin_user():
    """Create default admin user."""
    db = SessionLocal()
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("Admin user already exists.")
            return

        # Create admin user
        admin_user = User(
            username="admin",
            hashed_password=get_password_hash("admin123"),
            email="admin@productdescriber.local",
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print(f"✅ Admin user created successfully!")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"   User ID: {admin_user.id}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding database...")
    seed_admin_user()
    print("Done!")
