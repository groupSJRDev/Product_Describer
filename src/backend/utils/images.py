from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import io

def validate_and_process_image(file: UploadFile) -> Tuple[io.BytesIO, str, Optional[int], Optional[int]]:
    """
    Validate image file type and extract metadata.
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        Tuple containing:
        - file_obj (io.BytesIO): The file content stream
        - filename (str): The original filename
        - width (Optional[int]): Image width
        - height (Optional[int]): Image height
        
    Raises:
        HTTPException: If file type is not allowed
    """
    allowed_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Allowed: {allowed_types}"
        )
        
    # Read content
    try:
        # Read file into memory
        content = file.file.read()
        file_obj = io.BytesIO(content)
        
        # Reset file pointer for caller (though BytesIO is new)
        file.file.seek(0) 
        
        try:
            img = Image.open(io.BytesIO(content))
            width, height = img.size
        except Exception:
            width, height = None, None
            
        return file_obj, file.filename, width, height
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image {file.filename}: {str(e)}"
        )
