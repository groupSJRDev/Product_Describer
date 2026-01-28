"""Generation request and image models."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    TIMESTAMP,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base


class GenerationRequest(Base):
    """Image generation request model."""

    __tablename__ = "generation_requests"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    specification_id = Column(
        Integer, ForeignKey("product_specifications.id"), nullable=True
    )

    # Generation parameters
    prompt = Column(Text, nullable=False)
    custom_prompt_override = Column(Text, nullable=True)
    aspect_ratio = Column(String(20), default="1:1", nullable=True)
    resolution = Column(String(20), default="2K", nullable=True)
    image_count = Column(Integer, default=1, nullable=False)
    model = Column(String(100), default="gemini-3-pro-image-preview", nullable=True)

    # Status tracking
    status = Column(String(50), default="pending", nullable=False, index=True)
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    product = relationship("Product", back_populates="generations")
    specification = relationship("ProductSpecification")
    images = relationship(
        "GeneratedImage", back_populates="request", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="valid_status",
        ),
    )

    def __repr__(self):
        return f"<GenerationRequest(id={self.id}, product_id={self.product_id}, status='{self.status}')>"


class GeneratedImage(Base):
    """Generated image model."""

    __tablename__ = "generated_images"

    id = Column(Integer, primary_key=True, index=True)
    generation_request_id = Column(
        Integer,
        ForeignKey("generation_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)

    # Image details
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(50), default="image/png", nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    # Generation metadata
    generation_index = Column(Integer, nullable=True)
    model_response_text = Column(Text, nullable=True)

    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    request = relationship("GenerationRequest", back_populates="images")

    def __repr__(self):
        return f"<GeneratedImage(id={self.id}, filename='{self.filename}')>"
