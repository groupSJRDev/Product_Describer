"""Product and related models."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    TIMESTAMP,
    ForeignKey,
    DECIMAL,
    CheckConstraint,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base
from backend.services.storage import storage_service


class Product(Base):
    """Product model."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    product_category = Column(String(100), nullable=True)
    tags = Column(ARRAY(String), nullable=True)

    # Relationships
    references = relationship("ProductReferenceImage", back_populates="product", cascade="all, delete-orphan")
    specifications = relationship("ProductSpecification", back_populates="product", cascade="all, delete-orphan")
    generations = relationship("GenerationRequest", back_populates="product")

    __table_args__ = (
        CheckConstraint("slug ~ '^[a-z0-9_-]+$'", name="products_slug_format"),
    )

    def __repr__(self):
        return f"<Product(id={self.id}, slug='{self.slug}')>"


class ProductReferenceImage(Base):
    """Product reference image model."""

    __tablename__ = "product_reference_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(50), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="references")

    @property
    def url(self) -> str:
        return storage_service.get_public_url(self.storage_path)

    def __repr__(self):
        return f"<ProductReferenceImage(id={self.id}, filename='{self.filename}')>"


class ProductSpecification(Base):
    """Product specification (YAML) model with versioning."""

    __tablename__ = "product_specifications"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    yaml_content = Column(Text, nullable=False)
    template_version = Column(String(20), default="1.0", nullable=True)
    
    # Analysis metadata
    confidence_overall = Column(DECIMAL(3, 2), nullable=True)  # 0.00 to 1.00
    image_count = Column(Integer, nullable=True)
    analysis_model = Column(String(100), default="gpt-5.2-2025-12-11", nullable=True)
    
    # Versioning
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    change_notes = Column(Text, nullable=True)
    
    # Derived from YAML for quick access
    primary_dimensions = Column(JSONB, nullable=True)  # {width: 215.9, height: 260.35, depth: 35.0, unit: "mm"}
    primary_colors = Column(JSONB, nullable=True)     # [{hex: "#CFE7EE", name: "pale icy blue"}, ...]
    material_type = Column(String(255), nullable=True)

    # Relationships
    product = relationship("Product", back_populates="specifications")

    def __repr__(self):
        return f"<ProductSpecification(id={self.id}, product_id={self.product_id}, version={self.version})>"
