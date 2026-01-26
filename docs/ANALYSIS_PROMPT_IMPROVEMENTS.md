# Analysis Prompt Improvements for GPT Vision

## Overview

This document outlines potential improvements for the GPT Vision analysis prompt (in `gpt_analyzer.py`) that generates detailed YAML specifications from product images. These are untested hypotheses that could be implemented and A/B tested against the current approach.

**Note**: This is separate from the generation prompt used by Nano Banana Pro. For generation prompt improvements, see `GENERATION_PROMPT_IMPROVEMENTS.md`.

---

## 1. Structured Constraint Hierarchy

### Current Approach
All YAML specifications sent in a single block with equal implicit weight.

### Proposed Improvement
```
CRITICAL CONSTRAINTS (MUST MATCH):
- Width: 8.5 inches (215.9mm)
- Height: 10.25 inches (260.35mm)
- Corner radius: 0.777 inches (19.74mm)
- Body color (aqua): #D9E7EF
- Material: Silicone with 55-75% translucency

HIGH PRIORITY CONSTRAINTS (SHOULD MATCH):
- Top edge arch: 0.413 inch rise
- Side taper: 2.75-3.54 degrees inward
- Rim thickness: 2.5-4.5mm
- Refractive index: 1.40-1.43

NICE-TO-HAVE DETAILS:
- Subtle material wrinkles
- Edge highlight behavior
- ...
```

**Rationale**: 
- Hierarchical constraints help models prioritize when trade-offs are necessary
- Critical dimensions get explicit "MUST MATCH" emphasis
- Reduces cognitive load by categorizing 100+ specs into importance tiers

**Testing Approach**: Generate same product with flat specs vs hierarchical, measure dimensional accuracy

---

## 2. Numerical Tolerance Bands

### Current Approach
Exact values provided (e.g., "0.777 inches")

### Proposed Improvement
```yaml
corner_fillet_radius:
  target: 0.777 inches (19.74mm)
  acceptable_range: [0.70, 0.85] inches
  critical: true
  error_tolerance: ±5%
```

**Rationale**:
- AI models struggle with exact numerical precision
- Explicit tolerance bands define "good enough"
- Prevents model from over-indexing on impossible precision

**Trade-off**: May reduce precision if model interprets as "permission to be loose"

---

## 3. Reference-Point Anchoring

### Current Approach
Measurements given in isolation

### Proposed Improvement
```
ANCHOR MEASUREMENTS (verify these first):
1. Overall width MUST be 8.5" - measure this against reference image width
2. Overall height MUST be 10.25" - height/width ratio is 1.206
3. Corner radius is 9.1% of total width (0.777" / 8.5" = 0.091)

All other measurements scale from these anchors.
```

**Rationale**:
- Establishes spatial reference frame
- Ratios are often more accurate than absolute values
- Mimics how humans verify drawings (check overall proportions first)

---

## 4. Visual Verification Instructions

### Current Approach
Implicit expectation that model follows specs

### Proposed Improvement
```
GENERATION VERIFICATION CHECKLIST:
After generating, verify:
□ Width/height ratio is 0.829 (slightly wider than tall)
□ Top edge shows visible arch (not straight)
□ Corners are rounded, not sharp 90° angles
□ Material appears translucent (contents visible but softened)
□ Color matches hex #D9E7EF (light blue-grey)
□ No measurement callouts or dimension lines visible

If any checkbox fails, regenerate with corrections.
```

**Rationale**:
- Some models perform better with self-verification instructions
- Explicit checklist format may trigger internal validation loops
- Provides model with "test cases" for its own output

**Risk**: May not work if model doesn't actually perform verification

---

## 5. Negative Examples with Contrast

### Current Approach
"DO NOT deviate from specifications"

### Proposed Improvement
```
COMMON ERRORS TO AVOID:
❌ Making corners sharp 90° angles (they should be 0.777" radius)
❌ Straight top edge (it should arch upward 0.413")
❌ Perfectly rectangular silhouette (sides taper inward 3° on average)
❌ Opaque material (should be 55-75% translucent, contents visible)
❌ Bright blue color (should be subtle #D9E7EF, almost grey-blue)
❌ Adding dimension callouts or measurements to the image

CORRECT APPROACH:
✓ Soft, rounded corners with visible curvature
✓ Gentle arch at top edge (higher in center)
✓ Slight trapezoidal taper (wider at top than bottom)
✓ Milky translucent material (can see through but blurred)
✓ Subtle aqua tint, not vibrant blue
✓ Clean product image without annotations
```

