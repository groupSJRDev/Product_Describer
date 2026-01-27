# Code Refactoring Plan - 2026-01-27

**Status**: Draft
**Objective**: Improve code health, maintainability, and scalability of the Product Describer backend.

## 1. Helper Function Extraction

Isolate specific logic into reusable helper functions to reduce controller bloat and improve testability.

### 1.1 Image Processing Helpers
**File**: `src/backend/api/products.py` -> `src/backend/utils/images.py`

*   **Current State**: Validating file types, reading bytes, and using `PIL.Image.open` happens directly inside the `upload_reference_images` endpoint.
*   **Refactor**: Create a `validate_and_process_image(file: UploadFile)` helper.
    *   **Responsibilities**:
        *   Check content type (MIME).
        *   Read bytes safely.
        *   Extract dimensions (width/height).
        *   Return a clean data structure (bytes, metadata).
*   **Benefit**: Cleaner controller, easier to mock image upload in tests.

### 1.2 Specification Extraction
**File**: `src/product_describer/generate_test.py` -> `src/backend/utils/specs.py`

*   **Current State**: `_extract_key_specifications` is a private function inside the generation module.
*   **Refactor**: Expose this as a public utility `extract_critical_specs(specs_dict)`.
*   **Benefit**: The frontend or other services might want to display "Key Specs" without triggering a full generation.

## 2. Configuration & decoupling

### 2.1 Config Unification
**File**: `src/product_describer/config.py` vs `src/backend/config.py`

*   **Current State**: Two config systems exist. `product_describer` relies on strict directory structures (`data/`, `temp/`) and `PRODUCT_NAME` env var, which doesn't fit the API's "product-agnostic" model.
*   **Refactor**: 
    *   Ensure `product_describer` core functions accept **explicit paths** and **keys** rather than looking up global config values.
    *   (Already largely done in `generate_test.py`, but needs verification in `gpt_analyzer.py`).

### 2.2 Path Sanitization
**File**: `src/backend/api/schemas.py`

*   **Current State**: `ReferenceImageResponse` returns the raw `storage_path` (e.g., `local_storage/stasher_half_gallon/...`).
*   **Risk**: Leaking absolute paths or internal structure.
*   **Refactor**: 
    *   Return a relative URL or ID that the frontend uses to fetch the image via a dedicated download endpoint.
    *   Ensure `storage_service` returns "safe" paths for the API to consume.

## 3. Unused Variables & Parameters (Health Check)

### 3.1 Schemas vs Models
*   **Tags & Categories**: `ProductBase` includes `tags` and `product_category`. These are persisted but currently unused in business logic.
    *   **Decision**: **Keep**. These are essential for the upcoming "Search/Filter" feature in the frontend.
*   **Template Version**: `ProductSpecification` tracks `template_version`.
    *   **Decision**: **Keep**. Critical for auditing AI prompts later.

### 3.2 function arguments
*   **`use_template` in `AnalysisService.analyze_product`**:
    *   Currently defaults to `True`. Check if we ever execute `False`. If not, is the logic for "freestyle analysis" stale?
    *   **Action**: Verify if freestyle analysis is still a valid use case.

## 4. Scalability Improvements

### 4.1 Database Logic
**File**: `src/backend/api/products.py`

*   **Current State**: Direct DB queries in controllers (e.g., `db.query(Product)...`).
*   **Refactor**: Move Product CRUD operations to `src/backend/services/product.py`.
*   **Benefit**: 
    *   Allows calling product creation from CLI scripts or background tasks without mocking HTTP requests.
    *   Centralizes validation logic (e.g., "slug must be unique").

### 4.2 Storage Abstraction
**File**: `src/backend/services/storage.py`

*   **Current State**: Uses `local_storage` and string paths.
*   **Refactor**: 
    *   Ensure `StorageService` is an interface/abstract class.
    *   Local implementation should use `pathlib.Path` objects consistently internally but return strings to API.
    *   Prepare for S3 implementation by strictly separating "save", "get_url", and "delete".

## 5. Execution Plan (Immediate Steps)

1.  **Extract Image Util**: Create `src/backend/utils/image_processing.py`.
2.  **Sanitize API Response**: Modify `ReferenceImageResponse` to not leak raw absolute paths.
3.  **Refactor Product Controller**: Create `ProductService` class and move CRUD logic there.
4.  **Audit GPT Analyzer**: Ensure `gpt_analyzer.py` doesn't enforce `PRODUCT_NAME` env var when called from Backend.
