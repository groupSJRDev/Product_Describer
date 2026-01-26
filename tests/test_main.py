"""Tests for the main module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from product_describer.exceptions import ConfigurationError
from product_describer.main import main


def test_main_missing_product_name(monkeypatch, caplog) -> None:
    """Test main exits gracefully when PRODUCT_NAME is missing."""
    monkeypatch.delenv("PRODUCT_NAME", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert "Configuration Error" in caplog.text
    assert "PRODUCT_NAME" in caplog.text


def test_main_missing_api_key(monkeypatch, caplog) -> None:
    """Test main exits gracefully when OPENAI_API_KEY is missing."""
    monkeypatch.setenv("PRODUCT_NAME", "test_product")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data" / "test_product"
        data_dir.mkdir(parents=True)

        monkeypatch.chdir(tmpdir)

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        assert "Configuration Error" in caplog.text or "OPENAI_API_KEY" in caplog.text


def test_main_no_images(monkeypatch, caplog) -> None:
    """Test main exits when no images are found."""
    monkeypatch.setenv("PRODUCT_NAME", "test_product")
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")

    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data" / "test_product"
        data_dir.mkdir(parents=True)

        monkeypatch.chdir(tmpdir)

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        assert (
            "No valid images found" in caplog.text or "No images found" in caplog.text
        )