**Rationale**:
- Contrast learning (what NOT to do vs what TO do)
- Addresses common failure modes explicitly
- Visual descriptors alongside numbers ("subtle aqua" vs just "#D9E7EF")

---

## 6. Multi-Pass Generation Instructions

### Current Approach
Single-shot generation

### Proposed Improvement
```
GENERATION STRATEGY:
Pass 1: Generate base silhouette and overall proportions
  - Focus: Width, height, corner radii, edge arch
  - Ignore: Fine details, colors, materials
  
Pass 2: Apply material properties
  - Focus: Translucency, color (#D9E7EF), optical properties
  - Maintain: Geometry from Pass 1
  
Pass 3: Add scene context and lighting
  - Focus: {custom_prompt} requirements
  - Maintain: Geometry and material from Pass 1 & 2
```

**Rationale**:
- Decomposition into sequential sub-tasks
- Reduces complexity at each step
- Similar to how human artists work (sketch → render → light)

**Challenge**: Current API may not support multi-pass; would need implementation changes

---

## 7. Measurement Anchoring with Reference Scale

### Current Approach
Measurements alone

### Proposed Improvement
```
SCALE REFERENCE:
Using the reference image as ground truth:
- If reference image is 1190 pixels wide
- And actual product is 8.5 inches wide
- Then scale factor is: 140 pixels/inch

Apply this scale to generate:
- Corner radius: 0.777 in × 140 px/in = 109 pixels
- Top arch rise: 0.413 in × 140 px/in = 58 pixels
- Rim thickness: 3.5mm ≈ 0.138 in × 140 px/in = 19 pixels
```

**Rationale**:
- Bridges gap between abstract measurements and pixel space
- Model may work better with pixel dimensions
- Leverages reference image as calibration standard

**Risk**: Assumes model understands pixel-to-measurement mapping

---

## 8. Material Recipe Format

### Current Approach
Optical properties as isolated YAML values

### Proposed Improvement
```
MATERIAL SHADER RECIPE (implement as PBR material):

Base Layer:
- Albedo: #D9E7EF (sRGB)
- Roughness: 0.45 (semi-matte finish)
- Metallic: 0.0 (non-metallic)

Transmission:
- IOR (Index of Refraction): 1.42 (silicone-typical)
- Transmission: 0.65 (65% light passes through)
- Transmission Color: Slight blue shift (RGB delta: [-1, +7, +12])

Subsurface Scattering:
- Enabled: Yes
- Radius: 2.5mm
- Color: #E6F2F7 (milky blue-white)

Specular:
- Intensity: 0.5
- Tint: Neutral white

Think of this like gummy candy or frosted glass - light passes through but diffuses, 
making contents visible but softened.
```

**Rationale**:
- PBR (Physically Based Rendering) terminology may align with model's training
- Analogies ("like gummy candy") provide intuitive understanding
- Recipe format suggests implementation steps

---

## 9. Failure Mode Pre-Correction

### Current Approach
Generate once, hope for accuracy

### Proposed Improvement
```
KNOWN FAILURE MODES & PRE-CORRECTIONS:

Issue: AI often makes products too vibrant/saturated
→ Pre-correction: Emphasize "subtle", "muted", "desaturated" for color #D9E7EF

Issue: Corners often too sharp or too rounded
→ Pre-correction: "Corner radius is 0.777" (9.1% of width), between sharp and fully rounded

Issue: Translucency often too opaque or too transparent
→ Pre-correction: "65% translucent - you can see shapes through it but not fine details"

Issue: Dimensions often drift from specifications
→ Pre-correction: "Width-to-height ratio is 0.829 - verify this visually"

Issue: Scene context overrides product specs
→ Pre-correction: Product specifications are mandatory; {custom_prompt} only affects context
```

**Rationale**:
- Proactive correction based on observed failure patterns
- "Pre-debugs" the generation before it happens
- Provides specific guardrails for known weak points

---

## 10. Comparative Reference Points

### Current Approach
Absolute specifications only

