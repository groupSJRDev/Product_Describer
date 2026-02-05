# Database Schema Documentation

**Date**: February 5, 2026  
**System**: Product Describer Backend  
**Database**: PostgreSQL 15+  
**Status**: Implemented & Deployed

---

## Overview

The Product Describer database supports a full-stack web application for product image analysis, specification management, and AI-powered image generation. The schema is designed for versioned specifications, multi-user support, and complete audit trails.

---

## Entity Relationship Diagram

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

---

## Table Details

### 1. users

User authentication and authorization.

```mermaid
erDiagram
    users {
        int id PK "Auto-increment primary key"
        string username UK "Unique username (50 chars)"
        string hashed_password "Bcrypt hashed (255 chars)"
        string email UK "Optional unique email"
        boolean is_active "Account status (default: true)"
        timestamp created_at "Account creation time"
        timestamp updated_at "Last update time"
    }
```

**Indexes**:
- Primary Key: `id`
- Unique: `username`, `email`

**Security**:
- Passwords hashed with bcrypt
- JWT token-based authentication
- Can be extended with roles/permissions

**Default User**:
- Username: `admin`
- Password: `admin123` (hashed)

---

### 2. products

Core product entities (analogous to "brands" in VML system).

```mermaid
erDiagram
    products {
        int id PK "Auto-increment primary key"
        string name "Product name (255 chars)"
        string slug UK "URL-friendly identifier"
        text description "Optional description"
        int created_by FK "User who created product"
        timestamp created_at "Creation timestamp"
        timestamp updated_at "Last update timestamp"
        boolean is_active "Soft delete flag"
        string product_category "Optional category (100 chars)"
        array tags "PostgreSQL array of tags"
    }
    
    users ||--|| products : creates
```

**Indexes**:
- Primary Key: `id`
- Unique: `slug`
- Index: `created_by`

**Constraints**:
- Slug format: `^[a-z0-9_-]+$` (lowercase, numbers, underscores, hyphens only)

**Example**:
```sql
INSERT INTO products (name, slug, description, created_by, product_category, tags)
VALUES (
    'Stasher Half Gallon Bag',
    'stasher_half_gallon',
    'Reusable silicone storage bag',
    1,
    'Kitchen Storage',
    ARRAY['silicone', 'reusable', 'eco-friendly']
);
```

---

### 3. product_reference_images

Reference images uploaded for each product (analogous to "brand assets").

```mermaid
erDiagram
    product_reference_images {
        int id PK "Auto-increment primary key"
        int product_id FK "Parent product"
        string filename "Original filename (255 chars)"
        string storage_path "Full path to file (500 chars)"
        int file_size_bytes "File size in bytes"
        string mime_type "MIME type (e.g., image/jpeg)"
        int width "Image width in pixels"
        int height "Image height in pixels"
        int uploaded_by FK "User who uploaded"
        timestamp uploaded_at "Upload timestamp"
        boolean is_primary "Primary/hero image flag"
        int display_order "Display ordering (0-based)"
    }
    
    products ||--o{ product_reference_images : "has many"
    users ||--o{ product_reference_images : uploads
```

**Indexes**:
- Primary Key: `id`
- Index: `product_id`
- Composite Index: `(product_id, is_primary)`

**Constraints**:
- Only ONE primary image per product (PostgreSQL EXCLUDE constraint)
- Cascade delete when product is deleted

**Storage Path Example**:
```
local_storage/stasher_half_gallon/refs/original_1.jpg
```

---

### 4. product_specifications

YAML specifications generated from GPT Vision analysis with full version control.

```mermaid
erDiagram
    product_specifications {
        int id PK "Auto-increment primary key"
        int product_id FK "Parent product"
        int version "Version number (1, 2, 3...)"
        text yaml_content "Full YAML specification"
        string template_version "Template version (e.g., '1.0')"
        decimal confidence_overall "Overall confidence (0.00-1.00)"
        int image_count "Number of images analyzed"
        string analysis_model "GPT model used"
        boolean is_active "Currently active version flag"
        int created_by FK "User who created"
        timestamp created_at "Creation timestamp"
        text change_notes "Version change description"
        jsonb primary_dimensions "Quick access dimensions"
        jsonb primary_colors "Quick access color palette"
        string material_type "Quick access material"
    }
    
    products ||--o{ product_specifications : "has many"
    users ||--o{ product_specifications : creates
```

