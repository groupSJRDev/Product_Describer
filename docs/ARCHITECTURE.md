# Architecture Documentation

## System Overview

Product Describer is a modular Python application that analyzes product images using GPT vision capabilities and generates structured YAML descriptions.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Product Describer                        │
│                                                              │
│  ┌────────────┐                                             │
│  │   .env     │──────────────────┐                          │
│  └────────────┘                  │                          │
│                                  ▼                          │
│  ┌──────────────────────────────────────────────┐          │
│  │              main.py                          │          │
│  │  (Orchestration & CLI Interface)              │          │
│  └──────────────┬───────────────────────────────┘          │
│                 │                                            │
│                 ▼                                            │
│  ┌──────────────────────────────────────────────┐          │
│  │           config.py                           │          │
│  │  • Load environment variables                 │          │
│  │  • Validate configuration                     │          │
│  │  • Manage paths                               │          │
│  └──────────────┬───────────────────────────────┘          │
│                 │                                            │
│        ┌────────┴────────┐                                  │
│        ▼                 ▼                                  │
│  ┌─────────────┐   ┌─────────────┐                        │
│  │image_handler│   │gpt_analyzer │                        │
│  │.py          │   │.py          │                        │
│  │             │   │             │                        │
│  │• Find images│   │• Encode     │                        │
│  │• Validate   │   │  images     │                        │
│  │• Get info   │   │• Call GPT   │                        │
│  │             │   │• Parse YAML │                        │
│  └──────┬──────┘   └──────┬──────┘                        │
│         │                  │                                │
│         ▼                  ▼                                │
│  ┌──────────────┐   ┌──────────────┐                      │
│  │ data/        │   │ OpenAI API   │                      │
│  │ <PRODUCT>    │   │ GPT Vision   │                      │
│  │ *.jpg, *.png │   │              │                      │
│  └──────────────┘   └──────┬───────┘                      │
│                             │                               │
│                             ▼                               │
│                      ┌──────────────┐                      │
│                      │ temp/        │                      │
│                      │ <PRODUCT>/   │                      │
│                      │description.  │                      │
│                      │yaml          │                      │
│                      └──────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Entry Point: `main.py`
**Responsibility**: Application orchestration and user interface

- Loads configuration
- Validates environment setup
- Coordinates between modules
- Handles errors and user feedback
- Displays results

### 2. Configuration: `config.py`
**Responsibility**: Centralized configuration management

**Key Functions**:
- `__init__()`: Load environment variables
- `validate()`: Ensure required config is present
- `get_product_data_dir()`: Return path to product images
- `get_product_output_dir()`: Return path to output directory
- `get_output_file_path()`: Return full path to output YAML

**Environment Variables**:
- `PRODUCT_NAME` (required): Product identifier
- `OPENAI_API_KEY` (required): OpenAI authentication
- `GPT_MODEL` (optional): Model version (default: gpt-5.2-2025-12-11)

### 3. Image Processing: `image_handler.py`
**Responsibility**: Image file operations and validation

**Key Functions**:
- `get_image_files()`: Discover all supported images
- `encode_image_to_base64()`: Encode images for API transmission
- `get_image_info()`: Extract metadata (size, format, etc.)
- `validate_images()`: Check image integrity

**Supported Formats**: JPG, JPEG, PNG, GIF, WEBP

### 4. GPT Integration: `gpt_analyzer.py`
**Responsibility**: Communication with OpenAI GPT API

**Key Functions**:
- `analyze_product()`: Main analysis orchestration
- `_encode_image()`: Image encoding helper
- `_get_image_mime_type()`: Determine content type
- `_extract_yaml_from_response()`: Parse GPT response

**API Configuration**:
- Model: Configurable (default: gpt-5.2-2025-12-11)
- Max Tokens: 2000
- Temperature: 0.7
- Image Detail: High

**System Prompt**: Instructs GPT to analyze products and return structured YAML with facets including:
- Product Type
- Brand
- Materials
- Colors
- Dimensions
- Key Features
- Design Elements
- Condition
- Target Audience
- Use Cases
- Unique Characteristics

## Data Flow

```
1. User runs application
   ↓
2. Load .env configuration
   ↓
3. Validate PRODUCT_NAME and OPENAI_API_KEY
   ↓
4. Scan data/<PRODUCT_NAME> for images
   ↓
5. Validate images (format, readability)
   ↓
6. Encode images to base64
   ↓
7. Send to GPT Vision API with system prompt
   ↓
8. Receive structured analysis
   ↓
9. Parse YAML from response
   ↓
10. Save to temp/<PRODUCT_NAME>/description.yaml
    ↓
11. Display preview to user
```

## Directory Structure

```
product-describer/
├── src/
│   └── product_describer/
│       ├── __init__.py
│       ├── main.py              # Entry point & orchestration
│       ├── config.py             # Configuration management
│       ├── image_handler.py      # Image operations
│       └── gpt_analyzer.py       # GPT API integration
├── tests/                        # Unit tests
├── data/                         # Input: Product images
│   └── <PRODUCT_NAME>/
│       ├── image1.jpg
│       ├── image2.png
│       └── ...
├── temp/                         # Output: Generated descriptions
│   └── <PRODUCT_NAME>/
│       └── description.yaml
├── docs/                         # Documentation
├── .env                          # Environment configuration
├── .env.example                  # Configuration template
├── pyproject.toml                # Poetry dependencies
└── README.md                     # User documentation
```

## Design Principles

### Modularity
Each module has a single, well-defined responsibility with clear interfaces.

### Repeatability
- Configuration-driven execution
- Deterministic processing
- Idempotent operations (can run multiple times safely)

### Extensibility
- Easy to add new image sources
- Pluggable output formats
- Configurable GPT prompts and models

### Error Handling
- Comprehensive validation at each step
- Clear error messages with actionable guidance
- Graceful degradation when possible

## Technology Stack

- **Language**: Python 3.9+
- **Package Manager**: Poetry
- **AI/ML**: OpenAI GPT Vision API
- **Image Processing**: Pillow (PIL)
- **Data Format**: YAML
- **Configuration**: python-dotenv

## Security Considerations

1. **API Key Management**: 
   - Stored in `.env` (not committed to git)
   - Loaded at runtime via environment variables

2. **Input Validation**:
   - Image format verification
   - File integrity checks
   - Path validation (prevent directory traversal)

3. **Error Information**:
   - Sanitized error messages
   - No credential exposure in logs

## Performance Considerations

- **Image Encoding**: Base64 encoding is memory-efficient
- **API Calls**: Single batch request for all images
- **Image Detail**: High detail mode for better analysis
- **Rate Limiting**: Handled by OpenAI SDK

## Future Enhancements

- [ ] Support for batch processing multiple products
- [ ] Custom prompt templates
- [ ] Alternative output formats (JSON, CSV)
- [ ] Image preprocessing (resize, optimize)
- [ ] Caching of API responses
- [ ] Web interface
- [ ] Progress indicators for large batches
- [ ] Validation schemas for YAML output
