# Analysis Templates

This directory contains YAML templates for structured product analysis.

## Available Templates

### product_analysis_v1.0.yaml

The primary template for product analysis using GPT Vision. This template provides:

- **Metadata**: Version info, product name, analysis date, image count, overall confidence
- **Dimensions**: Width, height, depth measurements with confidence scores and measurement basis
- **Geometry**: Corner radii, edge shapes, thickness measurements, symmetry analysis
- **Colors**: Primary, secondary, accent colors with hex codes and coverage percentages
- **Materials**: Material type, finish, optical properties, surface texture
- **Labels**: Dimensions, placement, content, style information
- **Deformation**: Shape changes when filled/empty (for flexible products)
- **Keypoints**: Silhouette points and feature locations
- **Analysis Notes**: Challenges, assumptions, conflicts, recommendations
- **Uncertainty**: Confidence tracking for validation needs

## Usage

The template is automatically loaded by `TemplateManager` when template-based analysis is enabled:

```python
from product_describer.gpt_analyzer import GPTAnalyzer

# Template-based analysis (default)
analyzer = GPTAnalyzer(api_key="...", use_template=True, template_version="1.0")

# Free-form analysis (original approach)
analyzer = GPTAnalyzer(api_key="...", use_template=False)
```

## Template Structure

Each template includes:

1. **Null values**: Indicate fields that need to be filled
2. **Confidence scores**: 0.0-1.0 scale for uncertain measurements
3. **Measurement basis**: Explanation of how values were determined
4. **Consistent units**: mm for dimensions, hex codes for colors, ISO 8601 for dates

## Version History

- **v1.0** (2026-01-26): Initial template with comprehensive product analysis fields
