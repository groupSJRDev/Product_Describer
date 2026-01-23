"""GPT-based product analysis."""

import base64
from pathlib import Path
from typing import List

from openai import OpenAI
import yaml


class GPTAnalyzer:
    """Analyze product images using GPT vision."""
    
    SYSTEM_PROMPT = """You are a technical product analysis expert specializing in detailed specifications for 3D rendering and product reconstruction. Your analysis will guide AI image generation tools like Nano Banana Pro in accurately recreating products.

Analyze the provided product images with EXTREME precision and provide highly technical measurements and specifications.

CRITICAL REQUIREMENTS - Include all applicable details:

**GEOMETRY & DIMENSIONS:**
- Exact width-to-height ratios (e.g., 1:2.5)
- Depth-to-width ratios
- Precise angles of ALL curves (in degrees where possible)
- Radius measurements for rounded edges
- Curvature descriptions (convex/concave, degree of curve)
- Taper angles if applicable
- Thickness of materials (estimated in mm or inches)

**MATERIALS & PHYSICAL PROPERTIES:**
- Material composition (glass, plastic, metal, paper, fabric, etc.)
- Material finish (matte, glossy, semi-gloss, textured)
- Transparency level (opaque, translucent, transparent, percentage if measurable)
- Material elasticity/stretch properties (if applicable: rigid, flexible, stretchable - include stretch percentage if visible)
- Surface texture details (smooth, rough, embossed, grain pattern)
- Material thickness/gauge

**OPTICAL PROPERTIES:**
- Light refraction characteristics (how light bends through material)
- Reflection properties (specular, diffuse, percentage of reflectivity)
- Color of light passing through transparent/translucent materials
- Shadow characteristics cast by the product
- Highlights and how light interacts with surfaces

**COLOR SPECIFICATIONS (CRITICAL):**
- All visible colors in HEX format (e.g., #FF5733)
- Primary color hex codes
- Secondary/accent color hex codes
- Label colors in hex
- Liquid/content colors in hex (if applicable)
- Gradient information (if colors transition: start hex, end hex, direction)
- Metallic/reflective surface color codes
- Any color variations across the product

**LABELS & GRAPHICS:**
- Label material (paper, vinyl, metallic foil, printed directly, etc.)
- Label dimensions relative to product (e.g., "covers 60% of front face, 80mm wide on 120mm bottle")
- Label placement (exact position, wrap-around percentage)
- Label finish (matte, glossy, holographic, textured)
- Text size ratios
- Graphic element positions and sizes
- Logo dimensions and placement

**LIQUIDS (if applicable):**
- Liquid fill level (percentage and ratio)
- Liquid color (hex code)
- Liquid opacity/transparency
- Viscosity indicators (thin, thick, syrupy)
- Surface tension visibility (meniscus shape)

**PROPORTIONS & RELATIONSHIPS:**
- Part-to-whole ratios for all components
- Cap-to-body ratio (if applicable)
- Base-to-body width ratios
- Component hierarchy and relative sizing

**CONSTRUCTION DETAILS:**
- Assembly method indicators (welded, glued, threaded, snap-fit)
- Seam locations and types
- Connection points between components
- Structural support elements

Provide your analysis in a structured YAML format. Be EXTREMELY specific with measurements, ratios, angles, and hex color codes. If you cannot measure something exactly, provide your best technical estimate with qualifiers. Every measurement matters for accurate reconstruction."""
    
    def __init__(self, api_key: str, model: str = "gpt-5.2-2025-12-11"):
        """Initialize GPT analyzer.
        
        Args:
            api_key: OpenAI API key.
            model: GPT model to use for analysis.
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            Base64 encoded string.
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def _get_image_mime_type(self, image_path: Path) -> str:
        """Get MIME type for image.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            MIME type string.
        """
        ext = image_path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return mime_types.get(ext, "image/jpeg")
    
    def analyze_product(self, image_paths: List[Path], product_name: str) -> dict:
        """Analyze product images and return structured data.
        
        Args:
            image_paths: List of paths to product images.
            product_name: Name of the product being analyzed.
            
        Returns:
            Dictionary containing product analysis.
            
        Raises:
            Exception: If GPT API call fails.
        """
        print(f"Analyzing {len(image_paths)} images for product: {product_name}")
        
        # Prepare messages with images
        content = [
            {
                "type": "text",
                "text": f"""Analyze these images of the product '{product_name}' and provide an EXTREMELY detailed technical specification in YAML format.

FOCUS ON TECHNICAL PRECISION FOR 3D RECONSTRUCTION:
- Measure all angles, curves, and proportions
- Provide ALL colors in HEX format
- Calculate width-to-height ratios
- Describe material properties (thickness, stretch, transparency)
- Analyze light refraction and reflection
- Detail label specifications and relationships
- Include liquid properties if applicable

Your output will guide AI image generation, so accuracy and completeness are critical."""
            }
        ]
        
        # Add all images
        for i, image_path in enumerate(image_paths, 1):
            base64_image = self._encode_image(image_path)
            mime_type = self._get_image_mime_type(image_path)
            
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_image}",
                    "detail": "high"
                }
            })
            print(f"  - Added image {i}: {image_path.name}")
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ]
        
        # Call GPT API
        print(f"\nCalling GPT model: {self.model}...")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4000,  # Increased for detailed technical specs
            temperature=0.3,  # Lower temperature for more precise, technical output
        )
        
        # Extract response
        response_text = response.choices[0].message.content
        print("✓ Received response from GPT\n")
        
        # Parse YAML from response
        # GPT might wrap YAML in code blocks, so we need to extract it
        yaml_text = self._extract_yaml_from_response(response_text)
        
        try:
            product_data = yaml.safe_load(yaml_text)
            return product_data
        except yaml.YAMLError as e:
            print(f"Warning: Could not parse response as YAML: {e}")
            print("Returning raw response as text.")
            return {"raw_response": response_text}
    
    def _extract_yaml_from_response(self, response: str) -> str:
        """Extract YAML content from GPT response.
        
        Args:
            response: Raw response from GPT.
            
        Returns:
            Extracted YAML text.
        """
        # Check if response contains YAML code blocks
        if "```yaml" in response:
            start = response.find("```yaml") + 7
            end = response.find("```", start)
            return response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            return response[start:end].strip()
        else:
            return response.strip()
