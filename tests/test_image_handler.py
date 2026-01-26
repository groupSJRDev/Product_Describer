"""Tests for the image_handler module."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from product_describer.image_handler import ImageHandler


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test images."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_image(temp_data_dir):
    """Create a sample test image."""
    img_path = temp_data_dir / "test_image.jpg"
    img = Image.new("RGB", (100, 100), color="red")
    img.save(img_path)
    return img_path


def test_image_handler_initialization(temp_data_dir) -> None:
    """Test ImageHandler initialization."""
    handler = ImageHandler(temp_data_dir)
    assert handler.data_dir == temp_data_dir


def test_get_image_files_empty_directory(temp_data_dir) -> None:
    """Test getting image files from empty directory."""
    handler = ImageHandler(temp_data_dir)
    files = handler.get_image_files()
    assert files == []


def test_get_image_files_with_images(temp_data_dir) -> None:
    """Test getting image files from directory with images."""
    # Create test images
    img1 = Image.new("RGB", (100, 100), color="red")
    img1.save(temp_data_dir / "image1.jpg")

    img2 = Image.new("RGB", (100, 100), color="blue")
    img2.save(temp_data_dir / "image2.png")

    handler = ImageHandler(temp_data_dir)
    files = handler.get_image_files()

    assert len(files) == 2
    assert all(f.exists() for f in files)


def test_get_image_files_sorted(temp_data_dir) -> None:
    """Test that image files are returned sorted."""
    # Create images with specific names
    for name in ["c.jpg", "a.png", "b.jpg"]:
        img = Image.new("RGB", (100, 100))
        img.save(temp_data_dir / name)

    handler = ImageHandler(temp_data_dir)
    files = handler.get_image_files()

    names = [f.name for f in files]
    assert names == ["a.png", "b.jpg", "c.jpg"]


def test_get_image_files_case_insensitive(temp_data_dir) -> None:
    """Test that image file search is case-insensitive."""
    # Create images with uppercase extensions
    img = Image.new("RGB", (100, 100))
    img.save(temp_data_dir / "test.JPG")

    handler = ImageHandler(temp_data_dir)
    files = handler.get_image_files()

    assert len(files) == 1


def test_encode_image_to_base64(sample_image) -> None:
    """Test encoding image to base64."""
    handler = ImageHandler(sample_image.parent)
    encoded = handler.encode_image_to_base64(sample_image)

    assert isinstance(encoded, str)
    assert len(encoded) > 0


def test_get_image_info(sample_image) -> None:
    """Test getting image information."""
    handler = ImageHandler(sample_image.parent)
    info = handler.get_image_info(sample_image)

    assert info["filename"] == "test_image.jpg"
    assert info["format"] == "JPEG"
    assert info["size"] == (100, 100)
    assert info["mode"] == "RGB"


def test_validate_images_valid(temp_data_dir) -> None:
    """Test validating directory with valid images."""
    # Create valid image
    img = Image.new("RGB", (100, 100), color="green")
    img.save(temp_data_dir / "valid.jpg")

    handler = ImageHandler(temp_data_dir)
    valid_images, errors = handler.validate_images()

    assert len(valid_images) == 1
    assert len(errors) == 0


def test_validate_images_no_images(temp_data_dir) -> None:
    """Test validating empty directory."""
    handler = ImageHandler(temp_data_dir)
    valid_images, errors = handler.validate_images()

    assert len(valid_images) == 0
    assert len(errors) == 1
    assert "No images found" in errors[0]


def test_validate_images_invalid_file(temp_data_dir) -> None:
    """Test validating directory with invalid image file."""
    # Create a fake image file
    bad_file = temp_data_dir / "bad.jpg"
    bad_file.write_text("not an image")

    handler = ImageHandler(temp_data_dir)
    valid_images, errors = handler.validate_images()

    assert len(valid_images) == 0
    assert len(errors) == 1
    assert "Invalid image" in errors[0]


def test_validate_images_mixed(temp_data_dir) -> None:
    """Test validating directory with both valid and invalid images."""
    # Create valid image
    img = Image.new("RGB", (100, 100))
    img.save(temp_data_dir / "good.jpg")

    # Create invalid file
    bad_file = temp_data_dir / "bad.jpg"
    bad_file.write_text("not an image")

    handler = ImageHandler(temp_data_dir)
    valid_images, errors = handler.validate_images()

    assert len(valid_images) == 1
    assert len(errors) == 1
