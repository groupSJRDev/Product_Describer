# Backend Database Architecture Plan

**Date**: 2026-01-27  
**Branch**: planning/front_end-012726  
**Status**: Planning Phase

## Overview

Design a FastAPI backend with PostgreSQL database to support Product Describer web application. Modeled after the VML Brand-Based Image Generation system but adapted for product-centric workflows.

---

## Database Schema Design

### Core Tables

#### 1. **users**
User authentication and authorization.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default admin user
INSERT INTO users (username, hashed_password, email) 
VALUES ('admin', '$hashed_admin123', 'admin@productdescriber.local');
```

**Notes:**
- Password hashing using bcrypt
- JWT token-based authentication
- Simple role system (can expand later)

---

#### 2. **products**
Core product entities (analogous to "brands" in VML system).

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    product_category VARCHAR(100),
    tags TEXT[], -- PostgreSQL array for tags
    
    CONSTRAINT products_slug_format CHECK (slug ~ '^[a-z0-9_-]+$')
);

CREATE INDEX idx_products_slug ON products(slug);
CREATE INDEX idx_products_created_by ON products(created_by);
```

**Fields:**
- `slug`: URL-friendly identifier (e.g., "stasher_half_gallon")
- `product_category`: Optional categorization
- `tags`: Searchable keywords

---

#### 3. **product_reference_images**
Reference images uploaded for each product (analogous to "brand assets").

```sql
CREATE TABLE product_reference_images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    file_size_bytes INTEGER,
    mime_type VARCHAR(50),
    width INTEGER,
    height INTEGER,
    uploaded_by INTEGER REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_primary BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,
    
    CONSTRAINT unique_product_primary 
        EXCLUDE (product_id WITH =) WHERE (is_primary = TRUE)
);

CREATE INDEX idx_ref_images_product ON product_reference_images(product_id);
CREATE INDEX idx_ref_images_primary ON product_reference_images(product_id, is_primary);
```

**Notes:**
- One primary image per product (used as main reference)
- Multiple reference images for multi-angle analysis
- Storage path supports local or S3

---

#### 4. **product_specifications**
YAML specifications generated from GPT Vision analysis (analogous to "style guides").

```sql
CREATE TABLE product_specifications (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    yaml_content TEXT NOT NULL,
    template_version VARCHAR(20) DEFAULT '1.0',
    
    -- Analysis metadata
    confidence_overall DECIMAL(3,2), -- 0.00 to 1.00
    image_count INTEGER,
    analysis_model VARCHAR(100) DEFAULT 'gpt-5.2-2025-12-11',
    
    -- Versioning
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_notes TEXT,
    
    -- Derived from YAML for quick access
    primary_dimensions JSONB, -- {width: 215.9, height: 260.35, depth: 35.0, unit: "mm"}
    primary_colors JSONB,     -- [{hex: "#CFE7EE", name: "pale icy blue"}, ...]
    material_type VARCHAR(255),
    
    CONSTRAINT unique_product_version UNIQUE (product_id, version),
    CONSTRAINT only_one_active 
        EXCLUDE (product_id WITH =) WHERE (is_active = TRUE)
);

CREATE INDEX idx_specs_product ON product_specifications(product_id);
CREATE INDEX idx_specs_active ON product_specifications(product_id, is_active);
CREATE INDEX idx_specs_version ON product_specifications(product_id, version DESC);
```

**Features:**
- **Version Control**: Track all spec iterations
- **Active Flag**: Only one active spec per product
- **JSONB Fields**: Quick queries without parsing YAML
- **Change Notes**: Document what changed in each version

**Workflow:**
1. Upload images → analyze → create spec v1 (active=true)
2. User edits YAML → create spec v2 (v1 becomes inactive, v2 active)
3. Revert to v1 → set v1 active, v2 inactive
4. History preserved forever

---

