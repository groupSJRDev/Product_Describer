"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ===== Auth Schemas =====
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# ===== User Schemas =====
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Product Schemas =====
class ProductBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    product_category: Optional[str] = None
    tags: Optional[List[str]] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    product_category: Optional[str] = None
    tags: Optional[List[str]] = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# ===== Reference Image Schemas =====
class ReferenceImageResponse(BaseModel):
    id: int
    product_id: int
    filename: str
    storage_path: str
    file_size_bytes: Optional[int]
    mime_type: Optional[str]
    width: Optional[int]
    height: Optional[int]
    is_primary: bool
    display_order: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ===== Specification Schemas =====
class SpecificationResponse(BaseModel):
    id: int
    product_id: int
    version: int
    yaml_content: str
    template_version: Optional[str]
    confidence_overall: Optional[float]
    image_count: Optional[int]
    analysis_model: Optional[str]
    is_active: bool
    created_at: datetime
    change_notes: Optional[str]
    primary_dimensions: Optional[dict]
    primary_colors: Optional[List[dict]]
    material_type: Optional[str]

    class Config:
        from_attributes = True


class SpecificationUpdate(BaseModel):
    yaml_content: str
    change_notes: Optional[str] = None


# ===== Generation Schemas =====
class GenerationRequest(BaseModel):
    prompt: str
    custom_prompt_override: Optional[str] = None
    aspect_ratio: str = "1:1"
    resolution: str = "2K"
    image_count: int = Field(default=1, ge=1, le=10)
    specification_id: Optional[int] = None


class GeneratedImageResponse(BaseModel):
    id: int
    generation_request_id: int
    product_id: int
    filename: str
    storage_path: str
    file_size_bytes: Optional[int]
    width: Optional[int]
    height: Optional[int]
    generation_index: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class GenerationResponse(BaseModel):
    id: int
    product_id: int
    specification_id: Optional[int]
    prompt: str
    aspect_ratio: str
    image_count: int
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    generated_images: List[GeneratedImageResponse] = Field(default=[], alias="images")

    class Config:
        from_attributes = True
        populate_by_name = True