**Indexes**:
- Primary Key: `id`
- Index: `product_id`
- Composite Index: `(product_id, is_active)`
- Composite Index: `(product_id, version DESC)`

**Constraints**:
- Unique: `(product_id, version)`
- Only ONE active specification per product (PostgreSQL EXCLUDE constraint)

**Version Control Workflow**:
```mermaid
stateDiagram-v2
    [*] --> v1_active: Initial Analysis
    v1_active --> v1_inactive: User edits YAML
    v1_inactive --> v2_active: Save new version
    v2_active --> v1_active: Revert to v1
    v2_active --> v2_inactive: User edits again
    v2_inactive --> v3_active: Save new version
```

**JSONB Fields** (for fast queries without parsing YAML):
- `primary_dimensions`: `{"width": 215.9, "height": 260.35, "depth": 35.0, "unit": "mm"}`
- `primary_colors`: `[{"hex": "#CFE7EE", "name": "pale icy blue"}, {...}]`
- `material_type`: `"silicone"`

---

### 5. generation_requests

Image generation jobs with status tracking.

```mermaid
erDiagram
    generation_requests {
        int id PK "Auto-increment primary key"
        int product_id FK "Target product"
        int specification_id FK "Specification used (nullable)"
        text prompt "Generation prompt"
        text custom_prompt_override "User's custom prompt"
        string aspect_ratio "Aspect ratio (default: '1:1')"
        string resolution "Resolution (default: '2K')"
        int image_count "Number of images to generate"
        string model "AI model (default: gemini-3-pro)"
        string status "Status: pending/processing/completed/failed"
        timestamp started_at "Processing start time"
        timestamp completed_at "Processing end time"
        text error_message "Error details if failed"
        int created_by FK "User who requested"
        timestamp created_at "Request creation time"
    }
    
    products ||--o{ generation_requests : "has many"
    product_specifications ||--o{ generation_requests : "used by"
    users ||--o{ generation_requests : initiates
```

**Indexes**:
- Primary Key: `id`
- Index: `product_id`
- Index: `status`
- Index: `created_by`
- Index: `created_at DESC`

**Constraints**:
- Status CHECK: `IN ('pending', 'processing', 'completed', 'failed')`

**Status Lifecycle**:
```mermaid
stateDiagram-v2
    [*] --> pending: User submits request
    pending --> processing: Background job starts
    processing --> completed: Generation succeeds
    processing --> failed: Generation fails
    completed --> [*]
    failed --> [*]
```

---

### 6. generated_images

Output images from generation requests.

```mermaid
erDiagram
    generated_images {
        int id PK "Auto-increment primary key"
        int generation_request_id FK "Parent generation request"
        int product_id FK "Product (for quick filtering)"
        string filename "Generated filename (255 chars)"
        string storage_path "Full path to file (500 chars)"
        int file_size_bytes "File size in bytes"
        string mime_type "MIME type (default: image/png)"
        int width "Image width in pixels"
        int height "Image height in pixels"
        int generation_index "Index if count > 1 (1, 2, 3...)"
        text model_response_text "Any text response from model"
        timestamp created_at "Creation timestamp"
    }
    
    generation_requests ||--o{ generated_images : produces
    products ||--o{ generated_images : "has many"
```

**Indexes**:
- Primary Key: `id`
- Index: `generation_request_id`
- Index: `product_id`
- Index: `created_at DESC`

**Constraints**:
- Unique: `(generation_request_id, generation_index)`
- Cascade delete when generation_request is deleted

**Storage Path Example**:
```
local_storage/stasher_half_gallon/generated/2026/02/20260205_143022_abc123.png
```

---

## Database Workflows

### Workflow 1: Product Creation & Analysis

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

### Workflow 2: Specification Versioning

