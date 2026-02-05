# Backend Database Architecture Plan

**Date**: 2026-01-27  
**Branch**: planning/front_end-012726  
**Status**: Planning Phase

## Overview

Design a FastAPI backend with PostgreSQL database to support Product Describer web application. Modeled after the VML Brand-Based Image Generation system but adapted for product-centric workflows.

---

## Database Schema Design

### Schema Overview

```mermaid
erDiagram
    users ||--o{ products : creates
    users ||--o{ product_reference_images : uploads
    users ||--o{ product_specifications : creates
    users ||--o{ generation_requests : initiates
    
    products ||--o{ product_reference_images : "has many"
    products ||--o{ product_specifications : "has many"
    products ||--o{ generation_requests : "has many"
    products ||--o{ generated_images : "has many"
    
    product_specifications ||--o{ generation_requests : "used by"
    generation_requests ||--o{ generated_images : "produces"
    
    users {
        int id PK
        string username UK
        string hashed_password
        string email UK
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }
    
    products {
        int id PK
        string name
        string slug UK
        text description
        int created_by FK
        timestamp created_at
        timestamp updated_at
        boolean is_active
        string product_category
        array tags
    }
    
    product_reference_images {
        int id PK
        int product_id FK
        string filename
        string storage_path
        int file_size_bytes
        string mime_type
        int width
        int height
        int uploaded_by FK
        timestamp uploaded_at
        boolean is_primary
        int display_order
    }
    
    product_specifications {
        int id PK
        int product_id FK
        int version
        text yaml_content
        string template_version
        decimal confidence_overall
        int image_count
        string analysis_model
        boolean is_active
        int created_by FK
        timestamp created_at
        text change_notes
        jsonb primary_dimensions
        jsonb primary_colors
        string material_type
    }
    
    generation_requests {
        int id PK
        int product_id FK
        int specification_id FK
        text prompt
        text custom_prompt_override
        string aspect_ratio
        string resolution
        int image_count
        string model
        string status
        timestamp started_at
        timestamp completed_at
        text error_message
        int created_by FK
        timestamp created_at
    }
    
    generated_images {
        int id PK
        int generation_request_id FK
        int product_id FK
        string filename
        string storage_path
        int file_size_bytes
        string mime_type
        int width
        int height
        int generation_index
        text model_response_text
        timestamp created_at
    }
```

> **📄 Detailed Schema Documentation**: See [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) for comprehensive entity diagrams, workflows, and query examples.

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

### Storage Architecture Diagram

```mermaid
graph TB
    subgraph "Local Storage Structure"
        ROOT[local_storage/]
        
        PRODUCT1[stasher_half_gallon/]
        PRODUCT2[stasher_4_cup_bag/]
        
        REFS1[refs/]
        SPECS1[specs/]
        GEN1[generated/]
        
        REF_IMG1[original_1.jpg]
        REF_IMG2[original_2.jpg]
        
        SPEC_V1[v1.yaml]
        SPEC_V2[v2.yaml]
        
        Y2026[2026/]
        M02[02/]
        IMG1[20260205_143022_abc123.png]
        IMG2[20260205_143045_def456.png]
        
        ROOT --> PRODUCT1
        ROOT --> PRODUCT2
        
        PRODUCT1 --> REFS1
        PRODUCT1 --> SPECS1
        PRODUCT1 --> GEN1
        
        REFS1 --> REF_IMG1
        REFS1 --> REF_IMG2
        
        SPECS1 --> SPEC_V1
        SPECS1 --> SPEC_V2
        
        GEN1 --> Y2026
        Y2026 --> M02
        M02 --> IMG1
        M02 --> IMG2
    end
    
    style ROOT fill:#e1f5ff
    style PRODUCT1 fill:#fff3e0
    style REFS1 fill:#f3e5f5
    style SPECS1 fill:#e8f5e9
    style GEN1 fill:#e1bee7
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

### Workflow Diagrams

#### Product Creation & Analysis Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant DB
    participant Storage
    participant GPT
    
    User->>API: POST /api/products
    API->>DB: INSERT INTO products
    DB-->>API: product_id
    API-->>User: Product created
    
    User->>API: POST /api/products/{id}/upload-references
    API->>Storage: Save image files
    Storage-->>API: storage_paths
    API->>DB: INSERT INTO product_reference_images
    DB-->>API: Success
    API-->>User: Images uploaded
    
    User->>API: POST /api/products/{id}/analyze
    API->>DB: SELECT images WHERE product_id
    DB-->>API: image_paths
    API->>GPT: Analyze images (GPT Vision)
    GPT-->>API: YAML specification
    API->>DB: INSERT INTO product_specifications (v1, is_active=true)
    DB-->>API: specification_id
    API-->>User: Analysis complete
```

