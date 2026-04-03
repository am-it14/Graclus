# PDF to Text — AI Exam Handwriting Digitizer

Converts handwritten exam papers (PDF or images) into structured JSON formats, grouping the exact transcription of student answers by their question numbers and sub-parts.

---

## How It Works (The New Gemini Vision Pipeline)

```text
PDF / Image  →  Gemini 2.5 Flash (Vision) reads handwriting natively  →  Structured JSON output
```

We completely bypassed standard OCR libraries to leverage **Gemini Vision**, which provides:
- Near-perfect handwriting recognition
- Spatial awareness (understands question numbers, page continuations, indentations)
- Perfect hierarchical structuring (understands Q1 has parts a, b, c)

---

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Get your free Gemini API key

1. Go to: https://aistudio.google.com/apikey
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key

### 3. Create your `.env` file

Copy the `.env.example` file and create a new `.env` file in the root directory. Paste your key:
```env
GEMINI_API_KEY=AIzaSy...your_key_here
```

### 4. Install Poppler (Windows, for PDF support only)

To read PDFs, we use `pdf2image` which requires Poppler.

1. Download Poppler for Windows: https://github.com/oschwartz10612/poppler-windows/releases
   - Get the latest `.zip` (e.g. `poppler-25.12.0_x86.zip`)
2. Extract it anywhere, e.g. `E:\poppler\poppler-25.12.0\`
3. In your `.env` file, add:
   ```env
   POPPLER_PATH=E:/poppler/poppler-25.12.0/Library/bin
   ```
   *(Use forward slashes, not backslashes. Make sure it points to the folder containing `pdftoppm.exe`)*

> If you're only processing image files (JPG, PNG), you can skip Poppler completely.

---

## Usage

### Process a folder of exam papers

Drop your files into `sample_input/`, then run:

```bash
python pipeline.py
```

Or specify custom folders:

```bash
python pipeline.py --input my_exams/ --output results/
```

### Process a single file

```bash
python pipeline.py --file sample_input/student_exam.pdf
```

---

## Output Format

Each exam paper receives a JSON file in the output folder. Gemini structures your questions to handle sub-parts inherently:

```json
{
  "file": "Economics-student1.pdf",
  "processed_at": "2026-04-03T10:30:00",
  "pages_processed": 10,
  "num_questions": 2,
  "answers": {
    "Q1": {
      "full_text": "Answer for Q1 with sub-parts",
      "sub_parts": {
        "a": "the force is equal to mass times acceleration",
        "b": "gravity acts downward"
      }
    },
    "Q2": {
      "full_text": "the law of conservation of energy states that energy cannot be created",
      "sub_parts": {}
    }
  },
  "unassigned": ""
}
```

A `_summary.json` is also generated summarizing the results.

---

## Supported Input Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| JPEG   | .jpg, .jpeg | Best for photos of exam sheets |
| PNG    | .png | Good quality, larger file size |
| PDF    | .pdf | Requires Poppler (see Setup) |
| BMP    | .bmp | Supported |
| TIFF   | .tif, .tiff | Supported |
| WebP   | .webp | Supported |

---

## Folder Structure

```
pdftotext/
├── .env                  ← your API key (never commit this)
├── .env.example          ← template (safe to commit)
├── requirements.txt      ← pip install -r this
│
├── pdf_converter.py      ← pdf2image: PDF → list of images
├── llm_structurer.py     ← Gemini Vision: images → structured JSON
├── pipeline.py           ← Main script: ties everything together
│
├── sample_input/         ← Drop exam files here
└── output/               ← JSON results appear here (auto-created)
```

---

## AI Integrity Notes

- The AI **never corrects student mistakes** — spelling errors and grammatical errors are preserved exactly as written.
- It is prompt-engineered to transcribe exact wording and assign context logically regardless of whether a student writes `Q1`, `1.`, `Ans 1`, or `No.1`.

---

## Integration with Streamlit

This module is designed to be imported:

```python
from pipeline import process_file, process_folder

# Single file
result = process_file("exam.pdf")
print(result["answers"]["Q1"])

# Batch usage
summary = process_folder("input/", "output/")
```
