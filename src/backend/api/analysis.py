"""Analysis and Specification API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Product, ProductReferenceImage, ProductSpecification
from backend.api.schemas import SpecificationResponse, SpecificationUpdate
from backend.api.dependencies import get_current_user
from backend.services.analysis import analysis_service

router = APIRouter(tags=["Analysis & Specifications"])


# ===== Analysis Endpoint =====

@router.post("/products/{product_id}/analyze", response_model=SpecificationResponse)
def analyze_product(
    product_id: int,
    use_template: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze product images using GPT Vision and create a specification.
    
    This will:
    1. Get all reference images for the product
    2. Run GPT Vision analysis
    3. Create a new ProductSpecification with the YAML results
    4. Save the YAML to storage
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get reference images
    reference_images = db.query(ProductReferenceImage).filter(
        ProductReferenceImage.product_id == product_id
    ).all()
    
    if not reference_images:
        raise HTTPException(
            status_code=400,
            detail="No reference images found. Please upload images first."
        )
    
    try:
        spec = analysis_service.analyze_product(
            product=product,
            reference_images=reference_images,
            db=db,
            use_template=use_template
        )
        return spec
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


# ===== Specification Endpoints =====

@router.get("/products/{product_id}/specifications", response_model=List[SpecificationResponse])
def list_specifications(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all specification versions for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    specs = db.query(ProductSpecification).filter(
        ProductSpecification.product_id == product_id
    ).order_by(ProductSpecification.version.desc()).all()
    
    return specs


@router.get("/products/{product_id}/specifications/active", response_model=SpecificationResponse)
def get_active_specification(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the active specification for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    spec = db.query(ProductSpecification).filter(
        ProductSpecification.product_id == product_id,
        ProductSpecification.is_active == True
    ).first()
    
    if not spec:
        raise HTTPException(
            status_code=404,
            detail="No active specification found. Please analyze the product first."
        )
    
    return spec


@router.get("/products/{product_id}/specifications/{version}", response_model=SpecificationResponse)
def get_specification_by_version(
    product_id: int,
    version: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific specification version."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    spec = db.query(ProductSpecification).filter(
        ProductSpecification.product_id == product_id,
        ProductSpecification.version == version
    ).first()
    
    if not spec:
        raise HTTPException(status_code=404, detail="Specification version not found")
    
    return spec


@router.put("/specifications/{spec_id}", response_model=SpecificationResponse)
def update_specification(
    spec_id: int,
    spec_update: SpecificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a specification by creating a new version.
    
    This creates a new version with the updated YAML content,
    preserving the history of changes.
    """
    spec = db.query(ProductSpecification).filter(
        ProductSpecification.id == spec_id
    ).first()
    
    if not spec:
        raise HTTPException(status_code=404, detail="Specification not found")
    
    try:
        new_spec = analysis_service.update_specification(
            spec=spec,
            yaml_content=spec_update.yaml_content,
            change_notes=spec_update.change_notes,
            db=db
        )
        return new_spec
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Update failed: {str(e)}"
        )


@router.post("/specifications/{spec_id}/activate", response_model=SpecificationResponse)
def activate_specification(
    spec_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set a specification as the active version for its product."""
    spec = db.query(ProductSpecification).filter(
        ProductSpecification.id == spec_id
    ).first()
    
    if not spec:
        raise HTTPException(status_code=404, detail="Specification not found")
    
    # Deactivate all other versions for this product
    db.query(ProductSpecification).filter(
        ProductSpecification.product_id == spec.product_id,
        ProductSpecification.is_active == True
    ).update({"is_active": False})
    
    # Activate this version
    spec.is_active = True
    db.commit()
    db.refresh(spec)
    
    return spec