### Proposed Improvement
```
COMPARATIVE REFERENCES (for intuition):

Size comparison:
- Approximately the size of a large dinner plate (8.5" × 10.25")
- Similar dimensions to a standard paper tablet

Corner radius comparison:
- 0.777" radius ≈ size of a U.S. nickel (21mm diameter)
- Not as rounded as a corner of an iPhone, but more than a credit card

Material comparison:
- Transparency like a frosted ziplock bag (not clear, not opaque)
- Flexibility like a thick silicone phone case
- Color like faded sea glass or pale morning sky

Translucency comparison:
- Similar to wax paper - you can see shapes through it but not read text
- Like looking through a shower door with frosted glass
```

**Rationale**:
- Real-world comparisons provide intuitive understanding
- Humans use analogies; models may benefit too
- Bridges abstract specs with familiar objects

---

## 11. Constraint-Satisfaction Framing

### Current Approach
"Follow these specifications"

### Proposed Improvement
```
SOLVE FOR: Generate image that satisfies ALL constraints simultaneously

HARD CONSTRAINTS (must be true):
- width = 8.5" ± 0.1"
- height = 10.25" ± 0.1"
- color_hex = #D9E7EF ± 5% per channel
- translucency > 50% AND < 80%

SOFT CONSTRAINTS (optimize for):
- minimize deviation from corner_radius = 0.777"
- maximize match to reference image texture
- maximize scene composition quality from {custom_prompt}

If hard constraints conflict with soft constraints, 
ALWAYS prioritize hard constraints.
```

**Rationale**:
- Frames task as mathematical constraint satisfaction
- Explicit hard/soft distinction prevents compromises on critical specs
- May align with how model performs optimization

---

## 12. Step-by-Step Reasoning Prompt

### Current Approach
Direct generation request

### Proposed Improvement
```
GENERATION REASONING (think through this before generating):

Step 1: Analyze reference image
- What is the aspect ratio? (should be 0.829)
- What is the corner curvature? (should be 0.777" radius)
- What is the material appearance? (translucent silicone)

Step 2: Map specifications to visual features
- 8.5" × 10.25" → slightly wider than tall
- #D9E7EF → very pale blue-grey, almost neutral
- 65% translucent → can see through but blurred

Step 3: Plan composition for {custom_prompt}
- Where should product be positioned?
- What lighting achieves translucency + clarity?
- How to show requested scene elements?

Step 4: Generate image applying all above

Step 5: Mental verification
- Do dimensions match 8.5" × 10.25"?
- Is color #D9E7EF (not bright blue)?
- Is material translucent (not opaque)?
```

**Rationale**:
- Chain-of-thought prompting improves reasoning in LLMs
- May improve visual reasoning in multimodal models
- Forces systematic approach rather than intuitive generation

**Risk**: May not work if model doesn't actually "think" through steps

---

## 13. Numerical Precision Explicit Format

### Current Approach
Mixed units and formats

### Proposed Improvement
```
MEASUREMENTS (all values in inches, 3 decimal precision):

width: 8.500
height: 10.250
corner_radius_top_left: 0.777
corner_radius_top_right: 0.777
corner_radius_bottom_left: 0.750
corner_radius_bottom_right: 0.750
top_edge_arch_rise: 0.413

COLOR (hex format, sRGB color space):
body_primary: #D9E7EF
rim_band: #D6DFE3

MATERIAL (decimal 0.0-1.0 range):
translucency: 0.650
roughness: 0.450
ior: 1.420
```

**Rationale**:
- Consistent precision (3 decimals) reduces ambiguity
- Uniform unit system (inches only) prevents conversion errors
- Explicit ranges (0.0-1.0) set clear bounds

---

## 14. Anti-Hallucination Constraints

### Current Approach
"DO NOT add details"

### Proposed Improvement
```
PERMITTED ELEMENTS (only these may appear):
✓ The product itself (stasher bag)
✓ Contents as specified in {custom_prompt}
✓ Background as specified in {custom_prompt}
✓ Lighting/shadows from scene
✓ Surface the product rests on

PROHIBITED ELEMENTS (must NOT appear):
✗ Dimension lines, measurements, rulers, or annotations
✗ Additional logos or text not on product
✗ Additional products or variants
✗ Hands, people, or body parts (unless in {custom_prompt})
✗ Packaging, boxes, or tags
✗ Watermarks or digital artifacts
✗ Any elements not explicitly requested

LOGO CONSTRAINT:
- Only "stasher" logo permitted
- Must appear in lower-left quadrant
- Size: 16-22% of product width
- Color: #E6F3F6 (subtle light text)
- No other text or branding
```

