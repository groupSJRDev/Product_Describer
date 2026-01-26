"""Application constants."""

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# Default GPT model
DEFAULT_GPT_MODEL = "gpt-5.2-2025-12-11"

# API configuration
DEFAULT_MAX_TOKENS = 16000
DEFAULT_TEMPERATURE = 0.3
API_TIMEOUT = 60  # seconds
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_FACTOR = 2

# Image constraints
MAX_IMAGE_SIZE_MB = 20
WARN_IMAGE_SIZE_MB = 10

# File names
OUTPUT_FILENAME = "description.yaml"
GENERATION_PROMPT_FILENAME = "generation_prompt.txt"
