import sys
import os
from sqlalchemy import text

# Add src to python path to allow importing backend modules
sys.path.append(os.path.join(os.getcwd(), "src"))

from backend.database import SessionLocal
from backend.models.generation import GenerationRequest, GeneratedImage

def clear_generations():
    print("Connecting to database...")
    db = SessionLocal()
    try:
        # Delete all generated images
        deleted_images = db.query(GeneratedImage).delete()
        print(f"Deleted {deleted_images} generated images.")
        
        # Delete all generation requests
        deleted_requests = db.query(GenerationRequest).delete()
        print(f"Deleted {deleted_requests} generation requests.")
        
        db.commit()
        print("Successfully cleared all generation data from database.")
    except Exception as e:
        print(f"Error clearing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    confirm = input("This will delete ALL generated images and requests from the database. Are you sure? (y/N): ")
    if confirm.lower() == 'y':
        clear_generations()
    else:
        print("Operation cancelled.")
