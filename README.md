# Product Describer

A modular Python application that analyzes product images using GPT vision capabilities and generates structured YAML descriptions. Upload multiple images of a product, and let GPT break it down into detailed facets.

## Features

- 📸 **Multi-Image Analysis**: Process multiple product images simultaneously
- 🤖 **GPT Vision Integration**: Uses GPT-5.2 for intelligent product analysis
- 📋 **Structured Output**: Generates detailed YAML with product facets
- � **Template-Based Analysis**: Optional structured templates for consistent, validated output
- 🔧 **Modular Design**: Clean, maintainable, and extensible architecture
- ⚙️ **Configurable**: Environment-based configuration for different products
- 🔄 **Repeatable**: Consistent analysis with reproducible results
- ✅ **Validation**: Automatic schema validation with confidence scoring

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Poetry ([installation guide](https://python-poetry.org/docs/#installation))
- OpenAI API key with GPT Vision access

### Installation

1. **Clone and setup**:
   ```bash
   # Complete setup
   make setup
   
   # Or manually:
   poetry install
   cp .env.example .env
   ```

2. **Configure environment**:
   Edit `.env` and add your settings:
   ```bash
   PRODUCT_NAME=your_product_name
   OPENAI_API_KEY=your_openai_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here  # For image generation
   ```

3. **Prepare product images**:
   ```bash
   mkdir -p data/your_product_name
   # Copy your product images to data/your_product_name/
   ```

4. **Run analysis**:
   ```bash
   make describe
   ```

5. **Generate images** (optional):
   ```bash
   make generate
   # Or with custom prompt:
   make generate PROMPT="Show on marble background"
   ```

## Usage

### Basic Analysis

```bash
# Set your product name and API key in .env
echo "PRODUCT_NAME=laptop_dell" > .env
echo "OPENAI_API_KEY=sk-..." >> .env

# Add images to data directory
mkdir -p data/laptop_dell
cp ~/photos/laptop*.jpg data/laptop_dell/

# Run analysis
poetry run python -m product_describer.main

# Results saved to: temp/laptop_dell/description.yaml
```

### Generate Images with Nano Banana Pro

After analyzing your product, you can generate new images using Google's Nano Banana Pro:

```bash
# Add Gemini API key to .env
echo "GEMINI_API_KEY=your_gemini_api_key" >> .env

# Install Google Gen AI SDK
poetry add google-genai

# Generate images from YAML specs (uses default prompt)
poetry run python -m product_describer.generate_test

# Or create a custom prompt file
echo "Create a vibrant, colorful version with tropical background" > temp/laptop_dell/generation_prompt.txt
poetry run python -m product_describer.generate_test

# Or use environment variable for one-off prompts
GENERATION_PROMPT="Show in minimalist style" poetry run python -m product_describer.generate_test

# Generated images saved to: temp/laptop_dell/test_images/generated_*.png
```

### Using Different GPT Models

```bash
# Add to .env
echo "GPT_MODEL=gpt-4-turbo" >> .env
```

### Supported Image Formats

- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- GIF (`.gif`)
- WebP (`.webp`)

## Output Format

The tool generates a YAML file with detailed product analysis:

```yaml
product_type: "Laptop"
brand: "Dell"
materials:
  - "Aluminum chassis"
  - "Plastic components"
colors:
  - "Silver"
  - "Black"
key_features:
  - "15.6 inch display"
  - "Backlit keyboard"
  - "Multiple USB ports"
# ... additional facets
```

## Project Structure

```
product-describer/
├── src/
│   └── product_describer/
│       ├── __init__.py
│       ├── main.py              # Entry point
│       ├── config.py            # Configuration
│       ├── image_handler.py     # Image processing
│       └── gpt_analyzer.py      # GPT integration
├── tests/                       # Test suite
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md         # System design
│   ├── EXECUTION_PLAN.md       # Usage guide
│   └── DEVELOPER.md            # Dev guide
├── data/                        # Input images (gitignored)
├── temp/                        # Output YAML (gitignored)
├── pyproject.toml              # Dependencies
├── .env.example                # Config template
└── README.md                   # This file
```

## Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[Architecture](docs/ARCHITECTURE.md)**: System design and component documentation
- **[Execution Plan](docs/EXECUTION_PLAN.md)**: Detailed usage and troubleshooting
- **[Developer Guide](docs/DEVELOPER.md)**: Development workflow and API reference
- **[YAML Template Proposal](docs/YAML_TEMPLATE_PROPOSAL.md)**: Template-based analysis system design
- **[Analysis Prompt Improvements](docs/ANALYSIS_PROMPT_IMPROVEMENTS.md)**: GPT Vision prompt optimization
- **[Generation Prompt Improvements](docs/GENERATION_PROMPT_IMPROVEMENTS.md)**: Image generation prompt guidelines

## Template-Based Analysis

Product Describer now supports template-based analysis for more consistent and structured output:

### Using Templates

```python
from product_describer.gpt_analyzer import GPTAnalyzer

# Enable template-based analysis (default in v1.0+)
analyzer = GPTAnalyzer(
    api_key="your_key",
    use_template=True,  # Default: True
    template_version="1.0"
)

# Disable to use free-form analysis
analyzer = GPTAnalyzer(api_key="your_key", use_template=False)
```

### Template Features

- **Structured Fields**: Predefined sections for dimensions, geometry, colors, materials, labels
- **Confidence Scoring**: 0.0-1.0 confidence scores for uncertain measurements
- **Automatic Validation**: Schema validation with detailed error reporting
- **Measurement Basis**: Track how each measurement was derived
- **ISO Standards**: Date formats, unit consistency, hex color codes
- **Uncertainty Tracking**: Identify fields needing validation

### Available Templates

Templates are stored in [`templates/`](templates/):

- **product_analysis_v1.0.yaml**: Comprehensive product analysis template
  - Dimensions with confidence scores
  - Geometry (corners, edges, thickness, symmetry)
  - Colors with hex codes and coverage
  - Materials and optical properties
  - Labels and graphics placement
  - Deformation behaviors
  - Analysis notes and uncertainty tracking

See [`templates/README.md`](templates/README.md) for complete template documentation.

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Quality

```bash
# Format code
poetry run black src/ tests/

# Lint code
poetry run flake8 src/ tests/

# Type checking
poetry run mypy src/
```

### Adding New Features

See the [Developer Guide](docs/DEVELOPER.md) for detailed instructions on:
- Setting up development environment
- Writing tests
- Code style guidelines
- Contribution workflow

## Troubleshooting

### No images found
```bash
# Verify directory structure
ls -la data/$PRODUCT_NAME/
```

### API authentication error
```bash
# Check your .env file
cat .env | grep OPENAI_API_KEY
```

### Image validation errors
```bash
# Test image files
file data/$PRODUCT_NAME/*
```

For more troubleshooting, see [Execution Plan - Error Handling](docs/EXECUTION_PLAN.md#error-handling--troubleshooting).

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PRODUCT_NAME` | Yes | - | Product identifier for directories |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `GEMINI_API_KEY` | No | - | Gemini API key for image generation |
| `GPT_MODEL` | No | `gpt-5.2-2025-12-11` | GPT model version |
| `USE_TEMPLATE` | No | `true` | Enable template-based analysis |
| `TEMPLATE_VERSION` | No | `1.0` | Template version to use |

## Examples

### Example 1: Analyze a Shoe
```bash
PRODUCT_NAME=nike_air_max poetry run python -m product_describer.main
```

### Example 2: Batch Process Multiple Products
```bash
for product in laptop phone tablet; do
  PRODUCT_NAME=$product poetry run python -m product_describer.main
done
```

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please read our [Developer Guide](docs/DEVELOPER.md#contributing) first.

## Support

- 📖 Documentation: [`docs/`](docs/)
- 🐛 Issues: Open an issue on GitHub
- 💬 Questions: Check the [Execution Plan](docs/EXECUTION_PLAN.md)

## Deployment

### Docker Deployment

The application is containerized and can be deployed using Docker Compose.

```bash
# Build and start services (Backend + Database)
docker-compose up -d --build
```

The API will be available at `http://localhost:8000`.

### API Documentation

The backend provides interactive API documentation via Swagger UI.

- **Swagger UI**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **ReDoc**: [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)

#### Key Endpoints

- **Auth**: `POST /api/auth/login` (Get JWT token)
- **Products**: 
  - `POST /api/products` (Create product)
  - `GET /api/products` (List products)
  - `POST /api/products/{id}/upload-references` (Upload images)
- **Analysis**: `POST /api/products/{id}/analyze` (Trigger GPT analysis)
- **Generation**: `POST /api/products/{id}/generate` (Trigger image generation)

