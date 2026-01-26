"""Main module for product describer."""

import sys
from pathlib import Path

import yaml

from product_describer.config import Config
from product_describer.exceptions import ConfigurationError, ImageValidationError
from product_describer.gpt_analyzer import GPTAnalyzer
from product_describer.image_handler import ImageHandler
from product_describer.logger import setup_logger

logger = setup_logger(__name__)


def main() -> None:
    """Main entry point for the product describer application."""
    logger.info("=" * 60)
    logger.info("Product Describer - GPT-Powered Image Analysis")
    logger.info("=" * 60)

    try:
        # Load and validate configuration
        config = Config()
        logger.info(f"Product Name: {config.product_name}")
        logger.info(f"GPT Model: {config.gpt_model}")

        config.validate()

        # Initialize image handler
        data_dir = config.get_product_data_dir()
        logger.info(f"Reading images from: {data_dir}")

        image_handler = ImageHandler(data_dir)

        # Validate images
        valid_images, errors = image_handler.validate_images()

        if errors:
            logger.warning("Errors found:")
            for error in errors:
                logger.warning(f"  - {error}")

        if not valid_images:
            logger.error(
                "No valid images found. Please add images to the data directory."
            )
            sys.exit(1)

        logger.info(f"Found {len(valid_images)} valid image(s):")
        for img in valid_images:
            info = image_handler.get_image_info(img)
            logger.info(
                f"  - {info['filename']} ({info['format']}, {info['size'][0]}x{info['size'][1]})"
            )

        # Initialize GPT analyzer
        analyzer = GPTAnalyzer(api_key=config.openai_api_key, model=config.gpt_model)

        # Analyze product
        logger.info("-" * 60)
        product_data = analyzer.analyze_product(valid_images, config.product_name)
        logger.info("-" * 60)

        # Ensure output directory exists
        output_dir = config.get_product_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save results
        output_file = config.get_output_file_path()
        with open(output_file, "w") as f:
            yaml.dump(product_data, f, default_flow_style=False, sort_keys=False)

        logger.info("Analysis complete!")
        logger.info(f"Results saved to: {output_file}")

        # Display preview of results
        logger.info("=" * 60)
        logger.info("Preview of analysis:")
        logger.info("=" * 60)
        print(yaml.dump(product_data, default_flow_style=False, sort_keys=False))

    except ConfigurationError as e:
        logger.error(f"Configuration Error: {e}")
        logger.info("")
        logger.info("Please check your .env file and ensure:")
        logger.info("  1. PRODUCT_NAME is set")
        logger.info("  2. OPENAI_API_KEY is set")
        logger.info("  3. data/<PRODUCT_NAME> directory exists with images")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