```mermaid
sequenceDiagram
    participant User
    participant API
    participant DB
    
    User->>API: GET /api/products/{id}/specifications/active
    API->>DB: SELECT WHERE product_id AND is_active=true
    DB-->>API: specification (v1)
    API-->>User: Current YAML
    
    User->>API: PUT /api/specifications/{id} (edited YAML)
    API->>DB: UPDATE v1 SET is_active=false
    API->>DB: INSERT v2 (is_active=true, change_notes="User edit")
    DB-->>API: new_specification_id
    API-->>User: Version 2 saved
    
    User->>API: POST /api/specifications/{v1_id}/activate
    API->>DB: UPDATE v2 SET is_active=false
    API->>DB: UPDATE v1 SET is_active=true
    DB-->>API: Success
    API-->>User: Reverted to v1
```

### Workflow 3: Image Generation

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

---

## Storage Architecture

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

**Path Templates**:
- Reference images: `local_storage/{product_slug}/refs/{filename}`
- Specifications: `local_storage/{product_slug}/specs/v{version}.yaml`
- Generated images: `local_storage/{product_slug}/generated/{year}/{month}/{timestamp}_{hash}.png`

---

## Query Examples

### Get Product with All Related Data

```sql
SELECT 
    p.id,
    p.name,
    p.slug,
    COUNT(DISTINCT pri.id) as reference_count,
    COUNT(DISTINCT ps.id) as spec_version_count,
    COUNT(DISTINCT gr.id) as generation_count,
    COUNT(DISTINCT gi.id) as generated_image_count
FROM products p
LEFT JOIN product_reference_images pri ON p.id = pri.product_id
LEFT JOIN product_specifications ps ON p.id = ps.product_id
LEFT JOIN generation_requests gr ON p.id = gr.product_id
LEFT JOIN generated_images gi ON p.id = gi.product_id
WHERE p.is_active = true
GROUP BY p.id;
```

### Get Active Specification with Quick Access Fields

```sql
SELECT 
    ps.id,
    ps.version,
    ps.yaml_content,
    ps.primary_dimensions->>'width' as width,
    ps.primary_dimensions->>'height' as height,
    ps.primary_dimensions->>'unit' as unit,
    ps.primary_colors,
    ps.material_type,
    ps.confidence_overall,
    ps.created_at
FROM product_specifications ps
WHERE ps.product_id = $1
  AND ps.is_active = true;
```

### Get Recent Generations with Images

```sql
SELECT 
    gr.id,
    gr.prompt,
    gr.status,
    gr.created_at,
    gr.completed_at,
    COUNT(gi.id) as image_count,
    ARRAY_AGG(gi.storage_path) as image_paths
FROM generation_requests gr
LEFT JOIN generated_images gi ON gr.id = gi.generation_request_id
WHERE gr.product_id = $1
GROUP BY gr.id
ORDER BY gr.created_at DESC
LIMIT 10;
```

### Search Products by Color (JSONB Query)

```sql
SELECT DISTINCT
    p.id,
    p.name,
    p.slug,
    ps.primary_colors
FROM products p
JOIN product_specifications ps ON p.id = ps.product_id
WHERE ps.is_active = true
  AND ps.primary_colors @> '[{"hex": "#CFE7EE"}]'::jsonb;
```

---

## Migration History

### Initial Migration: `cf5f6be2f015_initial_schema_with_users_products_.py`

**Created**: 2026-01-27  
**Status**: Applied

**Tables Created**:
1. `users`
2. `products`
3. `product_reference_images`
4. `product_specifications`
5. `generation_requests`
6. `generated_images`

**Features**:
- Full foreign key relationships
- Check constraints for data validation
- Composite indexes for performance
- PostgreSQL-specific features (ARRAY, JSONB, EXCLUDE constraints)
- Cascade delete for dependent records

---

## Performance Considerations

### Indexes

All critical query paths have appropriate indexes:
- Primary keys (auto-indexed)
- Foreign keys
- Unique constraints
- Composite indexes for common query patterns
- Timestamp indexes for sorting

