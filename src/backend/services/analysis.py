"""Analysis service for GPT Vision product analysis."""

import os
import yaml
from pathlib import Path
from typing import Optional, List
from sqlalchemy.orm import Session

from backend.models import Product, ProductReferenceImage, ProductSpecification
from backend.services.storage import storage_service
from backend.config import OPENAI_API_KEY
from product_describer.gpt_analyzer import GPTAnalyzer


class AnalysisService:
    """Service for analyzing products using GPT Vision."""

    def __init__(self):
        self.analyzer = GPTAnalyzer(api_key=OPENAI_API_KEY)

    def analyze_product(
        self,
        product: Product,
        reference_images: List[ProductReferenceImage],
        db: Session,
        use_template: bool = True,
    ) -> ProductSpecification:
        """
        Analyze a product using GPT Vision and create a specification.

        Args:
            product: The product to analyze
            reference_images: List of reference images
            db: Database session
            use_template: Whether to use template-based analysis

        Returns:
            ProductSpecification: The created specification
        """
        if not reference_images:
            raise ValueError("No reference images provided for analysis")

        # Get full paths to reference images
        image_paths = [
            storage_service.get_file_path(img.storage_path) for img in reference_images
        ]

        # Run GPT analysis
        parsed_yaml = self.analyzer.analyze_product(
            image_paths, product_name=product.name
        )

        # Convert to string for storage
        yaml_content = yaml.dump(parsed_yaml, sort_keys=False)

        # Extract key information
        confidence = parsed_yaml.get("metadata", {}).get("confidence_overall")

        # Extract dimensions
        dimensions = parsed_yaml.get("dimensions", {}).get("primary", {})
        primary_dimensions = None
        if dimensions:
            primary_dimensions = {
                "width": dimensions.get("width", {}).get("value"),
                "height": dimensions.get("height", {}).get("value"),
                "depth": dimensions.get("depth", {}).get("value"),
                "unit": dimensions.get("width", {}).get("unit", "mm"),
            }

        # Extract colors
        colors = parsed_yaml.get("colors", {}).get("primary", {})
        primary_colors = None
        if colors:
            primary_colors = [{"hex": colors.get("hex"), "name": colors.get("name")}]

        # Extract material
        material = parsed_yaml.get("materials", {}).get("primary_material", {})
        material_type = material.get("type") if material else None

        # Get current max version for this product
        max_version = (
            db.query(ProductSpecification)
            .filter(ProductSpecification.product_id == product.id)
            .count()
        )

        # Deactivate previous active spec
        db.query(ProductSpecification).filter(
            ProductSpecification.product_id == product.id,
            ProductSpecification.is_active == True,
        ).update({"is_active": False})

        # Create new specification
        spec = ProductSpecification(
            product_id=product.id,
            version=max_version + 1,
            yaml_content=yaml_content,
            template_version="1.0" if use_template else None,
            confidence_overall=confidence,
            image_count=len(reference_images),
            analysis_model=self.analyzer.model,
            is_active=True,
            primary_dimensions=primary_dimensions,
            primary_colors=primary_colors,
            material_type=material_type,
        )

        db.add(spec)
        db.commit()
        db.refresh(spec)

        # Save YAML to storage
        storage_service.save_specification(product.slug, yaml_content, spec.version)

        return spec

    def update_specification(
        self,
        spec: ProductSpecification,
        yaml_content: str,
        change_notes: Optional[str],
        db: Session,
    ) -> ProductSpecification:
        """
        Update a specification by creating a new version.

        Args:
            spec: The current specification
            yaml_content: Updated YAML content
            change_notes: Notes about what changed
            db: Database session

        Returns:
            ProductSpecification: The new specification version
        """
        # Parse updated YAML
        parsed_yaml = yaml.safe_load(yaml_content)

        # Extract metadata (similar to analyze_product)
        confidence = parsed_yaml.get("metadata", {}).get("confidence_overall")

        dimensions = parsed_yaml.get("dimensions", {}).get("primary", {})
        primary_dimensions = None
        if dimensions:
            primary_dimensions = {
                "width": dimensions.get("width", {}).get("value"),
                "height": dimensions.get("height", {}).get("value"),
                "depth": dimensions.get("depth", {}).get("value"),
                "unit": dimensions.get("width", {}).get("unit", "mm"),
            }

        colors = parsed_yaml.get("colors", {}).get("primary", {})
        primary_colors = None
        if colors:
            primary_colors = [{"hex": colors.get("hex"), "name": colors.get("name")}]

        material = parsed_yaml.get("materials", {}).get("primary_material", {})
        material_type = material.get("type") if material else None

        # Deactivate current spec
        spec.is_active = False

        # Create new version
        new_spec = ProductSpecification(
            product_id=spec.product_id,
            version=spec.version + 1,
            yaml_content=yaml_content,
            template_version=spec.template_version,
            confidence_overall=confidence,
            image_count=spec.image_count,
            analysis_model=spec.analysis_model,
            is_active=True,
            change_notes=change_notes,
            primary_dimensions=primary_dimensions,
            primary_colors=primary_colors,
            material_type=material_type,
        )

        db.add(new_spec)
        db.commit()
        db.refresh(new_spec)

        # Get product to save YAML
        product = db.query(Product).filter(Product.id == spec.product_id).first()
        storage_service.save_specification(product.slug, yaml_content, new_spec.version)

        return new_spec


# Singleton instance
analysis_service = AnalysisService()
