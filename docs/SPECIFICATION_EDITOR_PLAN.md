# Specification Editor & Reference Images Feature Plan

**Date**: January 28, 2026  
**Branch**: planning/db_rethink-012826  
**Reference**: VML Brand-Based Image Generation project structure

## Overview

Implement a comprehensive specification (YAML) management system that allows users to:
1. View and edit the active YAML specification for a product
2. Save edits as new versions (incremental versioning)
3. View version history and rollback to previous versions
4. See which reference images are being sent with generation requests
5. Upload/manage reference images (up to 4 per product)

## Architecture Reference

### VML Project Structure
- **Style Guides** stored as versioned YAML files with metadata
- **Assets** (reference images) stored per brand with UUID filenames
- **Modal Editor** with Edit/History tabs
- **Version Management** with "Activate" functionality for rollback

**Local Storage Structure** (VML):
```
/local_storage/
  /{brand-name}/
    style_guides/
      v1.yaml
      v2.yaml
      ...
    assets/
      {uuid}.jpg
      {uuid}.png
      ...
    gen/
      {generation-outputs}
```

**Database** (VML):
- `brands` table (id, name, slug, created_at, is_protected)
- `style_guides` table (id, brand_id, version, content, is_active, created_at, created_by)
- `assets` table (id, style_guide_id, storage_path, mime_type, uploaded_at)

## Current Product Describer Architecture

### Database Schema (Already Exists)
✅ **products** table
- id, name, slug, description, created_by, created_at, updated_at, is_active
- product_category, tags

✅ **product_specifications** table
- id, product_id, **version**, **yaml_content**, template_version
- confidence_overall, image_count, analysis_model
- **is_active**, created_by, created_at, change_notes
- primary_dimensions, primary_colors, material_type (JSONB)

✅ **product_reference_images** table
- id, product_id, filename, storage_path, file_size_bytes
- mime_type, width, height, uploaded_by, uploaded_at
- **is_primary**, **display_order**

### Local Storage Structure (Already Exists)
```
/local_storage/
  /{product_slug}/
    specs/
      v1.yaml
      v2.yaml
      v3.yaml
      ...
    refs/
      {uuid}.jpg
      {uuid}.png
      ...
    generated/
      {generation-outputs}
```

## Implementation Plan

### Phase 1: Backend API Endpoints

#### 1.1 Specification Management Endpoints

**GET `/api/products/{product_id}/specifications`**
- Returns list of all specification versions for a product
- Includes: id, version, is_active, created_at, created_by, change_notes
- Orders by version DESC
- Response format:
```json
[
  {
    "id": 1,
    "product_id": 1,
    "version": 8,
    "is_active": true,
    "created_at": "2026-01-28T12:00:00Z",
    "created_by": 1,
    "change_notes": "Adjusted color palette for consistency",
    "yaml_preview": "product_name: Stasher Half Gallon..."
  },
  ...
]
```

**GET `/api/products/{product_id}/specifications/{spec_id}`**
- Returns full YAML content for a specific version
- Includes complete metadata
- Used when viewing/editing a specific version

**POST `/api/products/{product_id}/specifications`**
- Creates new version with incremented version number
- Payload: `{ yaml_content: string, change_notes?: string }`
- Automatically deactivates previous version
- Sets new version as active
- Saves YAML to local storage: `local_storage/{slug}/specs/v{N}.yaml`
- Response: newly created specification object

**PUT `/api/specifications/{spec_id}/activate`**
- Sets specified version as active (is_active = true)
- Deactivates all other versions for that product
- Used for rollback functionality
- Response: updated specification object

#### 1.2 Reference Images Endpoints

**GET `/api/products/{product_id}/reference-images`**
- Returns all reference images for product
- Includes public URLs for display
- Ordered by display_order
- Response format:
```json
[
  {
    "id": 1,
    "product_id": 1,
    "filename": "front_view.jpg",
    "storage_path": "stasher_half_gallon/refs/abc123.jpg",
    "url": "http://localhost:8001/assets/stasher_half_gallon/refs/abc123.jpg",
    "mime_type": "image/jpeg",
    "width": 1920,
    "height": 1080,
    "is_primary": true,
    "display_order": 0,
    "uploaded_at": "2026-01-28T10:00:00Z"
  },
  ...
]
```

