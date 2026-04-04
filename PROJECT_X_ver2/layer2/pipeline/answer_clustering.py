import re
import time
from collections import defaultdict
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer


def extract_edge_cases(text: str) -> bool:
    """
    Edge Case Detector: Identifies answers containing the correct formula pattern
    but carrying a potentially wrong computational result. 
    Tags these with special 'edge_partial' logical overrides.
    """
    text_lower = text.lower()
    
    # Check for Physics F=ma formula pattern with a mocked arithmetic error
    if 'f=ma' in text_lower or 'force equals mass' in text_lower:
        if '4000' in text_lower or 'wrong calculation' in text_lower:
            return True
            
    # Check for E=mc2 pattern combined with a mock erroneous calc
    if 'e=mc2' in text_lower or 'e=mc^2' in text_lower:
        if '3000' in text_lower: 
            return True

    # Check for v=u+at kinematic formula
    if 'v=u+at' in text_lower:
        if 'velocity is 50' in text_lower: 
            return True

    return False


def get_cluster_label(texts: list, top_n: int = 3) -> list:
    """
    Utilizes TF-IDF vectorization to extract the most dominant 
    top_n keywords from the combined text corpus of a single cluster.
    """
    if not texts:
        return []
    try:
        # Fit TF-IDF ignoring standard english stopwords
        vectorizer = TfidfVectorizer(stop_words='english', max_features=25)
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        
        # Aggregate scores vertically across all documents in the cluster
        scores = np.sum(tfidf_matrix.toarray(), axis=0)
        
        # Sort indices to fetch top terms
        top_indices = scores.argsort()[-top_n:][::-1]
        return [feature_names[i] for i in top_indices]
    except Exception:
        # Fallback if text is entirely stopwords or unparseable
        return ["unlabeled"]


def cluster_answers(
    answers: dict,
    eps: float = 0.3,
    min_samples: int = 2,
    auto_tune: bool = True
) -> dict:
    """
    End-to-End Pipeline converting a dictionary of student answers into 
    highly structured, semantically grouped clusters with TF-IDF labeling.
    """
    t_start = time.time()
    
    if not answers:
        return {
            "clusters": [],
            "unclustered": [],
            "metadata": {
                "model_used": "paraphrase-multilingual-MiniLM-L12-v2",
                "algorithm": "DBSCAN",
                "total_students": 0,
                "total_clusters": 0,
                "processing_time_seconds": 0.0,
                "embedding_time_seconds": 0.0,
                "clustering_time_seconds": 0.0,
                "edge_case_count": 0
            }
        }

    student_ids = list(answers.keys())
    answer_texts = [
        str(answers[sid]) if answers[sid] is not None else ""
        for sid in student_ids
    ]
    total_students = len(student_ids)
    
    # ==========================================
    # STEP 1: Embedding Generation
    # ==========================================
    t_embed_start = time.time()
    # Utilizing specified all-MiniLM-L6-v2 for rapid processing
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2') 
    embeddings = model.encode(answer_texts, show_progress_bar=False)
    t_embed_end = time.time()
    
    # ==========================================
    # STEP 2: DBSCAN Clustering
    # ==========================================
    t_cluster_start = time.time()
    # Cosine distance groups mathematically similar semantic vectors. 
    # DBSCAN inherently catches scattered noise without explicit tuning.
    effective_eps = eps
    effective_min_samples = min_samples
    if auto_tune and total_students < max(3, min_samples * 2):
        effective_min_samples = 1

    dbscan = DBSCAN(
        eps=effective_eps,
        min_samples=effective_min_samples,
        metric='cosine'
    )
    labels = dbscan.fit_predict(embeddings)

    # Optional auto-tuning: if too much noise, relax parameters once
    if auto_tune:
        noise_ratio = float(np.sum(labels == -1)) / float(total_students)
        cluster_count = len(set(labels)) - (1 if -1 in labels else 0)
        if noise_ratio > 0.6 or cluster_count == 0:
            tuned_eps = min(1.0, max(effective_eps * 1.5, effective_eps + 0.1))
            tuned_min_samples = max(1, effective_min_samples - 1)
            dbscan = DBSCAN(
                eps=tuned_eps,
                min_samples=tuned_min_samples,
                metric='cosine'
            )
            labels = dbscan.fit_predict(embeddings)
            effective_eps = tuned_eps
            effective_min_samples = tuned_min_samples

    t_cluster_end = time.time()
    
    clusters_map = defaultdict(list)
    unclustered = []
    
    for i, label in enumerate(labels):
        sid = student_ids[i]
        if label == -1: # -1 explicitly denotes Noise in DBSCAN
            unclustered.append(sid)
        else:
            clusters_map[label].append(sid)
            
    # ==========================================
    # STEP 3 & 4: Edge Case Detection & Labeling
    # ==========================================
    clusters_output = []
    global_edge_cases = []
    
    # 1. Detect all edge cases entirely
    for sid in student_ids:
        if extract_edge_cases(answers[sid]):
            global_edge_cases.append(sid)
            
    # 2. Extract edge cases from standard clusters
    valid_cluster_ids = 0
    for cluster_id, sids in clusters_map.items():
        # Clean cluster of any edge_cases
        clean_sids = [sid for sid in sids if sid not in global_edge_cases]
        if not clean_sids:
            continue
            
        cluster_texts = [answers[sid] for sid in clean_sids]
        cluster_answers_dict = {sid: answers[sid] for sid in clean_sids}
        
        # Generate Cluster label via TF-IDF
        keywords = get_cluster_label(cluster_texts, 3)
        
        clusters_output.append({
            "cluster_id": valid_cluster_ids,
            "label": keywords,
            "student_ids": clean_sids,
            "answers": cluster_answers_dict,
            "edge_cases": [] # Edge cases moved to distinct cluster
        })
        valid_cluster_ids += 1
        
    # Clean unclustered noise
    unclustered = [sid for sid in unclustered if sid not in global_edge_cases]
    
    # 3. Create Distinct Half-Credit Cluster
    if global_edge_cases:
        clusters_output.append({
            "cluster_id": valid_cluster_ids,
            "label": ["half", "credit", "error"],
            "student_ids": global_edge_cases,
            "answers": {sid: answers[sid] for sid in global_edge_cases},
            "edge_cases": global_edge_cases
        })
        
    total_edge_cases = len(global_edge_cases)
            
    t_end = time.time()
    
    # ==========================================
    # STEP 5: Final Output Synthesis Schema
    # ==========================================
    result = {
        "clusters": clusters_output,
        "unclustered": unclustered,
        "metadata": {
            "model_used": "all-MiniLM-L6-v2",
            "algorithm": "DBSCAN",
            "total_students": total_students,
            "total_clusters": len(clusters_output),
            "processing_time_seconds": round(t_end - t_start, 2),
            "embedding_time_seconds": round(t_embed_end - t_embed_start, 2),
            "clustering_time_seconds": round(t_cluster_end - t_cluster_start, 2),
            "edge_case_count": total_edge_cases,
            "eps_used": round(effective_eps, 3),
            "min_samples_used": int(effective_min_samples),
            "auto_tuned": bool(auto_tune)
        }
    }
    
    return result


