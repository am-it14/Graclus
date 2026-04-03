"""
COMPACT PIPELINE VALIDATOR - writes results to results.json
"""
import os, sys, json, traceback
sys.path.insert(0, os.path.dirname(__file__))

DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
results = {"layer1": {}, "layer2": {}, "layer3": {}, "issues": []}

# ── LAYER 1: dict_builder ──────────────────────────────────────────────────────
try:
    from dict_builder import build_question_dictionaries
    parsed = build_question_dictionaries(DOCS_DIR)
    
    # Check Q keys
    results["layer1"]["keys_present"] = sorted(parsed.keys())
    results["layer1"]["expected_keys"] = list(range(1, 11))
    results["layer1"]["keys_ok"] = sorted(parsed.keys()) == list(range(1, 11))
    
    # Per-question response counts
    q_counts = {f"Q{k}": len(v) for k, v in parsed.items()}
    results["layer1"]["response_counts"] = q_counts
    results["layer1"]["all_have_10"] = all(v == 10 for v in q_counts.values())
    
    # Key format check
    sample_keys = list(parsed[1].keys())
    results["layer1"]["sample_doc_keys"] = sample_keys[:5]
    results["layer1"]["keys_are_filenames"] = all(os.sep not in k for k in sample_keys)
    
    # Text quality check Q1/Doc1
    q1_doc1 = parsed.get(1, {}).get("Doc1_Standard.md", "")
    results["layer1"]["q1_doc1_preview"] = q1_doc1[:120] if q1_doc1 else "EMPTY"
    results["layer1"]["q1_doc1_empty"] = not bool(q1_doc1)
    results["layer1"]["q1_starts_with_digit"] = bool(q1_doc1 and q1_doc1.strip()[0].isdigit())
    
except Exception as e:
    results["layer1"]["EXCEPTION"] = traceback.format_exc()
    results["issues"].append(f"LAYER1: {e}")


# ── LAYER 2: answer_clustering ─────────────────────────────────────────────────
try:
    from answer_clustering import cluster_answers, extract_edge_cases
    q1_answers = parsed.get(1, {})
    res = cluster_answers(q1_answers, eps=0.3, min_samples=2)
    
    # ID accounting
    all_out = set(res["unclustered"])
    for c in res["clusters"]:
        all_out.update(c["student_ids"])
    input_ids = set(q1_answers.keys())
    results["layer2"]["ids_match"] = all_out == input_ids
    results["layer2"]["missing_ids"] = list(input_ids - all_out)
    results["layer2"]["extra_ids"] = list(all_out - input_ids)
    
    results["layer2"]["total_students"] = res["metadata"]["total_students"]
    results["layer2"]["total_clusters"] = res["metadata"]["total_clusters"]
    results["layer2"]["unclustered"] = res["unclustered"]
    results["layer2"]["edge_case_count"] = res["metadata"]["edge_case_count"]
    
    # Schema keys per cluster
    required_keys = {"cluster_id", "label", "student_ids", "answers", "edge_cases"}
    schema_ok = all(required_keys <= set(c.keys()) for c in res["clusters"])
    results["layer2"]["cluster_schema_ok"] = schema_ok
    
    # Cluster summaries
    results["layer2"]["clusters"] = [
        {"id": c["cluster_id"], "label": c["label"], "sids": c["student_ids"], "edge_cases": c["edge_cases"]}
        for c in res["clusters"]
    ]
    
    # Metadata keys
    required_meta = {"model_used","algorithm","total_students","total_clusters",
                     "processing_time_seconds","embedding_time_seconds","clustering_time_seconds","edge_case_count"}
    results["layer2"]["metadata_ok"] = required_meta <= set(res["metadata"].keys())
    results["layer2"]["metadata"] = res["metadata"]
    
    # Edge case unit tests
    EDGE   = "The formula is F=ma. So 1000 * 2.5 = 4000 Newtons."
    CLEAN  = "F=ma is Newton's second law: force equals mass times acceleration."
    NOISE  = "The weather today is very sunny and warm outside."
    results["layer2"]["edge_detector_tests"] = {
        "edge_text_flagged":   extract_edge_cases(EDGE),   # should be True
        "clean_not_flagged":   not extract_edge_cases(CLEAN),  # should be True
        "noise_not_flagged":   not extract_edge_cases(NOISE),  # should be True
    }
    results["layer2"]["edge_detector_all_pass"] = all(results["layer2"]["edge_detector_tests"].values())

except Exception as e:
    results["layer2"]["EXCEPTION"] = traceback.format_exc()
    results["issues"].append(f"LAYER2: {e}")


# ── LAYER 3: main_pipeline smoke test ─────────────────────────────────────────
try:
    import io, contextlib
    from main_pipeline import run_evaluation
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_evaluation(DOCS_DIR)
    output = buf.getvalue()
    results["layer3"]["all_10_questions_printed"] = all(f"EVALUATING QUESTION {q}" in output for q in range(1, 11))
    results["layer3"]["cluster_output_present"] = ("Cluster ID" in output or "HALF-CREDIT" in output or "Execution Metrics" in output)
    results["layer3"]["output_line_count"] = output.count("\n")

except Exception as e:
    results["layer3"]["EXCEPTION"] = traceback.format_exc()
    results["issues"].append(f"LAYER3: {e}")

# ── Write JSON ─────────────────────────────────────────────────────────────────
with open("results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"Done. Issues found: {len(results['issues'])}")
for iss in results["issues"]:
    print(f"  -> {iss}")
print("Full results written to results.json")
