"""GPT-based product analysis."""

import base64
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI
import yaml

from product_describer.constants import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    MAX_RETRY_ATTEMPTS,
    RETRY_BACKOFF_FACTOR,
)
from product_describer.exceptions import APIError, YAMLParsingError
from product_describer.logger import setup_logger
from product_describer.template_manager import TemplateManager

logger = setup_logger(__name__)


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

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5.2-2025-12-11",
        use_template: bool = True,
        template_version: str = "1.0",
    ) -> None:
        """Initialize GPT analyzer.

        Args:
            api_key: OpenAI API key.
            model: GPT model to use for analysis.
            use_template: Whether to use template-based analysis (default: True).
            template_version: Template version to use (default: "1.0").
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.use_template = use_template
        self.template_version = template_version

        if self.use_template:
            self.template_manager = TemplateManager()
            logger.info(f"Template-based analysis enabled (version {template_version})")

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

    def analyze_product(
        self, image_paths: List[Path], product_name: str
    ) -> Dict[str, Any]:
        """Analyze product images and return structured data.

        Args:
            image_paths: List of paths to product images.
            product_name: Name of the product being analyzed.

        Returns:
            Dictionary containing product analysis.

        Raises:
            APIError: If GPT API call fails after retries.
            YAMLParsingError: If response cannot be parsed as YAML.
        """
        logger.info(f"Analyzing {len(image_paths)} images for product: {product_name}")

        if self.use_template:
            return self._template_based_analysis(image_paths, product_name)
        else:
            return self._free_form_analysis(image_paths, product_name)

    def _template_based_analysis(
        self, image_paths: List[Path], product_name: str
    ) -> Dict[str, Any]:
        """Perform template-based analysis.

        Args:
            image_paths: List of paths to product images.
            product_name: Name of the product being analyzed.

        Returns:
            Dictionary containing product analysis.
        """
        logger.info("Using template-based analysis approach")

        # Load template
        template_yaml = self.template_manager.load_template(self.template_version)

        # Build prompt with template
        prompt_content = self._build_template_prompt(
            template_yaml, product_name, len(image_paths)
        )

        # Prepare content with images
        content = self._prepare_content_with_images(image_paths, prompt_content)

        # Call API and get response
        response_text = self._call_gpt_api(content)

        # Parse YAML
        yaml_text = self._extract_yaml_from_response(response_text)
        product_data = self._parse_yaml(yaml_text, response_text)

        # Validate against template
        is_valid, errors = self.template_manager.validate_response(
            product_data, self.template_version
        )

        if not is_valid:
            logger.warning(f"Template validation found {len(errors)} issues:")
            for error in errors[:5]:  # Show first 5 errors
                logger.warning(f"  - {error}")
            if len(errors) > 5:
                logger.warning(f"  ... and {len(errors) - 5} more")

        return product_data

    def _free_form_analysis(
        self, image_paths: List[Path], product_name: str
    ) -> Dict[str, Any]:
        """Perform free-form analysis (original approach).

        Args:
            image_paths: List of paths to product images.
            product_name: Name of the product being analyzed.

        Returns:
            Dictionary containing product analysis.
        """
        logger.info("Using free-form analysis approach")

        # Prepare content with images
        prompt_text = f"""
Analyze these images of the product '{product_name}' and produce a TECHNICAL RECONSTRUCTION SPEC in YAML.

{self.SYSTEM_PROMPT}
"""
        content = self._prepare_content_with_images(image_paths, prompt_text)

        # Call API and get response
        response_text = self._call_gpt_api(content)

        # Parse YAML
        yaml_text = self._extract_yaml_from_response(response_text)
        return self._parse_yaml(yaml_text, response_text)

    def _build_template_prompt(
        self, template_yaml: str, product_name: str, image_count: int
    ) -> str:
        """Build prompt for template-based analysis.

        Args:
            template_yaml: Template YAML string
            product_name: Product name
            image_count: Number of images

        Returns:
            Formatted prompt string
        """
        return f"""
You are a technical product analyst. Analyze the provided product images and fill in the YAML template with accurate measurements and observations.

PRODUCT: {product_name}
IMAGES PROVIDED: {image_count}