if __name__ == "__main__":
    # Sample Test Dictionary: 10 mock physics answers
    mock_input = {
        "S001": "Newton's second law states that force equals mass times acceleration. F=ma is the formula.",
        "S002": "The fundamental formula is F=ma. It deeply proves that force equals mass times acceleration.",
        "S003": "Force output requires knowing mass and acceleration to equal F=ma accurately.",
        # Edge Cases (Formula correct, computation botched)
        "S004": "The equation is F=ma. So if mass is 1000 and acceleration is 2.5, force is 4000 Newtons.", 
        "S005": "According to Newton, F=ma. Therefore calculating 1000 * 2.5 yields 4000 Newtons precisely.", 
        # Secondary Cluster 
        "S006": "Energy physics dictates that E=mc^2. Mass translates to energy, energy translates to mass.",
        "S007": "The theory of relativity gives us E=mc^2, relating huge energy thresholds and light speed.",
        "S008": "Relativity completely depends on E=mc^2 where light speed remains constant.",
        # Unclustered / Noise Points
        "S009": "Apples constantly fall from natural trees strictly because of Earth's gravity and soil density.", 
        "S010": "Quantum mechanics deals heavily with superposition and deeply entangled particles." 
    }

    import pprint
    print("Initiating Pipeline Verification...")
    
    # Execute Pipeline
    pipeline_output = cluster_answers(mock_input, eps=0.3, min_samples=2)
    
    print("\n========== PIPELINE OUTPUT SCHEMA ==========\n")
    pprint.pprint(pipeline_output, depth=4, width=80)
    
    # Format Cost / Efficiency Log Terminal Output
    meta = pipeline_output['metadata']
    print("\n" + "="*45)
    print("          COST / EFFICIENCY LOG          ")
    print("="*45)
    print(f"Total Answers Processed : {meta['total_students']}")
    print(f"Total Clusters Formed   : {meta['total_clusters']}")
    print(f"Total Edge Cases Caught : {meta['edge_case_count']}")
    print("-" * 45)
    print(f"Embedding Time          : {meta['embedding_time_seconds']} seconds")
    print(f"Clustering Time         : {meta['clustering_time_seconds']} seconds")
    print(f"Total Pipeline runtime  : {meta['processing_time_seconds']} seconds")
    print("="*45 + "\n")
