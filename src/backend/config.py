"""Application configuration and settings."""

import os
from typing import Literal
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_ROOT = BASE_DIR / "local_storage"

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://pd_user:pd_password@localhost:5432/product_describer_db"
)

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Storage
STORAGE_TYPE: Literal["local", "s3"] = os.getenv("STORAGE_TYPE", "local")  # type: ignore
STORAGE_LOCAL_ROOT = Path(os.getenv("STORAGE_LOCAL_ROOT", str(STORAGE_ROOT)))
STORAGE_BUCKET_NAME = os.getenv("STORAGE_BUCKET_NAME", "")
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024)))  # 10MB

# API Keys (existing from product_describer)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")

# Ensure storage directory exists
STORAGE_LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
