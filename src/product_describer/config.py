"""Configuration management for product describer."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self.product_name: Optional[str] = os.getenv("PRODUCT_NAME")
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.gpt_model: str = os.getenv("GPT_MODEL", "gpt-5.2-2025-12-11")
        
        # Base directories
        self.base_dir = Path.cwd()
        self.data_dir = self.base_dir / "data"
        self.temp_dir = self.base_dir / "temp"
    
    def get_product_data_dir(self) -> Path:
        """Get the directory containing product images.
        
        Returns:
            Path: Path to data/<PRODUCT_NAME> directory.
            
        Raises:
            ValueError: If PRODUCT_NAME is not set.
        """
        if not self.product_name:
            raise ValueError("PRODUCT_NAME environment variable is not set")
        return self.data_dir / self.product_name
    
    def get_product_output_dir(self) -> Path:
        """Get the directory for product output.
        
        Returns:
            Path: Path to temp/<PRODUCT_NAME> directory.
            
        Raises:
            ValueError: If PRODUCT_NAME is not set.
        """
        if not self.product_name:
            raise ValueError("PRODUCT_NAME environment variable is not set")
        return self.temp_dir / self.product_name
    
    def get_output_file_path(self) -> Path:
        """Get the full path to the output YAML file.
        
        Returns:
            Path: Path to temp/<PRODUCT_NAME>/description.yaml
        """
        return self.get_product_output_dir() / "description.yaml"
    
    def validate(self) -> None:
        """Validate configuration.
        
        Raises:
            ValueError: If required configuration is missing.
        """
        if not self.product_name:
            raise ValueError("PRODUCT_NAME environment variable is required")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Check if product data directory exists
        data_dir = self.get_product_data_dir()
        if not data_dir.exists():
            raise ValueError(
                f"Product data directory does not exist: {data_dir}\n"
                f"Please create it and add product images."
            )
