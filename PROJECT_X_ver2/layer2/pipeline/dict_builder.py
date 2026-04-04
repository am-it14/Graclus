import os
import json
import re

def build_question_dictionaries(directory_path: str) -> dict:
    # Initialize dictionary mapping question_id -> { doc_name -> answer_string }
    questions_dict = {i: {} for i in range(1, 11)}
    
    if not os.path.exists(directory_path):
        print(f"Error: Directory '{directory_path}' not found.")
        return questions_dict
        
    for filename in os.listdir(directory_path):
        # Process only our specific json sheets
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Ensure this is one of our parsed PDF-to-text JSONs by checking for the 'answers' key
                if "answers" not in data:
                    continue
                    
                for q_key, ans_data in data["answers"].items():
                    # Extract the numerical value out of the question key (e.g., 'Q3' -> 3)
                    q_num_str = re.sub(r'\D', '', q_key)
                    if not q_num_str:
                        continue
                        
                    try:
                        q_num = int(q_num_str)
                    except ValueError:
                        continue
                        
                    # Extract the entire text block, including sub-parts, so the clustering algo gets all the context
                    answer_text = ans_data.get("full_text", "")
                    
                    if "sub_parts" in ans_data and isinstance(ans_data["sub_parts"], dict):
                        for sp_k, sp_v in ans_data["sub_parts"].items():
                            answer_text += f"\n{sp_k}: {sp_v}"
                            
                    answer_text = answer_text.strip()
                    
                    if answer_text:
                        if q_num not in questions_dict:
                            questions_dict[q_num] = {}
                        # Append to dictionary using the filename explicitly as the key
                        questions_dict[q_num][filename] = answer_text
                        
            except (json.JSONDecodeError, UnicodeDecodeError, Exception) as e:
                print(f"Error reading {filename}: {e}")
                continue

    return questions_dict


if __name__ == "__main__":
    import pprint
    
    # Path to where the documents currently reside
    docs_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    print("Building dictionaries from documents...")
    all_questions_data = build_question_dictionaries(docs_folder)
    
    # Verify the dictionary format by printing out the dictionary solely for Question 1
    print("\n========== SAMPLE OUTPUT FOR QUESTION 1 ==========\n")
    if 1 in all_questions_data and all_questions_data[1]:
        pprint.pprint(all_questions_data[1], depth=2)
        print(f"\nTotal Responses Extracted for Q1: {len(all_questions_data[1])}")
    else:
        print("No data extracted for Question 1!")
        
    print("\nReady! The inner dictionary (pictured above) perfectly matches the input schema for your clustering pipeline.")
