import json
import re
import os
import io
import base64

import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

# Load .env so os.getenv() can find GEMINI_API_KEY
load_dotenv()

# ---- Setup Gemini ----
_api_key = os.getenv("GEMINI_API_KEY")

if not _api_key:
    raise ValueError(
        "\n\nGEMINI_API_KEY not found!\n"
        "Steps to fix:\n"
        "1. Copy .env.example to .env (in the same folder)\n"
        "2. Open .env and paste your API key after GEMINI_API_KEY=\n"
        "3. Get your free key at: https://aistudio.google.com/apikey\n"
    )

genai.configure(api_key=_api_key)

# gemini-2.5-flash supports vision (images) natively and is free
_model = genai.GenerativeModel("gemini-2.5-flash")


STRUCTURING_PROMPT = """\
You are an expert at reading handwritten student exam papers.

You will be given images of an exam answer sheet — one or more pages.

YOUR TASK:
1. Read every page carefully and transcribe all handwritten text EXACTLY as written.
2. Identify each question and its sub-parts (e.g., Q1(a), Q1(b), Q2, Q3(i), Q3(ii)).
3. Return a single structured JSON object grouping all text by question/sub-part.

CRITICAL RULES — DO NOT BREAK THESE:
- Transcribe the student's words EXACTLY. If they wrote "aceleration", keep "aceleration".
  Do NOT fix spelling, grammar, or factual errors. The examiner must see what the student wrote.
- If the student wrote part (a) and part (b) under Question 1, those are sub-parts of Q1,
  not separate questions. Group them correctly under Q1.
- A student may label questions in various ways: "Q1", "1.", "Ans 1", "Answer 1",
  "Question 1", "(1)", "No.1", "1)" — treat all as equivalent.
- Sub-parts may be labeled: (a)/(b)/(c), (i)/(ii)/(iii), A/B/C, 1/2/3, etc.
- If an answer continues from the previous page, attach it to the correct question.
- If text cannot be assigned to any question, place it in "unassigned".
- Do NOT invent, add, or remove any text.
- Preserve mathematical expressions, equations, and numbers precisely as written.

OUTPUT FORMAT — return ONLY valid JSON, nothing else, no markdown, no backticks:
{{
  "num_questions": <integer: total number of distinct questions found>,
  "answers": {{
    "Q1": {{
      "full_text": "<complete transcription of Q1's answer if no sub-parts, or summary>",
      "sub_parts": {{
        "a": "<exact transcription of sub-part a>",
        "b": "<exact transcription of sub-part b>"
      }}
    }},
    "Q2": {{
      "full_text": "<complete transcription if no sub-parts>",
      "sub_parts": {{}}
    }}
  }},
  "unassigned": "<any text that could not be matched to a question, or empty string>"
}}

RULES FOR "sub_parts":
- If a question has NO sub-parts, leave "sub_parts" as an empty object {{}}.
- If a question HAS sub-parts, put each sub-part's text inside "sub_parts" and
  leave "full_text" as a brief description like "Q1 answer with 3 sub-parts".
- Use the actual label the student used as the key (e.g. "a", "b", "i", "ii").

Now carefully read all the exam images provided and return the JSON:
"""


def structure_images(images: list) -> dict:
    if not images:
        return {
            "num_questions": 0,
            "answers": {},
            "unassigned": "",
            "error": "No images provided — PDF may be empty or failed to convert."
        }

    content = [STRUCTURING_PROMPT] + images

    try:
        print(f"  Sending {len(images)} page image(s) to Gemini Vision...")
        response = _model.generate_content(content)
        response_text = response.text.strip()

        cleaned = _strip_markdown_fences(response_text)
        result = json.loads(cleaned)
        return result

    except json.JSONDecodeError as e:
        return {
            "num_questions": 0,
            "answers": {},
            "unassigned": "",
            "error": f"Gemini returned invalid JSON: {str(e)}",
            "raw_llm_response": response_text if "response_text" in locals() else "no response captured"
        }

    except Exception as e:
        return {
            "num_questions": 0,
            "answers": {},
            "unassigned": "",
            "error": f"Gemini API error: {str(e)}"
        }


def _strip_markdown_fences(text: str) -> str:
    text = re.sub(r'^```(?:json)?\s*\n?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n?```\s*$', '', text)
    return text.strip()