**Rationale**:
- Whitelist approach (what's allowed) vs blacklist (what's forbidden)
- Explicit logo constraints prevent creative embellishment
- Addresses specific hallucination patterns observed

---

## 15. Multi-Reference Synthesis

### Current Approach
Single reference image

### Proposed Improvement
```
REFERENCE IMAGES (synthesize features from multiple views):

Image 1 (front view): Use for:
- Overall proportions
- Label placement and design
- Front surface texture

Image 2 (3/4 view): Use for:
- Depth/thickness information
- 3D form understanding
- Material translucency

Image 3 (top view): Use for:
- Top edge arch curvature
- Corner radius verification
- Width taper at closure

Image 4 (dimension callout): Use for:
- Exact measurements (8.5" × 10.25")
- Scale calibration
- Proportion verification

Generate final image synthesizing all reference views 
while maintaining dimension specifications.
```

**Rationale**:
- Multiple views provide richer information
- Explicit view-to-feature mapping guides synthesis
- Reduces ambiguity from single-view limitations

**Implementation**: Requires API support for multiple reference images

---

## Testing & Validation Framework

### Proposed A/B Testing Approach

1. **Baseline**: Current prompt structure
2. **Variants**: Each improvement tested individually
3. **Metrics**:
   - Dimensional accuracy (measure output vs specs)
   - Color fidelity (hex code deviation)
   - Material realism (human evaluation)
   - Constraint adherence (pass/fail checklist)
   - Scene composition quality (human evaluation)

4. **Test Set**: 3-5 products with varying complexity
5. **Sample Size**: 10 generations per variant per product

### Measurement Tools

- Image analysis scripts to measure dimensions from output
- Color histograms to verify hex code matching
- Human evaluation rubric (1-5 scale on multiple dimensions)
- Side-by-side comparison interface

---

## Priority Recommendations

### High Priority (Test First)
1. **Structured Constraint Hierarchy** - Easy to implement, likely high impact
2. **Negative Examples with Contrast** - Addresses observed failure modes
3. **Visual Verification Instructions** - Low cost, potential high benefit

### Medium Priority
4. **Numerical Tolerance Bands** - May help with precision expectations
5. **Comparative Reference Points** - Provides intuitive understanding
6. **Anti-Hallucination Constraints** - Reduces unwanted elements

### Low Priority (Higher Risk/Complexity)
7. **Multi-Pass Generation** - Requires implementation changes
8. **Step-by-Step Reasoning** - Unknown if effective for image models
9. **Multi-Reference Synthesis** - Needs API support

---

## Combination Strategies

Rather than single improvements, consider combinations:

**Precision Stack**:
- Structured Constraint Hierarchy
- Numerical Tolerance Bands  
- Visual Verification Instructions

**Failure Prevention Stack**:
- Negative Examples with Contrast
- Failure Mode Pre-Correction
- Anti-Hallucination Constraints

**Intuition Stack**:
- Comparative Reference Points
- Material Recipe Format
- Reference-Point Anchoring

Test combinations after individual variants are validated.

---

## Long-Term Improvements

### Fine-Tuning Approach
If generation patterns are consistently inaccurate:
- Collect dataset of (prompt, YAML spec, generated image, ground truth)
- Fine-tune Gemini on product reconstruction task
- Evaluate against held-out test set

### Hybrid Approach
Combine AI generation with procedural adjustments:
- Generate initial image with Nano Banana Pro
- Post-process with CV to verify dimensions
- Apply programmatic corrections to adjust color/geometry
- Return corrected image

### Iterative Refinement
- Generate image
- Measure vs specifications
- Create "correction prompt" highlighting deviations
- Regenerate with corrections
- Repeat until within tolerance

---

## Success Metrics

Define "success" before testing:
- **Dimensional Accuracy**: <5% deviation from specified measurements
- **Color Fidelity**: ΔE < 5 (perceptually similar)
- **Constraint Adherence**: 90% of checklist items pass
- **Material Realism**: >4.0/5.0 average human rating
- **Scene Quality**: >3.5/5.0 average for custom prompt execution

---

## Notes

- These are hypotheses, not proven improvements
- Some may reduce accuracy or have no effect
- Systematic testing required before production use
- Model updates may change effectiveness over time
- Cost/benefit should be evaluated (token count vs accuracy gain)

**Next Steps**: Implement baseline measurement, then A/B test top 3 priority improvements.
