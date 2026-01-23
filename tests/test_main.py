"""Tests for the main module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from product_describer.main import main


def test_main_missing_product_name(monkeypatch, capsys):
    """Test main exits gracefully when PRODUCT_NAME is missing."""
    monkeypatch.delenv("PRODUCT_NAME", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Configuration Error" in captured.out
    assert "PRODUCT_NAME" in captured.out


def test_main_missing_api_key(monkeypatch, capsys):
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
        captured = capsys.readouterr()
        assert "Configuration Error" in captured.out or "OPENAI_API_KEY" in captured.out


def test_main_no_images(monkeypatch, capsys):
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
        captured = capsys.readouterr()
        assert "No valid images found" in captured.out or "No images found" in captured.out
