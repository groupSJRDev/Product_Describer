# Developer Documentation

## Table of Contents
1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Module Documentation](#module-documentation)
4. [Development Workflow](#development-workflow)
5. [Testing](#testing)
6. [Contributing](#contributing)
7. [API Reference](#api-reference)

## Development Setup

### Prerequisites
- Python 3.9 or higher
- Poetry 1.2+
- Git
- OpenAI API key (for testing)

### Initial Setup

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd 2026-01-23_product_describer

# Install dependencies with dev packages
poetry install

# Activate virtual environment
poetry shell

# Install pre-commit hooks (if configured)
pre-commit install
```

### Development Environment

```bash
# Create .env for development
cp .env.example .env

# Add your development API key
echo "OPENAI_API_KEY=sk-..." >> .env
echo "PRODUCT_NAME=test_product" >> .env

# Create test data directory
mkdir -p data/test_product
```

### IDE Setup

#### VS Code
Recommended extensions:
- Python (Microsoft)
- Pylance
- Black Formatter
- autoDocstring

Recommended settings (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true
}
```

#### PyCharm
- Enable Poetry as package manager
- Set Python interpreter to Poetry virtual environment
- Enable pytest as test runner

## Project Structure

```
product-describer/
├── .github/
│   └── copilot-instructions.md   # Project checklist
├── src/
│   └── product_describer/
│       ├── __init__.py           # Package initialization
│       ├── main.py               # Entry point & CLI
│       ├── config.py             # Configuration management
│       ├── image_handler.py      # Image operations
│       └── gpt_analyzer.py       # GPT API integration
├── tests/
│   ├── __init__.py
│   ├── test_main.py              # Main module tests
│   ├── test_config.py            # Config tests (TODO)
│   ├── test_image_handler.py     # Image handler tests (TODO)
│   └── test_gpt_analyzer.py      # GPT analyzer tests (TODO)
├── docs/
│   ├── ARCHITECTURE.md           # System architecture
│   ├── EXECUTION_PLAN.md         # Execution guide
│   └── DEVELOPER.md              # This file
├── data/                         # Input directory (gitignored)
├── temp/                         # Output directory (gitignored)
├── pyproject.toml                # Poetry configuration
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
└── README.md                     # User documentation
```

## Module Documentation

### config.py

#### Class: Config

**Purpose**: Centralized configuration management with validation.

**Key Methods**:

```python
def __init__(self) -> None:
    """Load configuration from environment variables."""

def get_product_data_dir(self) -> Path:
    """Return path to product image directory."""

def get_product_output_dir(self) -> Path:
    """Return path to product output directory."""

def get_output_file_path(self) -> Path:
    """Return full path to output YAML file."""

def validate(self) -> None:
    """Validate all required configuration is present."""
```

**Usage Example**:
```python
from product_describer.config import Config

config = Config()
config.validate()  # Raises ValueError if invalid

data_dir = config.get_product_data_dir()
output_file = config.get_output_file_path()
```

### image_handler.py

#### Class: ImageHandler

**Purpose**: Handle all image file operations and validation.

**Key Methods**:

```python
def __init__(self, data_dir: Path) -> None:
    """Initialize with data directory path."""

def get_image_files(self) -> List[Path]:
    """Discover all supported image files."""

def encode_image_to_base64(self, image_path: Path) -> str:
    """Encode image to base64 string."""

def get_image_info(self, image_path: Path) -> dict:
    """Extract image metadata."""

def validate_images(self) -> tuple[List[Path], List[str]]:
    """Validate all images, return valid paths and errors."""
```

**Usage Example**:
```python
from pathlib import Path
from product_describer.image_handler import ImageHandler

handler = ImageHandler(Path("data/product_name"))
valid_images, errors = handler.validate_images()

for image_path in valid_images:
    info = handler.get_image_info(image_path)
    print(f"{info['filename']}: {info['size']}")
```

### gpt_analyzer.py

#### Class: GPTAnalyzer

**Purpose**: Interface with OpenAI GPT Vision API.

**Key Methods**:

```python
def __init__(self, api_key: str, model: str = "gpt-5.2-2025-12-11") -> None:
    """Initialize with API credentials."""

def analyze_product(self, image_paths: List[Path], product_name: str) -> dict:
    """Send images to GPT and return parsed analysis."""

def _encode_image(self, image_path: Path) -> str:
    """Encode single image to base64."""

def _get_image_mime_type(self, image_path: Path) -> str:
    """Determine MIME type from extension."""

def _extract_yaml_from_response(self, response: str) -> str:
    """Parse YAML content from GPT response."""
```

**Usage Example**:
```python
from product_describer.gpt_analyzer import GPTAnalyzer

analyzer = GPTAnalyzer(api_key="sk-...", model="gpt-5.2-2025-12-11")
result = analyzer.analyze_product(
    image_paths=[Path("image1.jpg"), Path("image2.jpg")],
    product_name="Test Product"
)
```

### main.py

**Purpose**: Application entry point and orchestration.

**Key Function**:

```python
def main() -> None:
    """Main application flow."""
```

**Flow**:
1. Load and validate configuration
2. Initialize image handler
3. Discover and validate images
4. Initialize GPT analyzer
5. Analyze product
6. Save results
7. Display preview

## Development Workflow

### Adding New Features

1. **Create Feature Branch**
```bash
git checkout -b feature/new-feature-name
```

2. **Write Tests First (TDD)**
```python
# tests/test_new_feature.py
def test_new_feature():
    # Arrange
    ...
    # Act
    ...
    # Assert
    ...
```

3. **Implement Feature**
```python
# src/product_describer/new_module.py
def new_feature():
    """Implement feature."""
    ...
```

4. **Run Tests**
```bash
poetry run pytest tests/test_new_feature.py -v
```

5. **Format and Lint**
```bash
poetry run black src/ tests/
poetry run flake8 src/ tests/
poetry run mypy src/
```

6. **Commit Changes**
```bash
git add .
git commit -m "feat: add new feature description"
```

### Code Style Guidelines

#### Python Style
- Follow PEP 8
- Use Black for formatting (line length: 88)
- Use type hints for all function signatures
- Write docstrings for all public functions/classes

#### Documentation
- Use Google-style docstrings
- Include examples for complex functions
- Keep documentation up-to-date with code changes

#### Example Function:
```python
def process_image(image_path: Path, resize: bool = False) -> dict:
    """Process a single image file.
    
    Args:
        image_path: Path to the image file.
        resize: Whether to resize the image.
        
    Returns:
        Dictionary containing processed image metadata.
        
    Raises:
        ValueError: If image file is invalid.
        
    Example:
        >>> result = process_image(Path("photo.jpg"), resize=True)
        >>> print(result['size'])
        (800, 600)
    """
    ...
```

### Git Commit Convention

Use conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```bash
git commit -m "feat(analyzer): add support for custom prompts"
git commit -m "fix(config): handle missing env file gracefully"
git commit -m "docs(architecture): update component diagram"
```

## Testing

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_config.py           # Config module tests
├── test_image_handler.py    # Image handler tests
├── test_gpt_analyzer.py     # GPT analyzer tests
└── test_main.py             # Integration tests
```

### Writing Tests

#### Unit Tests
```python
import pytest
from pathlib import Path
from product_describer.config import Config

def test_config_loads_env_variables(monkeypatch):
    """Test configuration loads from environment."""
    monkeypatch.setenv("PRODUCT_NAME", "test_product")
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    
    config = Config()
    
    assert config.product_name == "test_product"
    assert config.openai_api_key == "test_key"

def test_config_validation_fails_without_product_name():
    """Test validation raises error when PRODUCT_NAME missing."""
    config = Config()
    config.product_name = None
    
    with pytest.raises(ValueError, match="PRODUCT_NAME.*required"):
        config.validate()
```

#### Fixtures
```python
# conftest.py
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_image(temp_data_dir):
    """Create a sample test image."""
    from PIL import Image
    
    img = Image.new('RGB', (100, 100), color='red')
    img_path = temp_data_dir / "test.jpg"
    img.save(img_path)
    
    return img_path
```

#### Mocking External APIs
```python
from unittest.mock import Mock, patch

def test_analyze_product_calls_api(monkeypatch):
    """Test GPT analyzer calls OpenAI API correctly."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices[0].message.content = "key: value"
    mock_client.chat.completions.create.return_value = mock_response
    
    with patch('product_describer.gpt_analyzer.OpenAI', return_value=mock_client):
        analyzer = GPTAnalyzer(api_key="test_key")
        result = analyzer.analyze_product([Path("test.jpg")], "product")
        
        assert mock_client.chat.completions.create.called
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_config.py

# Run with coverage
poetry run pytest --cov=product_describer --cov-report=html

# Run with verbose output
poetry run pytest -v

# Run only fast tests (skip slow integration tests)
poetry run pytest -m "not slow"

# Run tests in parallel
poetry run pytest -n auto
```

### Test Coverage Goals
- Minimum 80% overall coverage
- 100% coverage for critical paths (config, validation)
- All error paths tested

## Contributing

### Pull Request Process

1. Update tests for any changed functionality
2. Ensure all tests pass: `poetry run pytest`
3. Update documentation if needed
4. Format code: `poetry run black .`
5. Check linting: `poetry run flake8 .`
6. Update CHANGELOG.md with changes
7. Submit PR with clear description

### Code Review Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] No unnecessary dependencies added
- [ ] Error handling implemented
- [ ] Type hints added
- [ ] Docstrings present

## API Reference

### Configuration Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PRODUCT_NAME` | Yes | - | Product identifier for directories |
| `OPENAI_API_KEY` | Yes | - | OpenAI API authentication key |
| `GPT_MODEL` | No | `gpt-5.2-2025-12-11` | GPT model version to use |

### Supported Image Formats

- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- GIF (`.gif`)
- WebP (`.webp`)

### Output YAML Schema

Expected structure (varies by product):

```yaml
product_type: string
brand: string
materials:
  - string
colors:
  - string
dimensions:
  length: string
  width: string
  height: string
key_features:
  - string
design_elements:
  - string
condition: string
target_audience: string
use_cases:
  - string
unique_characteristics:
  - string
```

## Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

#### Issue: Images not found
```bash
# Check directory structure
ls -la data/
ls -la data/$PRODUCT_NAME/

# Verify permissions
chmod 755 data/
```

#### Issue: API timeout
```python
# Increase timeout in gpt_analyzer.py
self.client = OpenAI(api_key=api_key, timeout=60.0)
```

#### Issue: YAML parsing fails
```python
# Add error handling
try:
    product_data = yaml.safe_load(yaml_text)
except yaml.YAMLError as e:
    logger.error(f"YAML parsing failed: {e}")
    # Fallback to raw text
```

## Performance Optimization

### Image Optimization
```python
from PIL import Image

def optimize_image(image_path: Path, max_size: int = 2048) -> Path:
    """Resize large images before processing."""
    with Image.open(image_path) as img:
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size))
            img.save(image_path)
    return image_path
```

### Batch Processing
```python
def process_multiple_products(product_names: List[str]) -> None:
    """Process multiple products sequentially."""
    for product_name in product_names:
        os.environ['PRODUCT_NAME'] = product_name
        main()
```

## Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Black Code Formatter](https://black.readthedocs.io/)

## Getting Help

- Check existing documentation in `/docs`
- Review test files for usage examples
- Check GitHub issues for known problems
- Contact maintainers for support
