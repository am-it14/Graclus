import os
import re

def build_question_dictionaries(directory_path: str) -> dict:
    """
    Parses all Markdown answer sheets in a directory and builds a nested dictionary.
    
    Output Schema:
    {
        1: {
            "Doc1_Standard.md": "Answer text for question 1...",
            "Doc2_Analytical.md": "Answer text for question 1..."
        },
        2: { 
            "Doc1_Standard.md": "Answer text for question 2...",
            ... 
        }
    }
    
    The inner dictionary for each question perfectly matches the `answers: dict` 
    input parameter expected by the cluster_answers() function.
    """
    # Initialize dictionary mapping question_id -> { doc_name -> answer_string }
    questions_dict = {i: {} for i in range(1, 11)}
    
    if not os.path.exists(directory_path):
        print(f"Error: Directory '{directory_path}' not found.")
        return questions_dict
        
    for filename in os.listdir(directory_path):
        # Process only our specific markdown sheets
        if filename.endswith(".md") and filename.startswith("Doc"):
            filepath = os.path.join(directory_path, filename)
            
            content = ""
            for enc in ("utf-8", "utf-16", "latin-1"):
                try:
                    with open(filepath, 'r', encoding=enc) as f:
                        content = f.read().strip()
                    break
                except UnicodeDecodeError:
                    continue
                
            # Split text strictly at numerical list markers (e.g., "1. ", "2. ")
            answers = re.split(r'(?m)^(\d+)\.\s+', content)
            
            # Re.split returns ['potential_header', '1', 'answer_text', '2', 'answer_text']
            for i in range(1, len(answers), 2):
                try:
                    q_num = int(answers[i])
                    q_text = answers[i+1].strip()
                    
                    if q_num in questions_dict:
                        # Append to dictionary using the filename explicitly as the key
                        questions_dict[q_num][filename] = q_text
                except (ValueError, IndexError):
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
