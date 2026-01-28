"""Reference image service for managing product reference images."""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status, UploadFile
from PIL import Image
import io
import uuid

from backend.models.product import ProductReferenceImage, Product
from backend.services.storage import storage_service


class ReferenceImageService:
    """Service for managing product reference images."""

    def get_reference_images(
        self, db: Session, product_id: int
    ) -> List[ProductReferenceImage]:
        """Get all reference images for a product."""
        # Verify product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        images = (
            db.query(ProductReferenceImage)
            .filter(ProductReferenceImage.product_id == product_id)
            .order_by(ProductReferenceImage.display_order)
            .all()
        )

        return images

    def upload_reference_image(
        self,
        db: Session,
        product_id: int,
        file: UploadFile,
        uploaded_by: int,
    ) -> ProductReferenceImage:
        """Upload a new reference image."""
        # Verify product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        # Check if we already have 4 images
        existing_count = (
            db.query(ProductReferenceImage)
            .filter(ProductReferenceImage.product_id == product_id)
            .count()
        )

        if existing_count >= 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum of 4 reference images allowed per product",
            )

        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image",
            )

        # Read file content
        content = file.file.read()
        file.file.seek(0)  # Reset for potential re-read

        # Get image dimensions
        try:
            image = Image.open(io.BytesIO(content))
            width, height = image.size
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image file: {str(e)}",
            )

        # Generate UUID-based filename
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"{uuid.uuid4().hex}.{ext}"

        # Save file to storage
        file.file.seek(0)
        filename, storage_path = storage_service.save_reference_image(
            product.slug, file.file, unique_filename
        )

        # Get next display order
        max_order = (
            db.query(ProductReferenceImage.display_order)
            .filter(ProductReferenceImage.product_id == product_id)
            .order_by(desc(ProductReferenceImage.display_order))
            .first()
        )
        next_order = (max_order[0] + 1) if max_order else 0

        # Create database record
        ref_image = ProductReferenceImage(
            product_id=product_id,
            filename=file.filename,
            storage_path=storage_path,
            file_size_bytes=len(content),
            mime_type=file.content_type,
            width=width,
            height=height,
            uploaded_by=uploaded_by,
            is_primary=(existing_count == 0),  # First image is primary
            display_order=next_order,
        )

        db.add(ref_image)
        db.commit()
        db.refresh(ref_image)

        return ref_image

    def delete_reference_image(self, db: Session, image_id: int) -> None:
        """Delete a reference image."""
        image = (
            db.query(ProductReferenceImage)
            .filter(ProductReferenceImage.id == image_id)
            .first()
        )

        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reference image not found",
            )

        # Delete file from storage
        storage_service.delete_file(image.storage_path)

        # Delete from database
        db.delete(image)
        db.commit()

    def update_display_order(
        self, db: Session, image_id: int, new_order: int
    ) -> ProductReferenceImage:
        """Update the display order of a reference image."""
        image = (
            db.query(ProductReferenceImage)
            .filter(ProductReferenceImage.id == image_id)
            .first()
        )

        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reference image not found",
            )

        image.display_order = new_order
        db.commit()
        db.refresh(image)

        return image


# Singleton instance
reference_image_service = ReferenceImageService()
