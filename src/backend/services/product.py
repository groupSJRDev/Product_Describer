from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from backend.models import Product, User
from backend.api.schemas import ProductCreate, ProductUpdate

class ProductService:
    def create_product(self, db: Session, product: ProductCreate, user_id: int) -> Product:
        # Check if slug already exists
        existing = db.query(Product).filter(Product.slug == product.slug).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with slug '{product.slug}' already exists"
            )
        
        db_product = Product(
            **product.model_dump(),
            created_by=user_id
        )
        db.add(db_product)
        try:
            db.commit()
            db.refresh(db_product)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error"
            )
        return db_product

    def list_products(self, db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
        return db.query(Product).filter(Product.is_active == True).offset(skip).limit(limit).all()

    def get_product(self, db: Session, product_id: int) -> Product:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    
    def get_product_by_slug(self, db: Session, slug: str) -> Product:
        product = db.query(Product).filter(Product.slug == slug).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product

    def update_product(self, db: Session, product_id: int, product_update: ProductUpdate) -> Product:
        product = self.get_product(db, product_id)
        
        update_data = product_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        db.commit()
        db.refresh(product)
        return product

    def delete_product(self, db: Session, product_id: int) -> None:
        product = self.get_product(db, product_id)
        # Soft delete is not implemented on model yet, maybe standard delete?
        # Model has is_active, so let's set it to False
        product.is_active = False 
        db.commit()

product_service = ProductService()
