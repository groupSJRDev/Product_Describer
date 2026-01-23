"""GPT-based product analysis."""

import base64
from pathlib import Path
from typing import List

from openai import OpenAI
import yaml


class GPTAnalyzer:
    """Analyze product images using GPT vision."""
    
    SYSTEM_PROMPT = """You are a product analysis expert. Analyze the provided product images and extract detailed information about the product.

Break down the product into multiple facets including but not limited to:
- Product Type
- Brand (if visible)
- Materials
- Colors
- Dimensions/Size (estimated or visible)
- Key Features
- Design Elements
- Condition (if applicable)
- Target Audience
- Use Cases
- Unique Characteristics

Provide your analysis in a structured YAML format. Be specific and detailed based on what you can observe in the images."""
    
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
                "text": f"Analyze these images of the product '{product_name}' and provide a detailed YAML breakdown."
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
            max_tokens=2000,
            temperature=0.7,
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
