"""Storage service for managing files."""

import os
import shutil
from pathlib import Path
from typing import BinaryIO, Optional
from datetime import datetime
import hashlib

from backend.config import STORAGE_LOCAL_ROOT, STORAGE_TYPE


class StorageService:
    """Service for handling file storage (local or S3)."""
    
    def __init__(self):
        self.storage_type = STORAGE_TYPE
        self.local_root = Path(STORAGE_LOCAL_ROOT)
        self.local_root.mkdir(parents=True, exist_ok=True)
    
    def _get_product_path(self, product_slug: str) -> Path:
        """Get the base path for a product."""
        path = self.local_root / product_slug
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def _get_refs_path(self, product_slug: str) -> Path:
        """Get the references directory for a product."""
        path = self._get_product_path(product_slug) / "refs"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def _get_specs_path(self, product_slug: str) -> Path:
        """Get the specifications directory for a product."""
        path = self._get_product_path(product_slug) / "specs"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def _get_generated_path(self, product_slug: str) -> Path:
        """Get the generated images directory for a product."""
        now = datetime.now()
        path = self._get_product_path(product_slug) / "generated" / str(now.year) / f"{now.month:02d}"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def _generate_filename(self, original_filename: str, prefix: str = "") -> str:
        """Generate a unique filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = Path(original_filename).suffix
        hash_part = hashlib.md5(f"{original_filename}{timestamp}".encode()).hexdigest()[:8]
        
        if prefix:
            return f"{prefix}_{timestamp}_{hash_part}{ext}"
        return f"{timestamp}_{hash_part}{ext}"
    
    def save_reference_image(
        self,
        product_slug: str,
        file: BinaryIO,
        original_filename: str
    ) -> tuple[str, str]:
        """
        Save a reference image.
        
        Returns:
            tuple: (filename, storage_path)
        """
        refs_path = self._get_refs_path(product_slug)
        filename = self._generate_filename(original_filename, prefix="ref")
        storage_path = refs_path / filename
        
        with open(storage_path, "wb") as f:
            shutil.copyfileobj(file, f)
        
        # Return relative path for storage
        relative_path = str(storage_path.relative_to(self.local_root))
        return filename, relative_path
    
    def save_specification(
        self,
        product_slug: str,
        yaml_content: str,
        version: int
    ) -> str:
        """
        Save a YAML specification file.
        
        Returns:
            str: storage_path
        """
        specs_path = self._get_specs_path(product_slug)
        filename = f"v{version}.yaml"
        storage_path = specs_path / filename
        
        with open(storage_path, "w") as f:
            f.write(yaml_content)
        
        relative_path = str(storage_path.relative_to(self.local_root))
        return relative_path

    def save_generated_image(
        self,
        product_slug: str,
        file: BinaryIO,
        original_filename: str
    ) -> tuple[str, str]:
        """
        Save a generated image.
        
        Returns:
            tuple: (filename, storage_path)
        """
        gen_path = self._get_generated_path(product_slug)
        filename = self._generate_filename(original_filename, prefix="gen")
        storage_path = gen_path / filename
        
        with open(storage_path, "wb") as f:
            shutil.copyfileobj(file, f)
        
        relative_path = str(storage_path.relative_to(self.local_root))
        return filename, relative_path
    
    def get_absolute_path(self, relative_path: str) -> Path:
        """
        Get the absolute filesystem path for a stored file.
        Use this for internal operations (Analysis, Generation) that need file access.
        """
        return self.local_root / relative_path

    def get_file_path(self, relative_path: str) -> Path:
        """Legacy alias for get_absolute_path."""
        return self.get_absolute_path(relative_path)
    
    def delete_file(self, storage_path: str) -> bool:
        """Delete a file from storage."""
        try:
            file_path = self.get_absolute_path(storage_path)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def get_public_url(self, storage_path: str) -> str:
        """Get the URL to access a file."""
        # For local storage, return the API endpoint
        return f"/api/files/{storage_path}"



# Singleton instance
storage_service = StorageService()
