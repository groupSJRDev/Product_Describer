"""Image generation test using Nano Banana Pro (Gemini 3 Pro Image).

This module generates product images based on technical YAML specifications
using Google's Gemini 3 Pro Image model (Nano Banana Pro).
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import yaml
from PIL import Image

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai package not installed.")
    print("Install it with: poetry add google-genai")
    sys.exit(1)

from product_describer.config import Config
from product_describer.constants import GENERATION_PROMPT_FILENAME
from product_describer.exceptions import ConfigurationError, APIError
from product_describer.logger import setup_logger

logger = setup_logger(__name__)


def load_yaml_specs(yaml_path: Path) -> str:
    """Load YAML specifications and convert to formatted string.

    Args:
        yaml_path: Path to the description YAML file.

    Returns:
        Formatted YAML content as string.

    Raises:
        FileNotFoundError: If YAML file doesn't exist.
        yaml.YAMLError: If YAML file is malformed.
    """
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    # Convert back to YAML string for prompt
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def generate_image_from_specs(
    reference_image_path: Path,
    yaml_specs: str,
    custom_prompt: str,
    output_path: Path,
    api_key: str,
    aspect_ratio: str = "1:1",
    resolution: str = "2K",
) -> None:
    """Generate product image using Nano Banana Pro.

    Args:
        reference_image_path: Path to reference product image.
        yaml_specs: YAML specifications as string.
        custom_prompt: Custom generation prompt.
        output_path: Where to save the generated image.
        api_key: Google API key.
        aspect_ratio: Image aspect ratio (e.g., "1:1", "16:9").
        resolution: Image resolution ("1K", "2K", or "4K").

    Raises:
        APIError: If image generation fails.
        FileNotFoundError: If reference image doesn't exist.
    """
    logger.info("=" * 70)
    logger.info("Nano Banana Pro Image Generation Test")
    logger.info("=" * 70)

    # Initialize client
    client = genai.Client(api_key=api_key)

    # Load reference image
    reference_image = Image.open(reference_image_path)
    logger.info(f"Reference image: {reference_image_path.name}")
    logger.info(f"  Size: {reference_image.size}")

    # Construct the full prompt
    full_prompt = f"""

Please generate product with these exact ratios. 
Exact label of reference.
No metrics on the final image.

{yaml_specs}


Pay special attention to:
- Exact color hex codes
- Material properties (transparency, refraction, reflection)
- Geometry and proportions
- Exact curves and angles
- Optical characteristics

DO NOT deviate from ANY specifications.
DO NOT add details to the product not described.


{custom_prompt}

You must follow all metric descriptions EXACTLY. Product maintains instructed color and exact dimensions.
"""

    logger.info("Generating image with Nano Banana Pro...")
    logger.info(f"  Model: gemini-3-pro-image-preview")
    logger.info(f"  Aspect Ratio: {aspect_ratio}")
    logger.info(f"  Resolution: {resolution}")

    # Generate content
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[full_prompt, reference_image],
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio, image_size=resolution
            ),
        ),
    )

    logger.info("-" * 70)

    # Process response
    image_saved = False
    for part in response.parts:
        if part.text is not None:
            logger.info("Model Response:")
            logger.info(part.text)
        elif image := part.as_image():
            image.save(output_path)
            image_saved = True
            logger.info(f"Generated image saved to: {output_path}")

    if not image_saved:
        logger.warning("No image was generated in the response")

    logger.info("=" * 70)


def main() -> None:
    """Main execution for image generation test."""
    # Load configuration
    config = Config()

    # Check for Gemini API key
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.error("GEMINI_API_KEY environment variable is required")
        logger.info("")
        logger.info("Add to your .env file:")
        logger.info("GEMINI_API_KEY=your_gemini_api_key_here")
        logger.info("")
        logger.info("Get your API key from: https://aistudio.google.com/apikey")
        sys.exit(1)

    if not config.product_name:
        logger.error("PRODUCT_NAME environment variable is required")
        sys.exit(1)

    logger.info(f"Product: {config.product_name}")

    # Check if YAML exists
    yaml_path = config.get_output_file_path()
    if not yaml_path.exists():
        logger.error(f"YAML description not found at {yaml_path}")
        logger.info("")
        logger.info("Run the analysis first:")
        logger.info("  poetry run python -m product_describer.main")
        sys.exit(1)

    # Load YAML specifications
    logger.info(f"Loading specifications from: {yaml_path}")
    yaml_specs = load_yaml_specs(yaml_path)
    logger.info(f"Loaded {len(yaml_specs)} characters of technical specs")

    # Get reference image (use first image from data directory)
    data_dir = config.get_product_data_dir()
    from product_describer.image_handler import ImageHandler

    handler = ImageHandler(data_dir)
    image_files = handler.get_image_files()

    if not image_files:
        logger.error(f"No images found in {data_dir}")
        sys.exit(1)

    reference_image = image_files[0]  # Use first image as reference

    # Load custom prompt from environment variable, file, or use default
    custom_prompt_file = config.get_product_output_dir() / GENERATION_PROMPT_FILENAME
    custom_prompt_env = os.getenv("GENERATION_PROMPT")

    if custom_prompt_env:
        logger.info("Using prompt from GENERATION_PROMPT environment variable")
        custom_prompt = custom_prompt_env
    elif custom_prompt_file.exists():
        logger.info(f"Using prompt from: {custom_prompt_file}")
        with open(custom_prompt_file, "r") as f:
            custom_prompt = f.read().strip()
    else:
        logger.info(
            "Using default prompt (create temp/<PRODUCT_NAME>/generation_prompt.txt to customize)"
        )
        custom_prompt = """Create a professional studio product photograph of this item.
The lighting should be clean and even, showing all details clearly.
The background should be neutral white.
Match the technical specifications exactly, especially colors, materials, and proportions."""

    logger.info("")
    logger.info("Prompt:")
    logger.info("-" * 70)
    logger.info(custom_prompt)
    logger.info("-" * 70)

    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = config.get_product_output_dir() / "test_images"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"generated_{timestamp}.png"

    # Optional: Allow customization via environment variables
    aspect_ratio = os.getenv("IMAGE_ASPECT_RATIO", "1:1")
    resolution = os.getenv("IMAGE_RESOLUTION", "2K")

    try:
        generate_image_from_specs(
            reference_image_path=reference_image,
            yaml_specs=yaml_specs,
            custom_prompt=custom_prompt,
            output_path=output_path,
            api_key=gemini_api_key,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
        )
    except Exception as e:
        logger.error(f"Error during generation: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
