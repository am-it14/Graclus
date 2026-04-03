import os
import pprint
from dict_builder import build_question_dictionaries
from answer_clustering import cluster_answers

def run_evaluation(docs_directory):
    """
    Integrates the DictBuilder document parsing step with the 
    Semantic DBSCAN mapping outputting straight to the terminal interface.
    """
    print(f"Scanning directory for exam documents: {docs_directory}\n")
    
    # Step 1: Use dict_builder logic to extract raw text mapped by filenames
    parsed_questions_data = build_question_dictionaries(docs_directory)
    
    if not parsed_questions_data or not any(parsed_questions_data.values()):
        print("No valid documents or questions extracted. Exiting.")
        return
        
    print("Documents successfully parsed! Proceeding to NLP Clustering...\n" + "="*50 + "\n")
    
    # Step 2: Iterate dynamically through mapped question dictionaries
    for q_num, answers_dict in parsed_questions_data.items():
        if not answers_dict:
            continue
            
        print(f"=====================================")
        print(f"    EVALUATING QUESTION {q_num}       ")
        print(f"=====================================")
        
        # Step 3: Run the cluster_answers pipeline from answer_clustering
        clustering_result = cluster_answers(answers_dict, eps=0.3, min_samples=2)
        
        # Step 4: Display the pipeline metrics exclusively on Terminal output
        print(f"Total Student Answers Processed: {clustering_result['metadata']['total_students']}")
        
        # Display each grouped cluster
        for cluster in clustering_result['clusters']:
            
            # Highlight the Half-Credit isolated 'Edge Case' cluster if it exists
            if cluster["label"] == ["half", "credit", "error"]:
                print(f"\n   [!] DISTINCT HALF-CREDIT CLUSTER DETECTED [!]")
                print(f"       Detected Edge Cases: {cluster['student_ids']}")
                print(f"       Auto-Label: {' | '.join(cluster['label'])}")
            else:
                print(f"\n   -> Cluster ID: {cluster['cluster_id']}")
                print(f"      Semantic Keywords : {' | '.join(cluster['label'])}")
                print(f"      Grouped Students  : {cluster['student_ids']}")
        
        # Output anomalous students entirely rejected by the DBSCAN filter model
        if clustering_result['unclustered']:
            print(f"\n   -> [NOISE] Unclassified / Invalid Outliers: {clustering_result['unclustered']}")
            
        # Optional: Print raw processing cost matrix 
        print(f"\n   >> (Execution Metrics: Embed: {clustering_result['metadata']['embedding_time_seconds']}s | Cluster: {clustering_result['metadata']['clustering_time_seconds']}s)")
        print("\n\n")

if __name__ == "__main__":
    # Supply path pointing up one directory to where your Markdown DocX.md files live
    #old stuff --- target_docs_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    target_docs_folder = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "layer1", "output"))
    run_evaluation(target_docs_folder)

print(f"[DEBUG] PATH: {target_docs_folder}")
print(f"[DEBUG] FILES: {os.listdir(target_docs_folder)}")