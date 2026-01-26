"""Tests for the gpt_analyzer module."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

from product_describer.exceptions import APIError, YAMLParsingError
from product_describer.gpt_analyzer import GPTAnalyzer


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    with patch("product_describer.gpt_analyzer.OpenAI") as mock:
        yield mock


@pytest.fixture
def analyzer(mock_openai_client):
    """Create a GPTAnalyzer instance with mocked client."""
    return GPTAnalyzer(api_key="test_key", model="gpt-4")


def test_gpt_analyzer_initialization(mock_openai_client) -> None:
    """Test GPTAnalyzer initialization."""
    analyzer = GPTAnalyzer(api_key="test_key", model="gpt-4")

    assert analyzer.model == "gpt-4"
    mock_openai_client.assert_called_once_with(api_key="test_key")


def test_encode_image(analyzer, tmp_path) -> None:
    """Test image encoding to base64."""
    # Create a test image file
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"fake image data")

    encoded = analyzer._encode_image(img_path)

    assert isinstance(encoded, str)
    assert len(encoded) > 0


def test_get_image_mime_type(analyzer) -> None:
    """Test getting MIME type for different image formats."""
    assert analyzer._get_image_mime_type(Path("test.jpg")) == "image/jpeg"
    assert analyzer._get_image_mime_type(Path("test.jpeg")) == "image/jpeg"
    assert analyzer._get_image_mime_type(Path("test.png")) == "image/png"
    assert analyzer._get_image_mime_type(Path("test.gif")) == "image/gif"
    assert analyzer._get_image_mime_type(Path("test.webp")) == "image/webp"


def test_extract_yaml_from_response_with_yaml_block(analyzer) -> None:
    """Test extracting YAML from response with code block."""
    response = """Here is the analysis:
```yaml
product:
  name: test
  color: red
```
"""
    result = analyzer._extract_yaml_from_response(response)

    assert "product:" in result
    assert "name: test" in result


def test_extract_yaml_from_response_with_generic_block(analyzer) -> None:
    """Test extracting YAML from response with generic code block."""
    response = """```
product:
  name: test
```"""
    result = analyzer._extract_yaml_from_response(response)

    assert "product:" in result
    assert "name: test" in result


def test_extract_yaml_from_response_no_block(analyzer) -> None:
    """Test extracting YAML from plain response."""
    response = """product:
  name: test
  color: red"""

    result = analyzer._extract_yaml_from_response(response)

    assert result == response.strip()


@patch("product_describer.gpt_analyzer.time.sleep")
def test_analyze_product_success(mock_sleep, analyzer, tmp_path) -> None:
    """Test successful product analysis."""
    # Create test image
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"fake image")

    # Mock API response
    mock_response = Mock()
    mock_message = Mock()
    mock_message.content = """```yaml
product_name: Test Product
dimensions:
  width: 100mm
  height: 200mm
```"""
    mock_response.choices = [Mock(message=mock_message)]

    analyzer.client.chat.completions.create = Mock(return_value=mock_response)

    # Analyze
    result = analyzer.analyze_product([img_path], "Test Product")

    assert isinstance(result, dict)
    assert "product_name" in result
    assert result["product_name"] == "Test Product"


@patch("product_describer.gpt_analyzer.time.sleep")
def test_analyze_product_retry_on_failure(mock_sleep, analyzer, tmp_path) -> None:
    """Test retry logic when API call fails."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"fake image")

    # Mock API to fail twice then succeed
    mock_response = Mock()
    mock_message = Mock()
    mock_message.content = "```yaml\nproduct: test\n```"
    mock_response.choices = [Mock(message=mock_message)]

    analyzer.client.chat.completions.create = Mock(
        side_effect=[Exception("API Error"), Exception("API Error"), mock_response]
    )

    # Should succeed after retries
    result = analyzer.analyze_product([img_path], "Test Product")

    assert isinstance(result, dict)
    assert analyzer.client.chat.completions.create.call_count == 3


@patch("product_describer.gpt_analyzer.time.sleep")
def test_analyze_product_max_retries_exceeded(mock_sleep, analyzer, tmp_path) -> None:
    """Test that APIError is raised after max retries."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"fake image")

    # Mock API to always fail
    analyzer.client.chat.completions.create = Mock(side_effect=Exception("API Error"))

    with pytest.raises(APIError, match="GPT API call failed"):
        analyzer.analyze_product([img_path], "Test Product")


def test_analyze_product_empty_response(analyzer, tmp_path) -> None:
    """Test handling of empty API response."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"fake image")

    # Mock empty response
    mock_response = Mock()
    mock_message = Mock()
    mock_message.content = None
    mock_response.choices = [Mock(message=mock_message)]

    analyzer.client.chat.completions.create = Mock(return_value=mock_response)

    with pytest.raises(APIError, match="empty response"):
        analyzer.analyze_product([img_path], "Test Product")


def test_analyze_product_invalid_yaml(analyzer, tmp_path) -> None:
    """Test handling of invalid YAML in response."""
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"fake image")

    # Mock response with invalid YAML
    mock_response = Mock()
    mock_message = Mock()
    mock_message.content = "```yaml\ninvalid: yaml: content: bad\n```"
    mock_response.choices = [Mock(message=mock_message)]

    analyzer.client.chat.completions.create = Mock(return_value=mock_response)

    # Should return raw response when YAML parsing fails
    result = analyzer.analyze_product([img_path], "Test Product")

    assert "raw_response" in result
