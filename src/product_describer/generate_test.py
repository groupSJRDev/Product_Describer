"""Image generation test using Nano Banana Pro (Gemini 3 Pro Image).

This module generates product images based on technical YAML specifications
using Google's Gemini 3 Pro Image model (Nano Banana Pro).
"""

import os
import sys
from pathlib import Path
from datetime import datetime

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


def load_yaml_specs(yaml_path: Path) -> str:
    """Load YAML specifications and convert to formatted string.
    
    Args:
        yaml_path: Path to the description YAML file.
        
    Returns:
        Formatted YAML content as string.
    """
    with open(yaml_path, 'r') as f:
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
    resolution: str = "2K"
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
    """
    print("=" * 70)
    print("Nano Banana Pro Image Generation Test")
    print("=" * 70)
    print()
    
    # Initialize client
    client = genai.Client(api_key=api_key)
    
    # Load reference image
    reference_image = Image.open(reference_image_path)
    print(f"Reference image: {reference_image_path.name}")
    print(f"  Size: {reference_image.size}")
    print()
    
    # Construct the full prompt
    full_prompt = f"""{custom_prompt}

TECHNICAL SPECIFICATIONS (Use these for accuracy):

{yaml_specs}

Generate a high-fidelity product image following the technical specifications above. 
Pay special attention to:
- Exact color hex codes
- Material properties (transparency, refraction, reflection)
- Geometry and proportions
- Curves and angles
- Optical characteristics

Create a professional product photograph that matches these precise specifications."""
    
    print("Generating image with Nano Banana Pro...")
    print(f"  Model: gemini-3-pro-image-preview")
    print(f"  Aspect Ratio: {aspect_ratio}")
    print(f"  Resolution: {resolution}")
    print()
    
    # Generate content
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[full_prompt, reference_image],
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=resolution
            ),
        )
    )
    
    print("-" * 70)
    print()
    
    # Process response
    image_saved = False
    for part in response.parts:
        if part.text is not None:
            print("Model Response:")
            print(part.text)
            print()
        elif image := part.as_image():
            image.save(output_path)
            image_saved = True
            print(f"✓ Generated image saved to: {output_path}")
            print()
    
    if not image_saved:
        print("⚠ Warning: No image was generated in the response")
    
    print("=" * 70)


def main():
    """Main execution for image generation test."""
    print()
    
    # Load configuration
    config = Config()
    
    # Check for Gemini API key
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("❌ Error: GEMINI_API_KEY environment variable is required")
        print("\nAdd to your .env file:")
        print("GEMINI_API_KEY=your_gemini_api_key_here")
        print("\nGet your API key from: https://aistudio.google.com/apikey")
        sys.exit(1)
    
    if not config.product_name:
        print("❌ Error: PRODUCT_NAME environment variable is required")
        sys.exit(1)
    
    print(f"Product: {config.product_name}")
    print()
    
    # Check if YAML exists
    yaml_path = config.get_output_file_path()
    if not yaml_path.exists():
        print(f"❌ Error: YAML description not found at {yaml_path}")
        print("\nRun the analysis first:")
        print(f"  poetry run python -m product_describer.main")
        sys.exit(1)
    
    # Load YAML specifications
    print(f"Loading specifications from: {yaml_path}")
    yaml_specs = load_yaml_specs(yaml_path)
    print(f"✓ Loaded {len(yaml_specs)} characters of technical specs")
    print()
    
    # Get reference image (use first image from data directory)
    data_dir = config.get_product_data_dir()
    from product_describer.image_handler import ImageHandler
    handler = ImageHandler(data_dir)
    image_files = handler.get_image_files()
    
    if not image_files:
        print(f"❌ Error: No images found in {data_dir}")
        sys.exit(1)
    
    reference_image = image_files[0]  # Use first image as reference
    
    # Custom prompt (user can modify this)
    custom_prompt = """Create a professional studio product photograph of this item.
The lighting should be clean and even, showing all details clearly.
The background should be neutral white.
Match the technical specifications exactly, especially colors, materials, and proportions."""
    
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
            resolution=resolution
        )
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