#### 5. **generation_requests**
Image generation jobs (like VML's generations).

```sql
CREATE TABLE generation_requests (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    specification_id INTEGER REFERENCES product_specifications(id),
    
    -- Generation parameters
    prompt TEXT NOT NULL,
    custom_prompt_override TEXT, -- User's creative direction
    aspect_ratio VARCHAR(20) DEFAULT '1:1',
    resolution VARCHAR(20) DEFAULT '2K',
    image_count INTEGER DEFAULT 1,
    model VARCHAR(100) DEFAULT 'gemini-3-pro-image-preview',
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    
    -- Metadata
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

CREATE INDEX idx_gen_requests_product ON generation_requests(product_id);
CREATE INDEX idx_gen_requests_status ON generation_requests(status);
CREATE INDEX idx_gen_requests_user ON generation_requests(created_by);
CREATE INDEX idx_gen_requests_created ON generation_requests(created_at DESC);
```

---

#### 6. **generated_images**
Output images from generation requests.

```sql
CREATE TABLE generated_images (
    id SERIAL PRIMARY KEY,
    generation_request_id INTEGER NOT NULL REFERENCES generation_requests(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    
    -- Image details
    filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    file_size_bytes INTEGER,
    mime_type VARCHAR(50) DEFAULT 'image/png',
    width INTEGER,
    height INTEGER,
    
    -- Generation metadata
    generation_index INTEGER, -- 1, 2, 3 if count > 1
    model_response_text TEXT, -- Any text response from model
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_gen_index 
        UNIQUE (generation_request_id, generation_index)
);

CREATE INDEX idx_gen_images_request ON generated_images(generation_request_id);
CREATE INDEX idx_gen_images_product ON generated_images(product_id);
CREATE INDEX idx_gen_images_created ON generated_images(created_at DESC);
```

---

## Storage Strategy

Following VML pattern with configurable storage:

```python
# settings.py
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")  # 'local' or 's3'
STORAGE_LOCAL_ROOT = os.getenv("STORAGE_LOCAL_ROOT", "local_storage")
STORAGE_BUCKET_NAME = os.getenv("STORAGE_BUCKET_NAME", "")

# Path structure:
# local_storage/
#   └── {product_slug}/
#       ├── refs/              # Reference images
#       │   └── original_1.jpg
#       ├── specs/             # YAML files (backup)
#       │   ├── v1.yaml
#       │   └── v2.yaml
#       └── generated/         # Generated images
#           └── {year}/{month}/
#               └── {timestamp}_{hash}.png
```

---

## API Endpoints Design

### Authentication
```
POST   /api/auth/login           # JWT token
POST   /api/auth/register        # Create user (admin only)
GET    /api/auth/me             # Current user info
```

### Products
```
GET    /api/products            # List all products
POST   /api/products            # Create product
GET    /api/products/{id}       # Get product details
PUT    /api/products/{id}       # Update product
DELETE /api/products/{id}       # Delete product

POST   /api/products/{id}/upload-references  # Upload reference images
GET    /api/products/{id}/references          # List references
DELETE /api/products/{id}/references/{ref_id} # Delete reference
```

### Product Analysis (GPT Vision)
```
POST   /api/products/{id}/analyze   # Run GPT analysis on refs
    Request: { template_version: "1.0", use_template: true }
    Response: { specification_id: 123, yaml_content: "...", confidence: 0.78 }
```

### Specifications
```
GET    /api/products/{id}/specifications           # List all versions
GET    /api/products/{id}/specifications/active    # Get active spec
GET    /api/products/{id}/specifications/{version} # Get specific version
PUT    /api/products/{id}/specifications/{id}      # Update spec (creates new version)
POST   /api/products/{id}/specifications/{id}/activate  # Set as active
```

### Image Generation
```
POST   /api/products/{id}/generate  # Create generation request
    Request: {
        prompt: "Product on marble table",
        aspect_ratio: "16:9",
        count: 3,
        specification_id: 123  # optional, uses active if null
    }
    Response: { request_id: 456, status: "pending" }

GET    /api/generation-requests/{id}           # Check status
GET    /api/generation-requests/{id}/images    # Get generated images
GET    /api/products/{id}/generations          # List all generations
```

### Gallery
```
GET    /api/products/{id}/gallery   # All generated images for product
    Query params: ?page=1&limit=20&sort=created_at
```

---

## Data Models (SQLAlchemy)

```python
# models.py
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey, DECIMAL, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP)
    
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey('users.id'))
    product_category = Column(String(100))
    tags = Column(ARRAY(String))
    
    # Relationships
    references = relationship("ProductReferenceImage", back_populates="product")
    specifications = relationship("ProductSpecification", back_populates="product")
    generations = relationship("GenerationRequest", back_populates="product")
    
class ProductReferenceImage(Base):
    __tablename__ = "product_reference_images"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    is_primary = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    
    product = relationship("Product", back_populates="references")
    
class ProductSpecification(Base):
    __tablename__ = "product_specifications"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    version = Column(Integer, nullable=False)
    yaml_content = Column(Text, nullable=False)
    template_version = Column(String(20), default='1.0')
    confidence_overall = Column(DECIMAL(3,2))
    is_active = Column(Boolean, default=True)
    primary_dimensions = Column(JSONB)
    primary_colors = Column(JSONB)
    material_type = Column(String(255))
    change_notes = Column(Text)
    
    product = relationship("Product", back_populates="specifications")
    
class GenerationRequest(Base):
    __tablename__ = "generation_requests"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    specification_id = Column(Integer, ForeignKey('product_specifications.id'))
    prompt = Column(Text, nullable=False)
    aspect_ratio = Column(String(20), default='1:1')
    image_count = Column(Integer, default=1)
    status = Column(String(50), default='pending')
    
    product = relationship("Product", back_populates="generations")
    specification = relationship("ProductSpecification")
    images = relationship("GeneratedImage", back_populates="request")
    
class GeneratedImage(Base):
    __tablename__ = "generated_images"
    id = Column(Integer, primary_key=True)
    generation_request_id = Column(Integer, ForeignKey('generation_requests.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    generation_index = Column(Integer)
    
    request = relationship("GenerationRequest", back_populates="images")
```

---

## Migration Strategy

### Phase 1: Database Setup
1. Create PostgreSQL database: `product_describer_db`
2. Initialize Alembic for migrations
3. Create base tables (users, products)
4. Seed admin user

### Phase 2: Core Tables
1. Add product_reference_images
2. Add product_specifications with versioning
3. Test YAML storage and retrieval

### Phase 3: Generation System
1. Add generation_requests
2. Add generated_images
3. Integrate with existing generate_test.py

### Phase 4: Optimization
1. Add indexes for performance
2. Implement JSONB queries for specs
3. Add full-text search on products

---

## Integration with Existing Code

### Adapt Current Workflow

**Current (CLI)**:
```python
# main.py: Analyze images → save YAML to temp/
# generate_test.py: Load YAML → generate images
```

**New (API-backed)**:
```python
# API receives upload → save to product_reference_images
# API calls gpt_analyzer.py → save to product_specifications
# API calls generate_test.py → save to generated_images
```

### Service Layer Structure

```python
# services/product_service.py
class ProductService:
    def create_product(name, slug, user_id)
    def get_product_by_slug(slug)
    def list_products(user_id)
    
# services/analysis_service.py
class AnalysisService:
    def analyze_product_images(product_id, use_template=True)
        # Calls existing gpt_analyzer.GPTAnalyzer
        # Saves result to product_specifications
    
# services/generation_service.py
class GenerationService:
    def create_generation_request(product_id, prompt, params)
    def process_generation(request_id)
        # Calls existing generate_test.generate_image_from_specs
        # Saves images to generated_images
```

---

## Authentication & Security

```python
# auth.py
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
```

**Default Credentials**:
- Username: `admin`
- Password: `admin123`
- Hash stored in database on seed

---

## Environment Configuration

```env
# .env
DATABASE_URL=postgresql://pd_user:pd_password@localhost:5432/product_describer_db
SECRET_KEY=your-secret-key-from-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Storage
STORAGE_TYPE=local
STORAGE_LOCAL_ROOT=local_storage
MAX_UPLOAD_SIZE_BYTES=10485760

# API Keys (existing)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
```

---

## Next Steps

1. ✅ **This Document**: Database schema planning
2. ⏳ **Frontend Planning**: UI/UX design document
3. ⏳ **Implementation**: 
   - Set up FastAPI project structure
   - Create database models
   - Implement authentication
   - Build API endpoints
   - Integrate existing analyzer/generator code

---

## Success Metrics

- [ ] User can create product via API
- [ ] User can upload reference images
- [ ] User can trigger GPT analysis via API
- [ ] YAML specifications saved with versioning
- [ ] User can generate images via API
- [ ] Generated images stored and retrievable
- [ ] Authentication works (JWT tokens)
- [ ] Frontend can consume all API endpoints
