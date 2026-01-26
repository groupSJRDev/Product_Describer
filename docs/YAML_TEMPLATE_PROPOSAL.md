# YAML Template-Based Analysis Proposal

## Overview

This document proposes a shift from free-form YAML generation to **template-based YAML population**. Instead of asking GPT Vision to create YAML from scratch, we provide a structured template that it fills in with specific values extracted from product images.

**Current Approach**: GPT generates arbitrary YAML structure based on natural language instructions

**Proposed Approach**: GPT receives a pre-defined YAML template and populates specific fields with measured/observed values

---

## Problem Statement

### Current Limitations

1. **Inconsistent Structure**: Each analysis may return different YAML fields/organization
2. **Unpredictable Keys**: Field names vary between runs ("dimensions" vs "measurements" vs "geometry")
3. **Missing Fields**: GPT might omit important sections if not explicitly reminded
4. **Validation Challenges**: Hard to programmatically validate free-form output
5. **Downstream Processing**: Generation prompt must handle arbitrary YAML structures

### Benefits of Template-Based Approach

✅ **Guaranteed Structure**: Same fields every time  
✅ **Easy Validation**: Can schema-validate against template  
✅ **Consistent Parsing**: Downstream code knows exact field locations  
✅ **Guided Analysis**: Template acts as checklist, ensures nothing missed  
✅ **Type Safety**: Can specify expected data types (number, hex, enum, etc.)  
✅ **Version Control**: Template evolution is explicit and trackable  

---

## Proposed YAML Template Structure

### Template Version 1.0

```yaml
# Product Analysis Template v1.0
# Instructions: Fill in all fields with measurements/observations from product images
# Use null for fields that cannot be determined
# Use confidence scores (0.0-1.0) for uncertain measurements

metadata:
  template_version: "1.0"
  product_name: null  # Fill with provided product name
  analysis_date: null  # ISO 8601 format
  image_count: null  # Number of images analyzed
  confidence_overall: null  # 0.0-1.0, overall confidence in analysis

# ============================================================
# SECTION 1: PRIMARY DIMENSIONS
# ============================================================
dimensions:
  primary:
    width:
      value: null  # in mm
      unit: "mm"
      confidence: null  # 0.0-1.0
      measurement_basis: null  # e.g., "front view, pixel measurement"
    
    height:
      value: null  # in mm
      unit: "mm"
      confidence: null
      measurement_basis: null
    
    depth:
      value: null  # in mm
      unit: "mm"
      confidence: null
      measurement_basis: null
  
  aspect_ratios:
    width_to_height: null  # decimal ratio
    depth_to_width: null   # decimal ratio
    
  scale_required: null  # true/false - whether absolute dimensions need external reference

# ============================================================
# SECTION 2: GEOMETRY DETAILS
# ============================================================
geometry:
  corner_radii:
    top_left:
      radius: null  # in mm
      confidence: null
    top_right:
      radius: null
      confidence: null
    bottom_left:
      radius: null
      confidence: null
    bottom_right:
      radius: null
      confidence: null
  
  edges:
    top:
      shape: null  # "straight" | "curved" | "arched"
      curvature_details: null  # description if curved/arched
      deviation: null  # max deviation from straight in mm
    bottom:
      shape: null
      curvature_details: null
      deviation: null
    left:
      shape: null
      curvature_details: null
      deviation: null
    right:
      shape: null
      curvature_details: null
      deviation: null
  
  thickness:
    rim:
      min: null  # in mm
      max: null  # in mm
      average: null  # in mm
    body:
      min: null
      max: null
      average: null
  
  symmetry:
    horizontal: null  # true/false
    vertical: null    # true/false
    asymmetry_notes: null  # description if asymmetric

# ============================================================
# SECTION 3: COLORS
# ============================================================
colors:
  primary:
    hex: null  # e.g., "#D9E7EF"
    rgb: null  # [R, G, B] array
    name: null  # descriptive name, e.g., "aqua teal"
    coverage_percentage: null  # 0-100
    confidence: null
  
  secondary:
    hex: null
    rgb: null
    name: null
    coverage_percentage: null
    confidence: null
  
  accent:
    hex: null
    rgb: null
    name: null
    coverage_percentage: null
    confidence: null
  
  label_colors:
    background: null  # hex
    text: null  # hex
    graphics: []  # array of hex values

# ============================================================
# SECTION 4: MATERIALS
# ============================================================
materials:
  primary_material:
    type: null  # "silicone" | "plastic" | "glass" | "metal" | "paper" | "fabric"
    finish: null  # "matte" | "glossy" | "semi-gloss" | "textured"
    rigidity: null  # "rigid" | "flexible" | "semi-flexible"
    confidence: null
  
  optical_properties:
    transparency:
      type: null  # "opaque" | "translucent" | "transparent"
      percentage: null  # 0-100, if translucent/transparent
      confidence: null
    
    refraction:
      present: null  # true/false
      index_estimate: null  # 1.0-2.0 if measurable
      description: null
    
    reflection:
      type: null  # "none" | "diffuse" | "specular" | "mixed"
      intensity: null  # "low" | "medium" | "high"
      description: null
  
  surface_texture:
    type: null  # "smooth" | "rough" | "embossed" | "grain"
    description: null
    visible_at_scale: null  # true/false

# ============================================================
# SECTION 5: LABELS & GRAPHICS
# ============================================================
labels:
  present: null  # true/false
  
  primary_label:
    material: null  # "printed" | "vinyl" | "embossed" | "molded"
    position: null  # "front" | "back" | "top" | "bottom" | "side"
    dimensions:
      width_mm: null
      height_mm: null
      width_percentage: null  # percentage of product width
      height_percentage: null
    
    placement:
      offset_from_top_mm: null
      offset_from_left_mm: null
      centered_horizontal: null  # true/false
      centered_vertical: null    # true/false
    
    content:
      text_present: null  # true/false
      text_content: null  # actual text if readable
      graphics_present: null  # true/false
      graphics_description: null
      logo_present: null  # true/false
      logo_description: null
    
    style:
      finish: null  # "matte" | "glossy" | "holographic" | "textured"
      colors_used: []  # array of hex values

# ============================================================
# SECTION 6: PHYSICAL BEHAVIOR (for flexible materials)
# ============================================================
deformation:
  applies: null  # true/false - whether product can deform
  
  when_filled:
    shape_change: null  # description
    expansion_areas: []  # list of areas that expand
    constraints: []  # list of areas that don't expand
  
  when_empty:
    resting_shape: null  # description
    folds_or_creases: null  # true/false
    fold_locations: []  # if applicable

# ============================================================
# SECTION 7: KEYPOINTS (for spatial reference)
# ============================================================
keypoints:
  silhouette:
    # Normalized 0.0-1.0 coordinates, origin top-left
    points: []  # array of [x, y] coordinates around outline
    point_count: null
  
  features:
    # Notable feature locations
    - name: null  # e.g., "logo_center"
      x: null  # 0.0-1.0
      y: null  # 0.0-1.0
      description: null

# ============================================================
# SECTION 8: ANALYSIS METADATA
# ============================================================
analysis_notes:
  measurement_challenges: []  # list of difficulties encountered
  assumptions_made: []  # list of assumptions
  cross_image_conflicts: []  # conflicting info between images
  recommended_additional_images: []  # what angles/views would help
  
uncertainty:
  highest_confidence_fields: []  # list of field paths
  lowest_confidence_fields: []  # list of field paths
  fields_requiring_validation: []  # fields that need external verification
```