CRITICAL INSTRUCTIONS:
1. Preserve the EXACT template structure - do not add or remove fields
2. Fill in all fields you can determine from the images
3. Use null for fields you cannot determine with confidence
4. Provide confidence scores (0.0-1.0) for uncertain measurements
5. Include measurement_basis explanations for key dimensions
6. Use ISO 8601 format for dates (YYYY-MM-DD)
7. Return ONLY the completed YAML - no explanations or commentary

MEASUREMENT GUIDELINES:
- For dimensions: measure in mm unless otherwise specified
- For colors: provide hex codes (e.g., #D9E7EF)
- For confidence: 0.0 = pure guess, 0.5 = somewhat confident, 1.0 = certain
- For ratios: use decimal format (e.g., 1.5 not "3:2")

TEMPLATE TO FILL:
{template_yaml}

Analyze the images carefully and return the completed YAML template.
"""

    def _prepare_content_with_images(
        self, image_paths: List[Path], prompt_text: str
    ) -> List[Dict[str, Any]]:
        """Prepare content list with prompt and images.

        Args:
            image_paths: List of image paths
            prompt_text: Prompt text

        Returns:
            Content list for API call
        """
        content = [{"type": "text", "text": prompt_text}]

        # Add all images
        for i, image_path in enumerate(image_paths, 1):
            base64_image = self._encode_image(image_path)
            mime_type = self._get_image_mime_type(image_path)

            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_image}",
                        "detail": "high",
                    },
                }
            )
            logger.debug(f"Added image {i}: {image_path.name}")

        return content

    def _call_gpt_api(self, content: List[Dict[str, Any]]) -> str:
        """Call GPT API with retry logic.

        Args:
            content: Content to send to API

        Returns:
            Response text from API

        Raises:
            APIError: If API call fails after retries
        """
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ]

        # Call GPT API with retry logic
        logger.info(f"Calling GPT model: {self.model}...")

        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            try:
                # Use max_completion_tokens for newer models (GPT-5.2+)
                if "gpt-5" in self.model or "gpt-6" in self.model:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_completion_tokens=DEFAULT_MAX_TOKENS,
                        temperature=DEFAULT_TEMPERATURE,
                    )
                else:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=DEFAULT_MAX_TOKENS,
                        temperature=DEFAULT_TEMPERATURE,
                    )
                break
            except Exception as e:
                logger.error(f"API call failed on attempt {attempt}: {e}")

                if attempt == MAX_RETRY_ATTEMPTS:
                    raise APIError(
                        f"GPT API call failed after {MAX_RETRY_ATTEMPTS} attempts: {e}"
                    )

                wait_time = RETRY_BACKOFF_FACTOR**attempt
                logger.warning(
                    f"API call attempt {attempt} failed: {e}. Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)

        # Extract and validate response
        response_text = response.choices[0].message.content

        if not response_text:
            logger.error("GPT returned empty response")
            logger.debug(f"Response object: {response}")
            raise APIError("GPT returned empty response")

        logger.info("Received response from GPT")
        logger.debug(f"Response length: {len(response_text)} characters")
        logger.debug("Response preview:")
        logger.debug("-" * 60)
        logger.debug(response_text[:500])
        logger.debug("-" * 60)

        return response_text

    def _parse_yaml(self, yaml_text: str, original_response: str) -> Dict[str, Any]:
        """Parse YAML text into dictionary.

        Args:
            yaml_text: YAML text to parse
            original_response: Original response for fallback

        Returns:
            Parsed YAML as dictionary

        Raises:
            YAMLParsingError: If YAML cannot be parsed
        """
        if not yaml_text or yaml_text.strip() == "":
            logger.error("Extracted YAML text is empty")
            logger.debug(f"Original response:\n{original_response}")
            raise YAMLParsingError("Could not extract YAML from GPT response")

        try:
            product_data = yaml.safe_load(yaml_text)

            if product_data is None:
                logger.error("YAML parsed to None")
                logger.debug(f"YAML text:\n{yaml_text}")
                raise YAMLParsingError("YAML parsing resulted in None")

            # Add analysis timestamp if template-based and metadata exists
            if self.use_template and "metadata" in product_data:
                if product_data["metadata"].get("analysis_date") is None:
                    product_data["metadata"]["analysis_date"] = datetime.now().strftime(
                        "%Y-%m-%d"
                    )

            return product_data
        except yaml.YAMLError as e:
            logger.error(f"Could not parse response as YAML: {e}")
            logger.debug(f"YAML text:\n{yaml_text}")
            logger.warning("Returning raw response as text.")
            return {"raw_response": original_response}

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
