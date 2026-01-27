"""Product API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from PIL import Image
import io

from backend.database import get_db
from backend.models import User, Product, ProductReferenceImage
from backend.api.schemas import ProductCreate, ProductResponse, ProductUpdate, ReferenceImageResponse
from backend.api.dependencies import get_current_user
from backend.services.storage import storage_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new product."""
    # Check if slug already exists
    existing = db.query(Product).filter(Product.slug == product.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with slug '{product.slug}' already exists"
        )
    
    db_product = Product(
        **product.model_dump(),
        created_by=current_user.id
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("", response_model=List[ProductResponse])
def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all products."""
    products = db.query(Product).filter(Product.is_active == True).offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete product (soft delete)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    


# ===== Reference Image Endpoints =====

@router.post("/{product_id}/upload-references", response_model=List[ReferenceImageResponse])
async def upload_reference_images(
    product_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload reference images for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Validate files
    allowed_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
    for file in files:
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Allowed: {allowed_types}"
            )
    
    uploaded_images = []
    existing_count = db.query(ProductReferenceImage).filter(
        ProductReferenceImage.product_id == product_id
    ).count()
    
    for idx, file in enumerate(files):
        # Read file
        content = await file.read()
        file_obj = io.BytesIO(content)
        
        # Get image dimensions
        try:
            img = Image.open(io.BytesIO(content))
            width, height = img.size
        except Exception:
            width, height = None, None
        
        # Save to storage
        filename, storage_path = storage_service.save_reference_image(
            product.slug,
            file_obj,
            file.filename
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
            display_order=existing_count + idx
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
    current_user: User = Depends(get_current_user)
):
    """List all reference images for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    images = db.query(ProductReferenceImage).filter(
        ProductReferenceImage.product_id == product_id
    ).order_by(ProductReferenceImage.display_order).all()
    
    return images


@router.delete("/{product_id}/references/{ref_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reference_image(
    product_id: int,
    ref_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a reference image."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    ref_image = db.query(ProductReferenceImage).filter(
        ProductReferenceImage.id == ref_id,
        ProductReferenceImage.product_id == product_id
    ).first()
    
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
