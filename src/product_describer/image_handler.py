"""Image handling utilities."""

import base64
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from product_describer.constants import SUPPORTED_IMAGE_FORMATS, WARN_IMAGE_SIZE_MB
from product_describer.exceptions import ImageValidationError


class ImageHandler:
    """Handle image operations for product analysis."""

    def __init__(self, data_dir: Path) -> None:
        """Initialize image handler.

        Args:
            data_dir: Directory containing product images.
        """
        self.data_dir = data_dir

    def get_image_files(self) -> List[Path]:
        """Get all supported image files from the data directory.

        Returns:
            List of Path objects for image files, sorted by name.
        """
        image_files = []
        for ext in SUPPORTED_IMAGE_FORMATS:
            image_files.extend(self.data_dir.glob(f"*{ext}"))
            image_files.extend(self.data_dir.glob(f"*{ext.upper()}"))

        return sorted(image_files)

    def encode_image_to_base64(self, image_path: Path) -> str:
        """Encode an image file to base64 string.

        Args:
            image_path: Path to the image file.

        Returns:
            Base64 encoded string of the image.
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def get_image_info(self, image_path: Path) -> Dict[str, any]:
        """Get basic information about an image.

        Args:
            image_path: Path to the image file.

        Returns:
            Dictionary with image information (size, format, etc.).
        """
        with Image.open(image_path) as img:
            return {
                "filename": image_path.name,
                "format": img.format,
                "size": img.size,
                "mode": img.mode,
            }

    def validate_images(self) -> Tuple[List[Path], List[str]]:
        """Validate all images in the data directory.

        Returns:
            Tuple of (valid_image_paths, error_messages).
        """
        image_files = self.get_image_files()
        valid_images = []
        errors = []

        if not image_files:
            errors.append(f"No images found in {self.data_dir}")
            return valid_images, errors

        for image_path in image_files:
            try:
                with Image.open(image_path) as img:
                    img.verify()
                valid_images.append(image_path)
            except Exception as e:
                errors.append(f"Invalid image {image_path.name}: {e}")

        return valid_images, errors
