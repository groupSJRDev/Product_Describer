"""Main module for product describer."""

import sys
from pathlib import Path

import yaml

from product_describer.config import Config
from product_describer.image_handler import ImageHandler
from product_describer.gpt_analyzer import GPTAnalyzer


def main() -> None:
    """Main entry point for the product describer application."""
    print("=" * 60)
    print("Product Describer - GPT-Powered Image Analysis")
    print("=" * 60)
    print()
    
    try:
        # Load and validate configuration
        config = Config()
        print(f"Product Name: {config.product_name}")
        print(f"GPT Model: {config.gpt_model}")
        print()
        
        config.validate()
        
        # Initialize image handler
        data_dir = config.get_product_data_dir()
        print(f"Reading images from: {data_dir}")
        
        image_handler = ImageHandler(data_dir)
        
        # Validate images
        valid_images, errors = image_handler.validate_images()
        
        if errors:
            print("\n⚠ Errors found:")
            for error in errors:
                print(f"  - {error}")
        
        if not valid_images:
            print("\n❌ No valid images found. Please add images to the data directory.")
            sys.exit(1)
        
        print(f"\n✓ Found {len(valid_images)} valid image(s):")
        for img in valid_images:
            info = image_handler.get_image_info(img)
            print(f"  - {info['filename']} ({info['format']}, {info['size'][0]}x{info['size'][1]})")
        
        print()
        
        # Initialize GPT analyzer
        analyzer = GPTAnalyzer(
            api_key=config.openai_api_key,
            model=config.gpt_model
        )
        
        # Analyze product
        print("-" * 60)
        product_data = analyzer.analyze_product(valid_images, config.product_name)
        print("-" * 60)
        print()
        
        # Ensure output directory exists
        output_dir = config.get_product_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save results
        output_file = config.get_output_file_path()
        with open(output_file, "w") as f:
            yaml.dump(product_data, f, default_flow_style=False, sort_keys=False)
        
        print(f"✓ Analysis complete!")
        print(f"✓ Results saved to: {output_file}")
        print()
        
        # Display preview of results
        print("=" * 60)
        print("Preview of analysis:")
        print("=" * 60)
        print(yaml.dump(product_data, default_flow_style=False, sort_keys=False))
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease check your .env file and ensure:")
        print("  1. PRODUCT_NAME is set")
        print("  2. OPENAI_API_KEY is set")
        print("  3. data/<PRODUCT_NAME> directory exists with images")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