---

## Implementation Approach

### Phase 1: Template Design

**Goal**: Create production-ready template

**Tasks**:
1. Review existing YAML outputs from current system
2. Identify common fields across products
3. Design flexible template accommodating various product types
4. Add comprehensive comments/instructions
5. Version the template (start at v1.0)

**Deliverable**: `templates/product_analysis_v1.0.yaml`

### Phase 2: Prompt Engineering

**Current Prompt** (simplified):
```
Analyze these images and produce a TECHNICAL RECONSTRUCTION SPEC in YAML.
[... long instructions ...]
```

**New Template-Based Prompt**:
```python
TEMPLATE_BASED_PROMPT = f"""
You are a technical product analyst. You will receive:
1. Product images to analyze
2. A YAML template with predefined structure

Your task: Fill in the template with accurate measurements and observations.

INSTRUCTIONS:
- Preserve the exact template structure
- Fill in all fields you can determine from the images
- Use null for fields you cannot determine
- Add confidence scores (0.0-1.0) for uncertain measurements
- Provide measurement_basis explanations for key dimensions
- Do NOT add fields not in the template
- Do NOT omit template fields (use null if unknown)

TEMPLATE TO FILL:
{yaml_template}

IMAGES TO ANALYZE:
[images attached]

PRODUCT NAME: {product_name}

Return the completed YAML template with all determinable fields filled in.
"""
```

### Phase 3: Template Loading System

**New Module**: `src/product_describer/template_manager.py`

