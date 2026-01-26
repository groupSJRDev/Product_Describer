"""Template management for structured product analysis."""

from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from product_describer.exceptions import ConfigurationError
from product_describer.logger import setup_logger

logger = setup_logger(__name__)


class TemplateManager:
    """Manage YAML analysis templates."""

    def __init__(self, templates_dir: Path = None) -> None:
        """Initialize template manager.

        Args:
            templates_dir: Directory containing templates. Defaults to project templates/ dir.
        """
        if templates_dir is None:
            # Default to templates directory in project root
            self.templates_dir = Path(__file__).parent.parent.parent / "templates"
        else:
            self.templates_dir = Path(templates_dir)

        logger.debug(f"Template directory: {self.templates_dir}")

    def load_template(self, version: str = "1.0") -> str:
        """Load YAML template by version.

        Args:
            version: Template version (e.g., "1.0", "2.0")

        Returns:
            Template as string

        Raises:
            ConfigurationError: If template file not found
        """
        template_path = self.templates_dir / f"product_analysis_v{version}.yaml"

        if not template_path.exists():
            raise ConfigurationError(
                f"Template version {version} not found at {template_path}"
            )

        logger.info(f"Loading template: {template_path}")
        with open(template_path, "r") as f:
            return f.read()

    def validate_response(
        self, response: Dict[str, Any], version: str = "1.0"
    ) -> Tuple[bool, List[str]]:
        """Validate response against template structure.

        Args:
            response: Parsed YAML response from GPT
            version: Template version to validate against

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Load expected structure
        try:
            template_str = self.load_template(version)
            template = yaml.safe_load(template_str)
        except Exception as e:
            errors.append(f"Failed to load template: {e}")
            return False, errors

        # Check all required sections present
        required_sections = self._get_required_sections(template)
        for section in required_sections:
            if section not in response:
                errors.append(f"Missing required section: {section}")

        # Validate metadata
        if "metadata" in response:
            if "template_version" not in response["metadata"]:
                errors.append("Missing metadata.template_version")
            elif response["metadata"]["template_version"] != version:
                errors.append(
                    f"Template version mismatch: expected {version}, "
                    f"got {response['metadata']['template_version']}"
                )

        # Validate data types for critical fields
        type_errors = self._validate_types(response, template)
        errors.extend(type_errors)

        is_valid = len(errors) == 0
        if is_valid:
            logger.info("Template validation passed")
        else:
            logger.warning(f"Template validation failed with {len(errors)} errors")

        return is_valid, errors

    def _get_required_sections(self, template: Dict[str, Any]) -> List[str]:
        """Extract required top-level sections.

        Args:
            template: Parsed template dictionary

        Returns:
            List of required section names
        """
        # All top-level keys are considered required
        return list(template.keys())

    def _validate_types(
        self, response: Dict[str, Any], template: Dict[str, Any]
    ) -> List[str]:
        """Validate field types match expected types.

        Args:
            response: Response to validate
            template: Template structure

        Returns:
            List of type validation errors
        """
        errors = []

        # Validate confidence scores are between 0 and 1
        confidence_errors = self._validate_confidence_scores(response)
        errors.extend(confidence_errors)

        # Validate hex color formats
        color_errors = self._validate_colors(response)
        errors.extend(color_errors)

        return errors

    def _validate_confidence_scores(self, data: Any, path: str = "") -> List[str]:
        """Recursively validate confidence scores.

        Args:
            data: Data structure to validate
            path: Current path in data structure

        Returns:
            List of validation errors
        """
        errors = []

        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key

                if key == "confidence" and value is not None:
                    if not isinstance(value, (int, float)):
                        errors.append(
                            f"{current_path}: confidence must be a number, got {type(value)}"
                        )
                    elif not (0.0 <= value <= 1.0):
                        errors.append(
                            f"{current_path}: confidence must be between 0.0 and 1.0, got {value}"
                        )

                # Recurse into nested structures
                if isinstance(value, (dict, list)):
                    errors.extend(self._validate_confidence_scores(value, current_path))

        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                errors.extend(self._validate_confidence_scores(item, current_path))

        return errors

    def _validate_colors(self, data: Any, path: str = "") -> List[str]:
        """Recursively validate hex color codes.

        Args:
            data: Data structure to validate
            path: Current path in data structure

        Returns:
            List of validation errors
        """
        errors = []

        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key

                if key == "hex" and value is not None:
                    if not isinstance(value, str):
                        errors.append(
                            f"{current_path}: hex must be a string, got {type(value)}"
                        )
                    elif not self._is_valid_hex_color(value):
                        errors.append(
                            f"{current_path}: invalid hex color format: {value}"
                        )

                # Recurse into nested structures
                if isinstance(value, (dict, list)):
                    errors.extend(self._validate_colors(value, current_path))

        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                errors.extend(self._validate_colors(item, current_path))

        return errors

    def _is_valid_hex_color(self, color: str) -> bool:
        """Check if string is valid hex color.

        Args:
            color: Color string to validate

        Returns:
            True if valid hex color format
        """
        if not color.startswith("#"):
            return False
        if len(color) != 7:
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False
