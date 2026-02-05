"""Specification service for managing product specifications."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status

from backend.models.product import ProductSpecification, Product
from backend.services.storage import storage_service


class SpecificationService:
    """Service for managing product specifications."""

    def get_specifications(
        self, db: Session, product_id: int
    ) -> List[ProductSpecification]:
        """Get all specification versions for a product."""
        # Verify product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        specs = (
            db.query(ProductSpecification)
            .filter(ProductSpecification.product_id == product_id)
            .order_by(desc(ProductSpecification.version))
            .all()
        )

        return specs

    def get_specification(
        self, db: Session, product_id: int, spec_id: int
    ) -> ProductSpecification:
        """Get a specific specification version."""
        spec = (
            db.query(ProductSpecification)
            .filter(
                ProductSpecification.id == spec_id,
                ProductSpecification.product_id == product_id,
            )
            .first()
        )

        if not spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Specification not found"
            )

        return spec

    def get_active_specification(
        self, db: Session, product_id: int
    ) -> Optional[ProductSpecification]:
        """Get the active specification for a product."""
        return (
            db.query(ProductSpecification)
            .filter(
                ProductSpecification.product_id == product_id,
                ProductSpecification.is_active == True,
            )
            .first()
        )

    def create_specification(
        self,
        db: Session,
        product_id: int,
        yaml_content: str,
        created_by: int,
        change_notes: Optional[str] = None,
    ) -> ProductSpecification:
        """Create a new specification version."""
        # Verify product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        # Get the highest version number for this product
        max_version_spec = (
            db.query(ProductSpecification)
            .filter(ProductSpecification.product_id == product_id)
            .order_by(desc(ProductSpecification.version))
            .first()
        )

        new_version = (max_version_spec.version + 1) if max_version_spec else 1

        # Deactivate all previous specifications
        db.query(ProductSpecification).filter(
            ProductSpecification.product_id == product_id
        ).update({"is_active": False})

        # Save YAML to local storage
        storage_path = storage_service.save_specification(
            product.slug, yaml_content, new_version
        )

        # Create new specification
        new_spec = ProductSpecification(
            product_id=product_id,
            version=new_version,
            yaml_content=yaml_content,
            is_active=True,
            created_by=created_by,
            change_notes=change_notes,
        )

        db.add(new_spec)
        db.commit()
        db.refresh(new_spec)

        return new_spec

    def activate_specification(self, db: Session, spec_id: int) -> ProductSpecification:
        """Activate a specific specification version (rollback)."""
        spec = (
            db.query(ProductSpecification)
            .filter(ProductSpecification.id == spec_id)
            .first()
        )

        if not spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Specification not found"
            )

        # Deactivate all specifications for this product
        db.query(ProductSpecification).filter(
            ProductSpecification.product_id == spec.product_id
        ).update({"is_active": False})

        # Activate the selected specification
        spec.is_active = True
        db.commit()
        db.refresh(spec)

        return spec


# Singleton instance
specification_service = SpecificationService()
