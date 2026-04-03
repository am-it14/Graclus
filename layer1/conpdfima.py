"""
pdf_converter.py
----------------
PURPOSE: Converts PDF files into lists of PIL Images, one per page.

WHY THIS IS A SEPARATE MODULE:
  EasyOCR/Gemini works natively with image format.
  This module bridges the gap.

HOW pdf2image WORKS:
  It uses a tool called Poppler under the hood.
  Poppler is a C++ library that renders PDF pages as pixel images.
  On Windows, you need to install Poppler separately (see README).

DPI EXPLAINED:
  DPI = Dots Per Inch = how many pixels per inch of the original page.
  Higher DPI = more pixels = better details (but slower, larger files).
  200 DPI is a good sweet spot for handwritten exam papers.
"""

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