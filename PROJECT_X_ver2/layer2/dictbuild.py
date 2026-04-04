import os
import json
import re
from typing import Dict


def build_question_dictionaries(directory_path: str) -> Dict[int, Dict[str, str]]:
    """
    Parses all JSON answer sheets in a directory and builds a nested dictionary.

    Output Schema:
    {
        1: {
            "file1_result.json": "Answer text...",
            "file2_result.json": "Answer text..."
        },
        ...
    }
    """

    # Initialize dictionary for questions 1–10
    questions_dict = {i: {} for i in range(1, 11)}

    # Validate directory
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    for filename in os.listdir(directory_path):
        if not filename.endswith("_result.json"):
            continue

        filepath = os.path.join(directory_path, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Skip malformed files
            if "answers" not in data:
                continue

            for q_key, ans_data in data["answers"].items():

                # Extract numeric part (Q1 → 1)
                q_num_str = re.sub(r'\D', '', q_key)
                if not q_num_str:
                    continue

                q_num = int(q_num_str)

                # Extract main answer text
                answer_text = ans_data.get("full_text", "")

                # Append sub-parts if present
                if isinstance(ans_data.get("sub_parts"), dict):
                    for sp_k, sp_v in ans_data["sub_parts"].items():
                        answer_text += f"\n{sp_k}: {sp_v}"

                answer_text = answer_text.strip()

                if not answer_text:
                    continue

                # Add to dictionary
                questions_dict.setdefault(q_num, {})
                questions_dict[q_num][filename] = answer_text

        except Exception as e:
            print(f"[WARNING] Skipping {filename}: {e}")
            continue

    return questions_dict


def get_output_folder_path() -> str:
    current_dir = os.path.dirname(__file__)

    return os.path.abspath(
        os.path.join(current_dir, "..", "layer1", "output")
    )


if __name__ == "__main__":
    import pprint

    print("=== Building Question Dictionaries ===")

    try:
        docs_folder = get_output_folder_path()
        print(f"Reading from: {docs_folder}")

        all_questions_data = build_question_dictionaries(docs_folder)

        # Debug: show Q1
        print("\n========== SAMPLE OUTPUT FOR QUESTION 1 ==========\n")

        q1_data = all_questions_data.get(1, {})

        if q1_data:
            pprint.pprint(q1_data, depth=2)
            print(f"\nTotal Responses Extracted for Q1: {len(q1_data)}")
        else:
            print("No data extracted for Question 1!")

        print("\n[✔] Dictionary build complete. Ready for clustering.\n")

    except Exception as e:
        print(f"[ERROR] {e}")