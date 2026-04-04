import os
import pprint
from dict_builder import build_question_dictionaries
from answer_clustering import cluster_answers

def run_evaluation(docs_directory):
    final_output = {}

    parsed_questions_data = build_question_dictionaries(docs_directory)

    for q_num, answers_dict in parsed_questions_data.items():
        if not answers_dict:
            continue

        clustering_result = cluster_answers(
            answers_dict,
            eps=0.3,
            min_samples=2
        )

        final_output[f"Q{q_num}"] = clustering_result

    return final_output

if __name__ == "__main__":
    target_docs_folder = ...

    result = run_evaluation(target_docs_folder)

    import json
    with open("pipeline_output.json", "w") as f:
        json.dump(result, f, indent=2)

    print("[✔] Output saved to pipeline_output.json")