**POST `/api/products/{product_id}/reference-images`**
- Uploads new reference image
- Form-data: file upload
- Generates UUID filename
- Saves to: `local_storage/{slug}/refs/{uuid}.{ext}`
- Extracts image metadata (width, height, size)
- Sets next display_order
- Response: newly created image object

**DELETE `/api/reference-images/{image_id}`**
- Removes reference image from DB
- Deletes file from local storage
- Admin permission required

**PUT `/api/reference-images/{image_id}/order`**
- Updates display_order for reordering
- Payload: `{ display_order: number }`

### Phase 2: Frontend Components

#### 2.1 SpecificationEditor Modal Component

**Location**: `frontend/components/dashboard/SpecificationEditor.tsx`

**Props**:
```typescript
interface SpecificationEditorProps {
  isOpen: boolean;
  onClose: () => void;
  productId: number;
  productSlug: string;
  onSaveSuccess: () => void;
}
```

**Features**:
- **Tabbed Interface**: "Editor" tab and "History" tab
- **Editor Tab**:
  - Large textarea with monospace font for YAML editing
  - Syntax highlighting (optional, can use `react-syntax-highlighter`)
  - Load active specification on open
  - "Save as New Version" button
  - Optional "Change Notes" field
  - Loading states, error handling
  
- **History Tab**:
  - List all versions with metadata
  - Show which version is currently active (highlighted)
  - "Revert" button for non-active versions
  - Confirmation dialog before rollback
  - Display: version number, created date, created by, change notes
  
**State Management**:
```typescript
const [activeTab, setActiveTab] = useState<'edit' | 'history'>('edit');
const [yamlContent, setYamlContent] = useState('');
const [changeNotes, setChangeNotes] = useState('');
const [versions, setVersions] = useState<Specification[]>([]);
const [isSaving, setIsSaving] = useState(false);
const [isLoadingHistory, setIsLoadingHistory] = useState(false);
```

**UI Design** (following VML pattern):
- Modal overlay with backdrop blur
- 800px width, 80vh height
- Header with tabs and close button
- Content area with scroll
- Footer with action buttons
- Purple accent color for active items
- Gray/white color scheme

#### 2.2 ReferenceImagesPanel Component

**Location**: `frontend/components/dashboard/ReferenceImagesPanel.tsx`

**Props**:
```typescript
interface ReferenceImagesPanelProps {
  productId: number;
  productSlug: string;
}
```

**Features**:
- Display up to 4 reference images in grid layout
- Show image thumbnails (150x150px with object-fit: cover)
- "Upload" button (multiple file selection, up to 4 total)
- "Delete" button on hover for each image
- Display order indicators (1, 2, 3, 4)
- Loading states for upload/delete
- Empty state: "No reference images. Upload up to 4 images."

**UI Layout**:
```
┌──────────────────────────────────────┐
│  Reference Images (Used in Generation) │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  │
│  │  1  │  │  2  │  │  3  │  │  4  │  │
│  │ IMG │  │ IMG │  │ [+] │  │     │  │
│  │ [x] │  │ [x] │  │     │  │     │  │
│  └─────┘  └─────┘  └─────┘  └─────┘  │
│           [Upload Images]             │
└──────────────────────────────────────┘
```

**Functionality**:
- Click image to view full size (use existing ImageModal)
- Hover to show delete button
- Upload validates: max 4 images total, image file types only
- Toast notifications for success/error

#### 2.3 Integration into Generate Page

**File**: `frontend/app/dashboard/generate/page.tsx`

**Changes**:
1. Add state for spec editor modal:
```typescript
const [isSpecEditorOpen, setIsSpecEditorOpen] = useState(false);
```

2. Add button to open spec editor (near product selector):
```tsx
{selectedProductId && (
  <button
    onClick={() => setIsSpecEditorOpen(true)}
    className="flex items-center gap-2 text-sm text-purple-600 hover:text-purple-700"
  >
    <Edit2 className="h-4 w-4" />
    View/Edit Specification
  </button>
)}
```

