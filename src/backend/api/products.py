"""Product API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from PIL import Image
import io

from backend.database import get_db
from backend.models import User, Product, ProductReferenceImage
from backend.api.schemas import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    ReferenceImageResponse,
    SpecificationResponse,
    SpecificationCreate,
    SpecificationListResponse,
)
from backend.api.dependencies import get_current_user
from backend.services.storage import storage_service
from backend.services.product import product_service
from backend.services.specification import specification_service
from backend.services.reference_image import reference_image_service
from backend.utils.images import validate_and_process_image

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new product."""
    return product_service.create_product(db, product, current_user.id)


@router.get("", response_model=List[ProductResponse])
def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all products."""
    return product_service.list_products(db, skip, limit)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get product by ID."""
    return product_service.get_product(db, product_id)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update product."""
    return product_service.update_product(db, product_id, product_update)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete product (soft delete)."""
    product_service.delete_product(db, product_id)


# ===== Specification Endpoints =====


@router.get("/{product_id}/specifications", response_model=List[SpecificationListResponse])
def list_specifications(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all specification versions for a product."""
    specs = specification_service.get_specifications(db, product_id)
    
    # Add preview for list view
    response = []
    for spec in specs:
        spec_dict = {
            "id": spec.id,
            "product_id": spec.product_id,
            "version": spec.version,
            "is_active": spec.is_active,
            "created_at": spec.created_at,
            "change_notes": spec.change_notes,
            "yaml_preview": spec.yaml_content[:200] + "..." if len(spec.yaml_content) > 200 else spec.yaml_content,
        }
        response.append(spec_dict)
    
    return response


@router.get("/{product_id}/specifications/{spec_id}", response_model=SpecificationResponse)
def get_specification(
    product_id: int,
    spec_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific specification version with full YAML content."""
    return specification_service.get_specification(db, product_id, spec_id)


@router.post("/{product_id}/specifications", response_model=SpecificationResponse, status_code=status.HTTP_201_CREATED)
def create_specification(
    product_id: int,
    spec_data: SpecificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new specification version."""
    return specification_service.create_specification(
        db,
        product_id,
        spec_data.yaml_content,
        current_user.id,
        spec_data.change_notes,
    )


@router.put("/{product_id}/specifications/{spec_id}/activate", response_model=SpecificationResponse)
def activate_specification(
    product_id: int,
    spec_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate a specification version (rollback to previous version)."""
    return specification_service.activate_specification(db, spec_id)


# ===== Reference Image Endpoints =====


@router.get("/{product_id}/reference-images", response_model=List[ReferenceImageResponse])
def list_reference_images(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all reference images for a product."""
    return reference_image_service.get_reference_images(db, product_id)


@router.post("/{product_id}/reference-images", response_model=ReferenceImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_reference_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a reference image for a product (max 4 total)."""
    return reference_image_service.upload_reference_image(
        db, product_id, file, current_user.id
    )


@router.delete("/{product_id}/reference-images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reference_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a reference image."""
    reference_image_service.delete_reference_image(db, image_id)


@router.put("/{product_id}/reference-images/{image_id}/order", response_model=ReferenceImageResponse)
def update_reference_image_order(
    product_id: int,
    image_id: int,
    order: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the display order of a reference image."""
    return reference_image_service.update_display_order(db, image_id, order)


# ===== Legacy Reference Image Endpoints (deprecated) =====


@router.post(
    "/{product_id}/upload-references", response_model=List[ReferenceImageResponse]
)
async def upload_reference_images(
    product_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload reference images for a product."""
    product = product_service.get_product(db, product_id)

    uploaded_images = []

    for file in files:
        # Process image using helper
        file_obj, filename, width, height = validate_and_process_image(file)

        # Save to storage
        saved_filename, storage_path = storage_service.save_reference_image(
            product.slug, file_obj, filename
        )

        # Create database record

        ref_image = ProductReferenceImage(
            product_id=product_id,
            filename=filename,
            storage_path=storage_path,
            file_size_bytes=len(content),
            mime_type=file.content_type,
            width=width,
            height=height,
            uploaded_by=current_user.id,
            is_primary=(existing_count == 0 and idx == 0),  # First image is primary
            display_order=existing_count + idx,
        )
        db.add(ref_image)
        uploaded_images.append(ref_image)

    db.commit()
    for img in uploaded_images:
        db.refresh(img)

    return uploaded_images


@router.get("/{product_id}/references", response_model=List[ReferenceImageResponse])
def list_reference_images(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all reference images for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    images = (
        db.query(ProductReferenceImage)
        .filter(ProductReferenceImage.product_id == product_id)
        .order_by(ProductReferenceImage.display_order)
        .all()
    )

    return images


@router.delete(
    "/{product_id}/references/{ref_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_reference_image(
    product_id: int,
    ref_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a reference image."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    ref_image = (
        db.query(ProductReferenceImage)
        .filter(
            ProductReferenceImage.id == ref_id,
            ProductReferenceImage.product_id == product_id,
        )
        .first()
    )

    if not ref_image:
        raise HTTPException(status_code=404, detail="Reference image not found")

    # Delete from storage
    storage_service.delete_file(ref_image.storage_path)

    # Delete from database
    db.delete(ref_image)
    db.commit()

    return None
    product.is_active = False
    db.commit()
    return None
