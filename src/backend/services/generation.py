"""Generation service for image generation using existing generate_test module."""

import yaml
import io
import tempfile
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from PIL import Image

from backend.models import (
    Product,
    ProductSpecification,
    ProductReferenceImage,
    GenerationRequest,
    GeneratedImage
)
from backend.services.storage import storage_service
from backend.config import GEMINI_API_KEY
from product_describer.generate_test import generate_image_from_specs


class GenerationService:
    """Service for generating images using Gemini."""
    
    def _generate_single_image(
        self,
        reference_image_path: str,
        yaml_specs: str,
        specs_dict: dict,
        custom_prompt: str,
        aspect_ratio: str,
        resolution: str
    ) -> bytes:
        """
        Generate a single image and return its bytes.
        
        Args:
            reference_image_path: Path to reference image
            yaml_specs: YAML specifications as string
            specs_dict: Parsed specifications dictionary
            custom_prompt: Custom generation prompt
            aspect_ratio: Image aspect ratio
            resolution: Image resolution
        
        Returns:
            bytes: Generated image data
        """
        # Create a temporary file for output
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
        
        try:
            # Call the existing generate function
            generate_image_from_specs(
                reference_image_path=Path(reference_image_path),
                yaml_specs=yaml_specs,
                specs_dict=specs_dict,
                custom_prompt=custom_prompt,
                output_path=tmp_path,
                api_key=GEMINI_API_KEY,
                aspect_ratio=aspect_ratio,
                resolution=resolution
            )
            
            # Read the generated image
            with open(tmp_path, "rb") as f:
                image_data = f.read()
            
            return image_data
            
        finally:
            # Clean up temporary file
            if tmp_path.exists():
                tmp_path.unlink()
    
    def create_generation_request(
        self,
        product: Product,
        prompt: str,
        specification_id: Optional[int],
        aspect_ratio: str,
        resolution: str,
        image_count: int,
        custom_prompt_override: Optional[str],
        user_id: int,
        db: Session
    ) -> GenerationRequest:
        """
        Create a new generation request.
        
        Args:
            product: The product to generate images for
            prompt: User's generation prompt
            specification_id: Optional specific spec version to use
            aspect_ratio: Image aspect ratio (1:1, 16:9, etc.)
            resolution: Image resolution (2K, 4K, etc.)
            image_count: Number of images to generate
            custom_prompt_override: Optional custom prompt text
            user_id: ID of user creating the request
            db: Database session
        
        Returns:
            GenerationRequest: The created request
        """
        # Create generation request
        gen_request = GenerationRequest(
            product_id=product.id,
            specification_id=specification_id,
            prompt=prompt,
            custom_prompt_override=custom_prompt_override,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            image_count=image_count,
            status="pending",
            created_by=user_id
        )
        
        db.add(gen_request)
        db.commit()
        db.refresh(gen_request)
        
        return gen_request
    
    def process_generation(
        self,
        request: GenerationRequest,
        db: Session
    ) -> List[GeneratedImage]:
        """
        Process a generation request and create images.
        
        Args:
            request: The generation request to process
            db: Database session
        
        Returns:
            List[GeneratedImage]: The generated images
        """
        try:
            # Update status to processing
            request.status = "processing"
            request.started_at = datetime.now()
            db.commit()
            
            # Get product and specification
            product = db.query(Product).filter(Product.id == request.product_id).first()
            
            if request.specification_id:
                spec = db.query(ProductSpecification).filter(
                    ProductSpecification.id == request.specification_id
                ).first()
            else:
                # Use active specification
                spec = db.query(ProductSpecification).filter(
                    ProductSpecification.product_id == request.product_id,
                    ProductSpecification.is_active == True
                ).first()
            
            if not spec:
                raise ValueError("No specification found for generation")
            
            # Parse YAML
            specs_dict = yaml.safe_load(spec.yaml_content)
            
            # Get a reference image to use for generation
            ref_images = db.query(ProductReferenceImage).filter(
                ProductReferenceImage.product_id == product.id
            ).order_by(ProductReferenceImage.is_primary.desc()).all()
            
            if not ref_images:
                raise ValueError("No reference images found for generation")
            
            # Use primary image or first one
            primary_ref = ref_images[0]
            ref_image_path = str(storage_service.get_file_path(primary_ref.storage_path))
            
            # Build full prompt (combine user prompt with spec-based prompt)
            full_prompt = request.custom_prompt_override if request.custom_prompt_override else request.prompt
            
            # Generate images
            generated_images = []
            
            for i in range(request.image_count):
                # Call wrapper function to generate image and get bytes
                image_data = self._generate_single_image(
                    reference_image_path=ref_image_path,
                    yaml_specs=spec.yaml_content,
                    specs_dict=specs_dict,
                    custom_prompt=full_prompt,
                    aspect_ratio=request.aspect_ratio,
                    resolution=request.resolution
                )
                
                if image_data:
                    # image_data is the raw bytes from the generation
                    image_bytes = io.BytesIO(image_data)
                    
                    # Save to storage
                    filename = f"gen_{request.id}_{i+1}.png"
                    saved_filename, storage_path = storage_service.save_generated_image(
                        product.slug,
                        image_bytes,
                        filename
                    )
                    
                    # Create database record
                    gen_image = GeneratedImage(
                        generation_request_id=request.id,
                        product_id=product.id,
                        filename=saved_filename,
                        storage_path=storage_path,
                        file_size_bytes=len(image_data),
                        mime_type="image/png",
                        generation_index=i + 1
                    )
                    
                    db.add(gen_image)
                    generated_images.append(gen_image)
            
            # Update request status
            request.status = "completed"
            request.completed_at = datetime.now()
            db.commit()
            
            for img in generated_images:
                db.refresh(img)
            
            return generated_images
            
        except Exception as e:
            # Update request with error
            request.status = "failed"
            request.error_message = str(e)
            request.completed_at = datetime.now()
            db.commit()
            raise
    
    def get_generation_status(
        self,
        request_id: int,
        db: Session
    ) -> Optional[GenerationRequest]:
        """Get the status of a generation request."""
        return db.query(GenerationRequest).filter(
            GenerationRequest.id == request_id
        ).first()
    
    def get_generated_images(
        self,
        request_id: int,
        db: Session
    ) -> List[GeneratedImage]:
        """Get all images from a generation request."""
        return db.query(GeneratedImage).filter(
            GeneratedImage.generation_request_id == request_id
        ).order_by(GeneratedImage.generation_index).all()
    
    def get_product_generations(
        self,
        product_id: int,
        db: Session,
        skip: int = 0,
        limit: int = 50
    ) -> List[GenerationRequest]:
        """Get all generation requests for a product."""
        return db.query(GenerationRequest).filter(
            GenerationRequest.product_id == product_id
        ).order_by(GenerationRequest.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_product_gallery(
        self,
        product_id: int,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[GeneratedImage]:
        """Get all generated images for a product (gallery view)."""
        return db.query(GeneratedImage).filter(
            GeneratedImage.product_id == product_id
        ).order_by(GeneratedImage.created_at.desc()).offset(skip).limit(limit).all()


# Singleton instance
generation_service = GenerationService()