#### Specification Version Control

```mermaid
stateDiagram-v2
    [*] --> v1_active: Initial Analysis
    v1_active --> v1_inactive: User edits YAML
    v1_inactive --> v2_active: Save new version
    v2_active --> v1_active: Revert to v1
    v2_active --> v2_inactive: User edits again
    v2_inactive --> v3_active: Save new version
    
    note right of v1_active: is_active=true<br/>All others false
    note right of v2_active: Only one active<br/>at a time
```

#### Image Generation Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant DB
    participant Worker
    participant Gemini
    participant Storage
    
    User->>API: POST /api/products/{id}/generate
    API->>DB: INSERT generation_requests (status='pending')
    DB-->>API: request_id
    API->>Worker: BackgroundTasks.add_task()
    API-->>User: Request submitted (request_id)
    
    Worker->>DB: UPDATE status='processing', started_at=now()
    Worker->>DB: SELECT active specification
    DB-->>Worker: YAML content
    Worker->>Gemini: Generate images (with specs)
    Gemini-->>Worker: Generated images
    Worker->>Storage: Save images
    Storage-->>Worker: storage_paths
    Worker->>DB: INSERT generated_images (for each)
    Worker->>DB: UPDATE status='completed', completed_at=now()
    
    User->>API: GET /api/generation-requests/{id}
    API->>DB: SELECT request with images
    DB-->>API: request details + images
    API-->>User: Status: completed, 3 images
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

## Implementation Checklist

### Phase 1: Foundation Setup
- [x] 1.1: Install FastAPI dependencies (fastapi, uvicorn, sqlalchemy, psycopg2, alembic)
- [x] 1.2: Install auth dependencies (python-jose, passlib, python-multipart)
- [x] 1.3: Create backend directory structure
- [x] 1.4: Set up environment configuration (.env, settings.py)
- [x] 1.5: Initialize PostgreSQL database (Docker on port 5433)

### Phase 2: Database Models & Migrations
- [x] 2.1: Create SQLAlchemy Base and database connection
- [x] 2.2: Implement User model
- [x] 2.3: Implement Product model
- [x] 2.4: Implement ProductReferenceImage model
- [x] 2.5: Implement ProductSpecification model with versioning
- [x] 2.6: Implement GenerationRequest model
- [x] 2.7: Implement GeneratedImage model
- [x] 2.8: Initialize Alembic and create initial migration
- [x] 2.9: Run migrations and verify database schema
- [x] 2.10: Seed admin user (admin/admin123)

### Phase 3: Authentication System
- [x] 3.1: Create auth utilities (password hashing, JWT tokens)
- [x] 3.2: Implement login endpoint (POST /api/auth/login)
- [x] 3.3: Implement get current user endpoint (GET /api/auth/me)
- [x] 3.4: Create authentication dependency for protected routes
- [x] 3.5: Test authentication flow

### Phase 4: Storage Service
- [x] 4.1: Create storage service interface
- [x] 4.2: Implement local file storage
- [x] 4.3: Create upload/download utilities
- [x] 4.4: Set up directory structure (refs/, specs/, generated/)
- [x] 4.5: Add image validation and processing

