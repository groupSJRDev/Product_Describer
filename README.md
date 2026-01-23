# Product Describer

A modular Python application that analyzes product images using GPT vision capabilities and generates structured YAML descriptions. Upload multiple images of a product, and let GPT break it down into detailed facets.

## Features

- 📸 **Multi-Image Analysis**: Process multiple product images simultaneously
- 🤖 **GPT Vision Integration**: Uses GPT-5.2 for intelligent product analysis
- 📋 **Structured Output**: Generates detailed YAML with product facets
- 🔧 **Modular Design**: Clean, maintainable, and extensible architecture
- ⚙️ **Configurable**: Environment-based configuration for different products
- 🔄 **Repeatable**: Consistent analysis with reproducible results

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Poetry ([installation guide](https://python-poetry.org/docs/#installation))
- OpenAI API key with GPT Vision access

### Installation

1. **Install dependencies**:
   ```bash
   poetry install
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your settings:
   ```bash
   PRODUCT_NAME=your_product_name
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Prepare product images**:
   ```bash
   mkdir -p data/your_product_name
   # Copy your product images to data/your_product_name/
   ```

4. **Run analysis**:
   ```bash
   poetry run python -m product_describer.main
   ```

5. **View results**:
   ```bash
   cat temp/your_product_name/description.yaml
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
| `GPT_MODEL` | No | `gpt-5.2-2025-12-11` | GPT model version |

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