```python
"""Template management for structured product analysis."""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml

class TemplateManager:
    """Manage YAML analysis templates."""
    
    def __init__(self, templates_dir: Path = None):
        self.templates_dir = templates_dir or Path("templates")
    
    def load_template(self, version: str = "1.0") -> str:
        """Load YAML template by version.
        
        Args:
            version: Template version (e.g., "1.0", "2.0")
            
        Returns:
            Template as string
        """
        template_path = self.templates_dir / f"product_analysis_v{version}.yaml"
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template version {version} not found")
        
        with open(template_path, 'r') as f:
            return f.read()
    
    def validate_response(self, response: Dict[str, Any], version: str = "1.0") -> tuple[bool, list[str]]:
        """Validate response against template structure.
        
        Args:
            response: Parsed YAML response from GPT
            version: Template version to validate against
            
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Load expected structure
        template_str = self.load_template(version)
        template = yaml.safe_load(template_str)
        
        # Check all required sections present
        required_sections = self._get_required_sections(template)
        for section in required_sections:
            if section not in response:
                errors.append(f"Missing required section: {section}")
        
        # Validate data types
        type_errors = self._validate_types(response, template)
        errors.extend(type_errors)
        
        return len(errors) == 0, errors
    
    def _get_required_sections(self, template: Dict) -> list[str]:
        """Extract required top-level sections."""
        # Implementation
        pass
    
    def _validate_types(self, response: Dict, template: Dict) -> list[str]:
        """Validate field types match template."""
        # Implementation
        pass
```

### Phase 4: Integration with GPTAnalyzer

**Modified**: `src/product_describer/gpt_analyzer.py`

```python
from product_describer.template_manager import TemplateManager

class GPTAnalyzer:
    def __init__(self, api_key: str, model: str = "gpt-5.2-2025-12-11", 
                 template_version: str = "1.0"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.template_manager = TemplateManager()
        self.template_version = template_version
    
    def analyze_product(self, image_paths: List[Path], product_name: str) -> Dict[str, Any]:
        """Analyze product using template-based approach."""
        
        # Load template
        template_yaml = self.template_manager.load_template(self.template_version)
        
        # Construct prompt with template
        prompt = self._build_template_prompt(template_yaml, product_name)
        
        # ... rest of analysis
        
        # Validate response
        is_valid, errors = self.template_manager.validate_response(
            product_data, 
            self.template_version
        )
        
        if not is_valid:
            logger.warning(f"Template validation errors: {errors}")
            # Could retry or flag for review
        
        return product_data
```

### Phase 5: Schema Validation

**Tool**: Use `pydantic` for runtime validation

```python
from pydantic import BaseModel, Field, confloat
from typing import Optional, List, Literal

class Measurement(BaseModel):
    value: Optional[float]
    unit: str
    confidence: Optional[confloat(ge=0.0, le=1.0)]
    measurement_basis: Optional[str]

class PrimaryDimensions(BaseModel):
    width: Measurement
    height: Measurement
    depth: Measurement

class ColorInfo(BaseModel):
    hex: Optional[str] = Field(regex=r'^#[0-9A-Fa-f]{6}$')
    rgb: Optional[List[int]]
    name: Optional[str]
    coverage_percentage: Optional[confloat(ge=0.0, le=100.0)]
    confidence: Optional[confloat(ge=0.0, le=1.0)]

class ProductAnalysis(BaseModel):
    """Complete product analysis schema."""
    metadata: MetadataSection
    dimensions: DimensionsSection
    geometry: GeometrySection
    colors: ColorsSection
    materials: MaterialsSection
    labels: LabelsSection
    deformation: DeformationSection
    keypoints: KeypointsSection
    analysis_notes: NotesSection

    class Config:
        extra = 'forbid'  # Reject unknown fields
```

---

## Template Versioning Strategy

### Version 1.0 (Initial)
- Core fields for common products
- Focus on rigid products (bottles, boxes, containers)

### Version 1.1 (Flexible Products)
- Enhanced deformation section
- Fabric/textile specific fields
- Wearables support

### Version 2.0 (Advanced Materials)
- Multi-material products
- Complex optical properties
- Composite structures

### Migration Path
```python
def migrate_template(old_version: str, new_version: str, data: dict) -> dict:
    """Migrate data from old template version to new."""
    # Implement migration logic
    pass
```

---

## Advantages Over Free-Form

### 1. Consistency
**Before**: 
```yaml
# Run 1
size:
  w: 100mm
  h: 200mm

# Run 2  
dimensions:
  width: 100
  height: 200
```

**After**:
```yaml
# Always the same structure
dimensions:
  primary:
    width:
      value: 100
      unit: "mm"
```

### 2. Validation
**Before**: Parse unpredictable YAML, hope for the best

**After**: Schema validation, type checking, required field verification

### 3. Guided Analysis
Template serves as checklist—GPT less likely to forget important aspects

### 4. Confidence Tracking
Built-in confidence scores enable downstream decisions

### 5. Null Handling
Explicit nulls better than missing fields—know what GPT couldn't determine

---

## Challenges and Mitigations

### Challenge 1: Template Rigidity

**Problem**: One template may not fit all product types

**Mitigation**: 
- Template versioning
- Product-type-specific templates (template_bottle_v1.0, template_bag_v1.0)
- Optional sections that can be omitted for irrelevant products

