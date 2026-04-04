
import os
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image

def pdf_to_images(pdf_path: str, dpi: int = 200):
  BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  poppler_path = os.path.join(BASE_DIR, "stuff_imp/poppler/poppler-25.12.0/Library/bin")

  if poppler_path:
      images = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
  else:
      images = convert_from_path(pdf_path, dpi=dpi)

  print(f"  Converted PDF: {len(images)} page(s) at {dpi} DPI")
  return images

def load_image(image_path: str) -> Image.Image:
    #Loads a single image file and converts it to RGB mode.
    return Image.open(image_path).convert("RGB")