"""Custom exceptions for product describer."""


class ProductDescriberError(Exception):
    """Base exception for product describer."""

    pass


class ConfigurationError(ProductDescriberError):
    """Configuration related errors."""

    pass


class ImageValidationError(ProductDescriberError):
    """Image validation errors."""

    pass


class APIError(ProductDescriberError):
    """API call errors."""

    pass


class YAMLParsingError(ProductDescriberError):
    """YAML parsing errors."""

    pass
