"""Tests for the config module."""

import os
import tempfile
from pathlib import Path

import pytest

from product_describer.config import Config
from product_describer.exceptions import ConfigurationError


def test_config_initialization(monkeypatch) -> None:
    """Test that Config initializes correctly with environment variables."""
    monkeypatch.setenv("PRODUCT_NAME", "test_product")
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("GPT_MODEL", "gpt-4")

    config = Config()

    assert config.product_name == "test_product"
    assert config.openai_api_key == "test_key"
    assert config.gpt_model == "gpt-4"


def test_config_default_gpt_model(monkeypatch) -> None:
    """Test that Config uses default GPT model when not specified."""
    monkeypatch.setenv("PRODUCT_NAME", "test_product")
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    monkeypatch.delenv("GPT_MODEL", raising=False)

    config = Config()

    from product_describer.constants import DEFAULT_GPT_MODEL

    assert config.gpt_model == DEFAULT_GPT_MODEL


def test_config_get_product_data_dir(monkeypatch) -> None:
    """Test getting product data directory path."""
    monkeypatch.setenv("PRODUCT_NAME", "test_product")

    config = Config()
    data_dir = config.get_product_data_dir()

    assert data_dir == config.base_dir / "data" / "test_product"


def test_config_get_product_data_dir_no_product_name(monkeypatch) -> None:
    """Test that get_product_data_dir raises error when PRODUCT_NAME is not set."""
    monkeypatch.delenv("PRODUCT_NAME", raising=False)

    config = Config()

    with pytest.raises(ConfigurationError, match="PRODUCT_NAME environment variable"):
        config.get_product_data_dir()


def test_config_get_product_output_dir(monkeypatch) -> None:
    """Test getting product output directory path."""
    monkeypatch.setenv("PRODUCT_NAME", "test_product")

    config = Config()
    output_dir = config.get_product_output_dir()

    assert output_dir == config.base_dir / "temp" / "test_product"


def test_config_get_output_file_path(monkeypatch) -> None:
    """Test getting output file path."""
    monkeypatch.setenv("PRODUCT_NAME", "test_product")

    config = Config()
    output_file = config.get_output_file_path()

    assert output_file == config.base_dir / "temp" / "test_product" / "description.yaml"


def test_config_validate_success(monkeypatch) -> None:
    """Test that validate succeeds with valid configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create product data directory
        data_dir = Path(tmpdir) / "data" / "test_product"
        data_dir.mkdir(parents=True)

        monkeypatch.setenv("PRODUCT_NAME", "test_product")
        monkeypatch.setenv("OPENAI_API_KEY", "test_key")
        monkeypatch.chdir(tmpdir)

        config = Config()
        config.validate()  # Should not raise


def test_config_validate_missing_product_name(monkeypatch) -> None:
    """Test that validate raises error when PRODUCT_NAME is missing."""
    monkeypatch.delenv("PRODUCT_NAME", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")

    config = Config()

    with pytest.raises(ConfigurationError, match="PRODUCT_NAME"):
        config.validate()


def test_config_validate_missing_api_key(monkeypatch) -> None:
    """Test that validate raises error when OPENAI_API_KEY is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data" / "test_product"
        data_dir.mkdir(parents=True)

        monkeypatch.setenv("PRODUCT_NAME", "test_product")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.chdir(tmpdir)

        config = Config()

        with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
            config.validate()


def test_config_validate_missing_data_directory(monkeypatch) -> None:
    """Test that validate raises error when data directory doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("PRODUCT_NAME", "test_product")
        monkeypatch.setenv("OPENAI_API_KEY", "test_key")
        monkeypatch.chdir(tmpdir)

        config = Config()

        with pytest.raises(ConfigurationError, match="does not exist"):
            config.validate()