3. Add ReferenceImagesPanel above or below GenerationForm:
```tsx
{selectedProductId && (
  <ReferenceImagesPanel
    productId={selectedProductId}
    productSlug={selectedProduct?.slug || ''}
  />
)}
```

4. Add SpecificationEditor modal:
```tsx
<SpecificationEditor
  isOpen={isSpecEditorOpen}
  onClose={() => setIsSpecEditorOpen(false)}
  productId={selectedProductId || 0}
  productSlug={selectedProduct?.slug || ''}
  onSaveSuccess={() => {
    // Optionally refresh something
  }}
/>
```

**Page Layout Structure**:
```
┌────────────────────────────────────────────┐
│  Product Selector                          │
│  [Stasher Half Gallon ▼] [Edit Spec]      │
├────────────────────────────────────────────┤
│  Reference Images Panel                    │
│  [Grid of 4 images with upload]           │
├────────────────────────────────────────────┤
│  Generation Form                           │
│  Prompt: [___________________________]     │
│  Aspect Ratio: [____________]              │
│  [Generate]                                │
├────────────────────────────────────────────┤
│  Results Gallery                           │
│  [Grid of generated images]               │
└────────────────────────────────────────────┘
```

### Phase 3: API Client Updates

**File**: `frontend/lib/api.ts`

Add API functions:
```typescript
// Specifications
export const getSpecifications = (productId: number) =>
  api.get(`/products/${productId}/specifications`);

export const getSpecification = (productId: number, specId: number) =>
  api.get(`/products/${productId}/specifications/${specId}`);

export const createSpecification = (productId: number, data: { yaml_content: string; change_notes?: string }) =>
  api.post(`/products/${productId}/specifications`, data);

export const activateSpecification = (specId: number) =>
  api.put(`/specifications/${specId}/activate`);

// Reference Images
export const getReferenceImages = (productId: number) =>
  api.get(`/products/${productId}/reference-images`);

export const uploadReferenceImage = (productId: number, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post(`/products/${productId}/reference-images`, formData);
};

export const deleteReferenceImage = (imageId: number) =>
  api.delete(`/reference-images/${imageId}`);
```

### Phase 4: Types Updates

**File**: `frontend/lib/types.ts`

Add types:
```typescript
export interface Specification {
  id: number;
  product_id: number;
  version: number;
  yaml_content: string;
  template_version: string;
  is_active: boolean;
  created_at: string;
  created_by: number;
  change_notes?: string;
  confidence_overall?: number;
  yaml_preview?: string; // For list view
}

export interface ReferenceImage {
  id: number;
  product_id: number;
  filename: string;
  storage_path: string;
  url: string;
  mime_type: string;
  width: number;
  height: number;
  is_primary: boolean;
  display_order: number;
  uploaded_at: string;
}
```

## User Flow

### Viewing/Editing Specifications

1. User selects product from dropdown
2. "View/Edit Specification" button appears
3. Click button → modal opens with active YAML in editor
4. User can:
   - Edit YAML directly
   - Add change notes
   - Click "Save as New Version"
   - Switch to "History" tab to see all versions
   - Click "Revert" on old version to make it active again
5. On save, new version is created and set as active
6. Modal closes, toast shows success

### Managing Reference Images

1. User selects product
2. Reference Images panel shows current images (or empty state)
3. User can:
   - Click image to view full size
   - Hover and click [x] to delete
   - Click "Upload Images" to add more (up to 4 total)
4. When generating, these images are automatically included in the request

### Generation Flow

1. User fills out generation form
2. Backend uses:
   - Active specification YAML (is_active=true)
   - All reference images for the product
   - User's custom prompt (merged with spec)
3. Images are generated using combined context

## Technical Considerations

### Backend Service Logic

**File**: `src/backend/services/specification.py` (create new service)