### Challenge 2: GPT May Ignore Template

**Problem**: Model might generate different structure despite instructions

**Mitigation**:
- Strong prompt emphasis on structure preservation
- Few-shot examples showing template fill-in
- Response validation and retry logic
- Consider fine-tuning on template-completion task

### Challenge 3: Verbose Templates

**Problem**: Large templates consume token budget

**Mitigation**:
- Remove comments in actual prompt (keep in source)
- Use minimal template (just keys, no descriptions)
- Consider hierarchical analysis (high-level then detail passes)

### Challenge 4: Maintenance Burden

**Problem**: Template updates require coordination

**Mitigation**:
- Semantic versioning
- Migration tools
- Changelog documentation
- Backward compatibility testing

---

## Testing Plan

### Phase 1: Template Design Validation
- [ ] Analyze 10 diverse products with current free-form approach
- [ ] Extract common fields
- [ ] Draft template covering 90%+ of fields
- [ ] Review with stakeholders

### Phase 2: Prompt Engineering Test
- [ ] Test template-based prompt with 5 products
- [ ] Measure GPT's adherence to template structure
- [ ] Refine prompt based on violations
- [ ] Establish baseline compliance rate

### Phase 3: Accuracy Comparison
- [ ] Same 20 products: free-form vs template-based
- [ ] Compare measurement accuracy
- [ ] Compare completeness (fields filled)
- [ ] Compare consistency across runs

### Phase 4: Production Rollout
- [ ] Gradual rollout (20% → 50% → 100%)
- [ ] Monitor validation error rates
- [ ] Collect feedback on downstream usability
- [ ] Iterate on template design

---

## Success Metrics

**Structure Compliance**: >95% of responses match template structure

**Completeness**: >80% of fields filled (non-null)

**Consistency**: <5% variation in same-product repeated analyses

**Validation Pass Rate**: >90% of responses pass schema validation

**Downstream Integration**: 50% reduction in parsing errors

**Maintenance**: <2 hours/month template maintenance

---

## Migration Path

### Option 1: Hard Cutover
- Pick date
- Switch all analysis to template-based
- Update all code simultaneously

**Pros**: Clean, simple  
**Cons**: Risky, potential breakage

### Option 2: Gradual Migration
```python
class GPTAnalyzer:
    def __init__(self, use_template: bool = False):
        self.use_template = use_template
    
    def analyze_product(self, ...):
        if self.use_template:
            return self._template_based_analysis(...)
        else:
            return self._free_form_analysis(...)
```

**Pros**: Safe, testable, reversible  
**Cons**: Maintains two code paths temporarily

### Option 3: Hybrid Approach
- Use template for critical fields
- Allow free-form for product-specific details
```yaml
# Template section
dimensions: {...}
colors: {...}

# Free-form section
custom_observations:
  # GPT can add product-specific fields here
```

---

## Future Enhancements

### 1. Product-Type Detection
```python
def detect_product_type(images: List[Path]) -> str:
    """Use GPT to classify product type first."""
    # Returns: "bottle" | "bag" | "box" | "apparel" | ...
    # Then load appropriate template

template = template_manager.load_template_for_type(product_type)
```

### 2. Interactive Template Builder
Web UI to:
- Preview templates
- Test on sample products
- Generate new templates for product categories
- Version control integration

### 3. Template Marketplace
- Community-contributed templates
- Product-category-specific templates
- Industry-standard templates (packaging, apparel, electronics)

### 4. Multi-Pass Analysis
```
Pass 1: High-level template (dimensions, colors, material)
Pass 2: Detailed template for specific areas
Pass 3: Verification pass
```

### 5. Confidence-Based Re-analysis
```python
if analysis.metadata.confidence_overall < 0.7:
    # Re-analyze with enhanced prompt
    # Focus on low-confidence fields
```

---

## Appendix: Template Design Principles

1. **Hierarchical**: Organize by logical sections
2. **Commented**: Include instructions inline (remove for actual prompt)
3. **Typed**: Specify expected data types
4. **Nullable**: All fields should accept null
5. **Confidence-Tracked**: Include confidence scores for measurements
6. **Basis-Documented**: Ask for measurement source/method
7. **Versioned**: Explicit version field
8. **Extensible**: Allow for future additions
9. **Validatable**: Structure that can be schema-validated
10. **Human-Readable**: Clear field names and organization

---

## Appendix: Example Completed Template

See `examples/completed_template_stasher_bag.yaml` for full example

---

## References

- **Current System**: `src/product_describer/gpt_analyzer.py`
- **Template Location**: `templates/product_analysis_v1.0.yaml`
- **Schema Validation**: `src/product_describer/schemas.py`
- **Related**: `ANALYSIS_PROMPT_IMPROVEMENTS.md`

---

## Changelog

- **2026-01-26**: Initial proposal created