### Phase 5: Product API Endpoints
- [x] 5.1: POST /api/products - Create product
- [x] 5.2: GET /api/products - List all products
- [x] 5.3: GET /api/products/{id} - Get product details
- [x] 5.4: PUT /api/products/{id} - Update product
- [x] 5.5: DELETE /api/products/{id} - Delete product
- [x] 5.6: POST /api/products/{id}/upload-references - Upload reference images
- [x] 5.7: GET /api/products/{id}/references - List references
- [x] 5.8: DELETE /api/products/{id}/references/{ref_id} - Delete reference

### Phase 6: Analysis Integration
- [x] 6.1: Create AnalysisService wrapping gpt_analyzer.py
- [x] 6.2: POST /api/products/{id}/analyze - Trigger analysis
- [x] 6.3: Save YAML to product_specifications table
- [x] 6.4: Extract and store JSONB metadata (dimensions, colors)
- [x] 6.5: Return analysis results with confidence scores
- [x] 6.6: Test with stasher_half_gallon images (Verified in test_e2e.py)

### Phase 7: Specification Management
- [x] 7.1: GET /api/products/{id}/specifications - List all versions
- [x] 7.2: GET /api/products/{id}/specifications/active - Get active spec
- [x] 7.3: GET /api/products/{id}/specifications/{version} - Get specific version
- [x] 7.4: PUT /api/specifications/{id} - Update spec (create new version)
- [x] 7.5: POST /api/specifications/{id}/activate - Set active version
- [x] 7.6: Version control workflow implemented

### Phase 8: Generation Integration
- [x] 8.1: Create GenerationService wrapping generate_test.py
- [x] 8.2: POST /api/products/{id}/generate - Create generation request
- [x] 8.3: Implement background job processing with FastAPI BackgroundTasks (Fixed session isolation)
- [x] 8.4: GET /api/generation-requests/{id} - Check generation status
- [x] 8.5: GET /api/generation-requests/{id}/images - Get generated images
- [x] 8.6: GET /api/products/{id}/generations - List all generations
- [x] 8.7: GET /api/products/{id}/gallery - Gallery view
- [x] 8.8: API endpoints verified (image upload, analysis, generation endpoints implemented)

### Phase 9: API Documentation & Testing
- [x] 9.1: FastAPI OpenAPI/Swagger docs (auto-generated at /api/docs)
- [x] 9.2: Pydantic request/response schemas complete
- [x] 9.3: CORS middleware configured for frontend
- [x] 9.4: Manual API testing completed (login, product creation, image upload verified)
- [x] 9.5: Write unit tests for services (test_e2e.py covers this)
- [x] 9.6: Write integration tests for API endpoints (test_e2e.py covers full flow)

### Phase 10: Deployment Preparation
- [x] 10.1: Create Dockerfile for backend
- [x] 10.2: Create docker-compose.yml (app + postgres)
- [x] 10.3: Add production environment config (In docker-compose env vars)
- [x] 10.4: Create startup script with migrations (entrypoint.sh)
- [x] 10.5: Document API endpoints in README

---

## Implementation Order (Completed)

**Priority 1**: Foundation & Database
1. Install dependencies
2. Create project structure
3. Set up database models
4. Run migrations
5. Seed admin user

**Priority 2**: Authentication
1. Implement auth utilities
2. Create login endpoint
3. Test authentication

**Priority 3**: Core Product APIs
1. Build product CRUD endpoints
2. Add image upload functionality
3. Test with sample data

**Priority 4**: Analysis & Generation
1. Integrate existing gpt_analyzer
2. Integrate existing generate_test
3. Test full workflow

---

## Success Metrics

- [x] User can create product via API
- [x] User can upload reference images
- [x] User can trigger GPT analysis via API
- [x] YAML specifications saved with versioning
- [x] User can generate images via API
- [x] Generated images stored and retrievable
- [x] Authentication works (JWT tokens)
- [x] Frontend can consume all API endpoints
- [x] All tests pass (End-to-End verified)
- [x] API documentation complete (OpenAPI)
- [x] Docker deployment ready