```python
class SpecificationService:
    """Service for managing product specifications"""
    
    async def get_specifications(self, product_id: int) -> List[ProductSpecification]:
        """Get all versions for a product"""
        
    async def create_specification(
        self, 
        product_id: int, 
        yaml_content: str,
        created_by: int,
        change_notes: Optional[str] = None
    ) -> ProductSpecification:
        """Create new version, deactivate old, save file"""
        
    async def activate_specification(self, spec_id: int) -> ProductSpecification:
        """Set version as active, deactivate others"""
```

**File**: `src/backend/services/reference_images.py` (create new service)

```python
class ReferenceImageService:
    """Service for managing reference images"""
    
    async def upload_image(
        self,
        product_id: int,
        file: UploadFile,
        uploaded_by: int
    ) -> ProductReferenceImage:
        """Save image file, create DB record"""
        
    async def delete_image(self, image_id: int):
        """Remove DB record and file"""
```

### Frontend Hooks

**File**: `frontend/hooks/useSpecifications.ts`

```typescript
export function useSpecifications(productId?: number) {
  const [specifications, setSpecifications] = useState<Specification[]>([]);
  const [activeSpec, setActiveSpec] = useState<Specification | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchSpecifications = useCallback(async () => {
    if (!productId) return;
    // Fetch and set
  }, [productId]);

  const saveSpecification = async (yamlContent: string, changeNotes?: string) => {
    // Create new version
  };

  const activateVersion = async (specId: number) => {
    // Activate old version (rollback)
  };

  return {
    specifications,
    activeSpec,
    isLoading,
    fetchSpecifications,
    saveSpecification,
    activateVersion
  };
}
```

**File**: `frontend/hooks/useReferenceImages.ts`

```typescript
export function useReferenceImages(productId?: number) {
  const [images, setImages] = useState<ReferenceImage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchImages = useCallback(async () => {
    if (!productId) return;
    // Fetch and set
  }, [productId]);

  const uploadImage = async (file: File) => {
    // Upload and refresh
  };

  const deleteImage = async (imageId: number) => {
    // Delete and refresh
  };

  return {
    images,
    isLoading,
    fetchImages,
    uploadImage,
    deleteImage
  };
}
```

## Database Migrations

### Migration: Add missing columns if needed

Check current schema and ensure:
- ✅ `product_specifications.is_active` exists
- ✅ `product_specifications.version` exists
- ✅ `product_specifications.change_notes` exists
- ✅ `product_reference_images.display_order` exists

All columns already exist based on current schema review!

## Testing Plan

### Backend Tests
1. Test specification versioning (create, list, activate)
2. Test reference image upload/delete
3. Test file storage operations
4. Test permission checks (admin required for edits)

### Frontend Tests
1. Test modal open/close
2. Test YAML editing and save
3. Test version history display
4. Test rollback functionality
5. Test reference image upload/delete
6. Test integration with generation flow

### Integration Tests
1. Full flow: upload images → edit spec → generate
2. Version rollback flow
3. Multi-user concurrent editing

## Success Criteria

✅ User can view active YAML specification for a product  
✅ User can edit YAML and save as new version  
✅ User can add optional change notes  
✅ User can view complete version history  
✅ User can rollback to previous version  
✅ User can see which reference images are being used  
✅ User can upload up to 4 reference images  
✅ User can delete reference images  
✅ Reference images are automatically included in generation requests  
✅ All operations have proper loading states and error handling  
✅ UI follows existing design system (Tailwind, Radix UI)  

## Timeline Estimate

- Phase 1 (Backend): 4-6 hours
- Phase 2 (Frontend Components): 6-8 hours
- Phase 3 (API Client): 1 hour
- Phase 4 (Types): 30 minutes
- Testing & Polish: 2-3 hours

**Total**: ~14-18 hours

## Notes

- Backend models and storage structure already support this feature
- Can reuse existing toast notification system
- Can reuse existing auth/permission checks
- File storage service already handles asset URLs
- Generation service already queries for active spec (is_active=True)

## Next Steps

1. ✅ Review and approve this plan
2. Create backend API endpoints
3. Build SpecificationEditor component
4. Build ReferenceImagesPanel component
5. Integrate into generate page
6. Test end-to-end flow
7. Deploy to main branch
