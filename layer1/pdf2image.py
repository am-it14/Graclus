import os
from pathlib import Path
from PIL import Image

def pdftoimage(pathofpdf : str, dpi : int = 200) -> list:
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise ImportError("pdf2image is not installed. Fix: pip install pdf2image")
    
    poppler_path = os.getenv("POPPLER_PATH", None)

    if poppler_path:
            images = convert_from_path(pathofpdf, poppler_path = poppler_path)
    else:
            images = convert_from_path(pathofpdf)

    print(f" Converted PDF: {len(images)}")
    return images