### JSONB Usage

JSONB fields provide fast queries without parsing YAML:
```sql
-- Fast dimension lookup
WHERE ps.primary_dimensions->>'width' > '200'

-- Fast color search
WHERE ps.primary_colors @> '[{"hex": "#CFE7EE"}]'::jsonb
```

### Soft Deletes

Products use `is_active` flag instead of hard deletes to:
- Preserve historical data
- Maintain referential integrity
- Enable undo/restore functionality

---

## Security Features

### Password Security
- Bcrypt hashing with salt
- No plain text passwords stored
- Configurable hash rounds

### JWT Authentication
- Stateless authentication
- Configurable expiration
- Secure token generation

### SQL Injection Prevention
- Parameterized queries via SQLAlchemy ORM
- Input validation via Pydantic schemas

### Access Control
- User ownership tracking (`created_by` fields)
- Can be extended with role-based permissions

---

## Backup & Recovery

### Recommended Backup Strategy

```bash
# Daily automated backup
pg_dump -U pd_user -h localhost -p 5433 product_describer_db \
  -F c -b -v -f backup_$(date +%Y%m%d).dump

# Point-in-time recovery
psql -U pd_user -h localhost -p 5433 product_describer_db \
  < backup_20260205.dump
```

### Data Retention

- **Users**: Permanent
- **Products**: Soft delete (permanent storage)
- **Specifications**: All versions preserved
- **Generations**: Permanent (consider archival strategy for old images)
- **Images**: Consider moving old generated images to cold storage

---

## Future Enhancements

### Potential Schema Extensions

1. **Role-Based Access Control**
   ```sql
   CREATE TABLE roles (
       id SERIAL PRIMARY KEY,
       name VARCHAR(50) UNIQUE NOT NULL
   );
   
   CREATE TABLE user_roles (
       user_id INTEGER REFERENCES users(id),
       role_id INTEGER REFERENCES roles(id),
       PRIMARY KEY (user_id, role_id)
   );
   ```

2. **Product Collections/Categories**
   ```sql
   CREATE TABLE product_collections (
       id SERIAL PRIMARY KEY,
       name VARCHAR(255) NOT NULL,
       description TEXT
   );
   
   CREATE TABLE product_collection_memberships (
       product_id INTEGER REFERENCES products(id),
       collection_id INTEGER REFERENCES product_collections(id),
       PRIMARY KEY (product_id, collection_id)
   );
   ```

3. **Image Favorites/Ratings**
   ```sql
   CREATE TABLE image_favorites (
       user_id INTEGER REFERENCES users(id),
       image_id INTEGER REFERENCES generated_images(id),
       rating INTEGER CHECK (rating BETWEEN 1 AND 5),
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       PRIMARY KEY (user_id, image_id)
   );
   ```

4. **Audit Trail**
   ```sql
   CREATE TABLE audit_log (
       id SERIAL PRIMARY KEY,
       table_name VARCHAR(100) NOT NULL,
       record_id INTEGER NOT NULL,
       action VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
       old_data JSONB,
       new_data JSONB,
       user_id INTEGER REFERENCES users(id),
       timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

---

## Related Documentation

- [BACKEND_DATABASE_PLAN.md](./BACKEND_DATABASE_PLAN.md) - Implementation plan and checklist
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Overall system architecture
- [DEVELOPER.md](./DEVELOPER.md) - Developer guide with API documentation
- [README.md](../README.md) - Project overview and setup instructions

---

## Maintenance Commands

### View Schema Information

```sql
-- List all tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- View table structure
\d+ products

-- Check indexes
SELECT * FROM pg_indexes WHERE schemaname = 'public';

-- View foreign keys
SELECT * FROM information_schema.table_constraints 
WHERE constraint_type = 'FOREIGN KEY';
```

### Database Statistics

```sql
-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Row counts
SELECT 
    schemaname,
    tablename,
    n_tup_ins - n_tup_del as row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public';
```

---

**Last Updated**: February 5, 2026  
**Schema Version**: 1.0  
**Migration**: cf5f6be2f015
