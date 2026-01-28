"""Generation API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Product
from backend.models.generation import GenerationRequest, GeneratedImage
from backend.api.schemas import (
    GenerationRequest as GenerationRequestSchema,
    GenerationResponse,
    GeneratedImageResponse
)
from backend.api.dependencies import get_current_user
from backend.services.generation import generation_service
from backend.services.storage import storage_service

router = APIRouter(tags=["Image Generation"])


@router.post("/products/{product_id}/generate", response_model=GenerationResponse)
def create_generation(
    product_id: int,
    gen_request: GenerationRequestSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create an image generation request.
    
    The generation will be processed asynchronously in the background.
    Use the returned request_id to check status and retrieve images.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Create generation request
    request = generation_service.create_generation_request(
        product=product,
        prompt=gen_request.prompt,
        specification_id=gen_request.specification_id,
        aspect_ratio=gen_request.aspect_ratio,
        resolution=gen_request.resolution,
        image_count=gen_request.image_count,
        custom_prompt_override=gen_request.custom_prompt_override,
        user_id=current_user.id,
        db=db
    )
    
    # Process generation in background (pass ID only, not session)
    background_tasks.add_task(
        generation_service.process_generation,
        request.id
    )
    
    return request


@router.get("/generation-requests/{request_id}", response_model=GenerationResponse)
def get_generation_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the status and details of a generation request."""
    request = generation_service.get_generation_status(request_id, db)
    
    if not request:
        raise HTTPException(status_code=404, detail="Generation request not found")
    
    return request


@router.get("/generation-requests/{request_id}/images", response_model=List[GeneratedImageResponse])
def get_generation_images(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all images from a generation request."""
    request = generation_service.get_generation_status(request_id, db)
    
    if not request:
        raise HTTPException(status_code=404, detail="Generation request not found")
    
    images = generation_service.get_generated_images(request_id, db)
    return images


@router.get("/products/{product_id}/generations", response_model=List[GenerationResponse])
def list_product_generations(
    product_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all generation requests for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    requests = generation_service.get_product_generations(product_id, db, skip, limit)
    return requests


@router.get("/products/{product_id}/gallery", response_model=List[GeneratedImageResponse])
def get_product_gallery(
    product_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get gallery of all generated images for a product.
    
    Returns images sorted by creation date (newest first).
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    images = generation_service.get_product_gallery(product_id, db, skip, limit)
    return images


@router.delete("/generation-requests/{request_id}")
def delete_generation_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a generation request and all its associated images.
    
    This will:
    - Cancel the generation if it's still processing
    - Delete all generated image files from storage
    - Delete all database records for generated images
    - Delete the generation request record
    """
    request = db.query(GenerationRequest).filter(GenerationRequest.id == request_id).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Generation request not found")
    
    # If processing or pending, cancel it
    if request.status in ['pending', 'processing']:
        generation_service.cancel_generation(request_id)
    
    # Delete all associated images and their files
    images = db.query(GeneratedImage).filter(GeneratedImage.generation_request_id == request_id).all()
    for image in images:
        # Delete file from storage if it exists
        if image.storage_path:
            try:
                storage_service.delete_file(image.storage_path)
            except Exception as e:
                # Log but don't fail if file doesn't exist
                print(f"Warning: Could not delete file {image.storage_path}: {e}")
        
        # Delete database record
        db.delete(image)
    
    # Delete the generation request
    db.delete(request)
    db.commit()
    
    return {"message": "Generation request deleted successfully", "id": request_id}
