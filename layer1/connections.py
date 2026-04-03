"""
pipeline.py
-----------
PURPOSE: Main orchestrator — ties everything together.

NEW FLOW (EasyOCR removed):
  PDF   →  [pdf_converter]  →  list of PIL Images
  Image →  [load_image]     →  single PIL Image in a list
  Images → [llm_structurer] →  Gemini Vision reads handwriting + returns JSON

HOW TO RUN:
  # Process a folder of exams:
  python pipeline.py --input sample_input/ --output output/

  # Process a single file:
  python pipeline.py --file path/to/exam.pdf

  # Use defaults (input = sample_input/, output = output/):
  python pipeline.py

HOW TO USE AS A MODULE (for Streamlit integration):
  from pipeline import process_file, process_folder
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

# Load .env before importing our modules
# (llm_structurer.py needs GEMINI_API_KEY at import time)
load_dotenv()

from conpdfima import pdf_to_images, load_image
from ocr_integration import structure_images


# ---- Supported file types ----
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png'}
SUPPORTED_PDF_FORMAT    = {'.pdf'}
ALL_SUPPORTED           = SUPPORTED_IMAGE_FORMATS | SUPPORTED_PDF_FORMAT


def process_file(file_path: str) -> dict:
    file_path = Path(file_path)
    file_ext  = file_path.suffix.lower()

    print(f"\n{'─' * 55}")
    print(f"  File: {file_path.name}")
    print(f"{'─' * 55}")

    # ---- Step 1: Get images ----
    # Turn whatever the input is into a list of PIL Images.
    # Gemini Vision accepts PIL Images directly — no intermediate text needed.

    if file_ext in SUPPORTED_PDF_FORMAT:
        print("  [1/2] PDF → Images")
        try:
            images = pdf_to_images(str(file_path))
        except EnvironmentError as e:
            return {"file": file_path.name, "error": str(e), "num_questions": 0, "answers": {}}
        except Exception as e:
            return {"file": file_path.name, "error": f"PDF conversion failed: {e}", "num_questions": 0, "answers": {}}

    elif file_ext in SUPPORTED_IMAGE_FORMATS:
        print("  [1/2] Loading image")
        try:
            images = [load_image(str(file_path))]
        except Exception as e:
            return {"file": file_path.name, "error": f"Image load failed: {e}", "num_questions": 0, "answers": {}}

    else:
        return {
            "file": file_path.name,
            "error": f"Unsupported format: '{file_ext}'. Supported: {', '.join(sorted(ALL_SUPPORTED))}",
            "num_questions": 0,
            "answers": {}
        }

    # ---- Step 2: Gemini Vision → Structured JSON ----
    # All pages are sent in ONE API call.
    # Gemini sees every page together, so it can correctly handle:
    #   - Answers that continue across a page break
    #   - Sub-parts split across pages
    #   - The full context of the paper

    print(f"  [2/2] Gemini Vision — reading {len(images)} page(s)...")
    structured = structure_images(images)

    # ---- Assemble final result ----
    result = {
        "file":            file_path.name,
        "processed_at":    datetime.now().isoformat(),
        "pages_processed": len(images),
        **structured   # Unpacks: num_questions, answers, unassigned, (maybe error)
    }

    if "error" in structured:
        print(f"  ⚠  Warning: {structured['error']}")
    else:
        num = structured.get("num_questions", 0)
        print(f"  ✓  Done — found {num} question(s)")

    return result


def process_folder(input_folder: str, output_folder: str) -> list:
    """
    Batch processes all supported files in a folder.

    For each file:
      - Runs the full pipeline
      - Saves a <filename>_result.json in output_folder

    Also saves a _summary.json with aggregate stats.

    Args:
        input_folder (str):  Folder containing student exam files
        output_folder (str): Folder where JSON results will be saved

    Returns:
        list[dict]: Summary of all processed files
    """
    input_path  = Path(input_folder)
    output_path = Path(output_folder)

    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    # Find all supported files (ignore hidden files, subdirectories)
    files = sorted([
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in ALL_SUPPORTED
    ])

    if not files:
        print(f"\nNo supported files found in: {input_folder}")
        print(f"Supported formats: {', '.join(sorted(ALL_SUPPORTED))}")
        return []

    print(f"\n{'=' * 55}")
    print(f"  Batch Processing")
    print(f"  Input:  {input_folder}")
    print(f"  Output: {output_folder}")
    print(f"  Files:  {len(files)}")
    print(f"{'=' * 55}")

    summary = []

    for i, file_path in enumerate(files):
        print(f"\n[{i + 1}/{len(files)}]", end="")
        result = process_file(str(file_path))

        # Save individual result JSON
        output_file = output_path / f"{file_path.stem}_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"  Saved → {output_file.name}")

        summary.append({
            "file":         file_path.name,
            "output":       output_file.name,
            "num_questions": result.get("num_questions", 0),
            "status":       "error" if "error" in result else "success",
            "error":        result.get("error", None)
        })

    # Save batch summary
    summary_data = {
        "batch_processed_at": datetime.now().isoformat(),
        "total_files":  len(files),
        "successful":   sum(1 for s in summary if s["status"] == "success"),
        "errors":       sum(1 for s in summary if s["status"] == "error"),
        "results":      summary
    }

    summary_file = output_path / "_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2)

    print(f"\n{'=' * 55}")
    print(f"  Batch complete!")
    print(f"  Successful: {summary_data['successful']}/{len(files)}")
    print(f"  Errors:     {summary_data['errors']}/{len(files)}")
    print(f"  Summary:    {summary_file}")
    print(f"{'=' * 55}\n")

    return summary


# ---- Command-line interface ----
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Handwritten Exam OCR Pipeline — Gemini Vision → JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Process a folder of exams:
    python pipeline.py --input sample_input/ --output output/

  Process a single file:
    python pipeline.py --file sample_input/exam1.pdf

  Use defaults (sample_input/ → output/):
    python pipeline.py
        """
    )

    parser.add_argument(
        "--input", "-i",
        type=str,
        default="sample_input",
        help="Folder containing exam PDFs or images (default: sample_input/)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output",
        help="Folder to save JSON results (default: output/)"
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=None,
        help="Process a single file and print result to console"
    )

    args = parser.parse_args()

    if args.file:
        # Single file mode — print to console
        result = process_file(args.file)
        print("\n" + "=" * 55)
        print("RESULT:")
        print("=" * 55)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Batch folder mode
        process_folder(args.input, args.output)
