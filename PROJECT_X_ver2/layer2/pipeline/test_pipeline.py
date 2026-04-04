import os, sys
sys.path.insert(0, os.path.dirname(__file__))

DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

print("\n" + "="*60)
print("  LAYER 1: dict_builder.build_question_dictionaries()")
print("="*60)

from dict_builder import build_question_dictionaries

parsed = build_question_dictionaries(DOCS_DIR)

# 1a. All 10 question keys must be present
print(f"\n[1a] Question keys present: {sorted(parsed.keys())}")
assert sorted(parsed.keys()) == list(range(1, 11)), f"{FAIL} Expected keys 1-10"
print(f"  {PASS} Keys 1-10 all present")

# 1b. Each question should have exactly 10 responses (one per doc)
for q_num, answers in parsed.items():
    count = len(answers)
    status = PASS if count == 10 else FAIL
    print(f"  {status} Q{q_num}: {count} responses extracted | Docs: {list(answers.keys())}")

# 1c. Verify that text is non-empty and does NOT start with a digit followed by '.'
print("\n[1c] Spot-checking answer text quality (Q1 from Doc1_Standard.md):")
q1_doc1 = parsed.get(1, {}).get("Doc1_Standard.md", "")
if not q1_doc1:
    print(f"  {FAIL} Q1/Doc1_Standard.md returned empty string!")
elif q1_doc1.strip()[0].isdigit():
    print(f"  {WARN} Answer text starts with a digit — possible parse bleed: {q1_doc1[:80]!r}")
else:
    print(f"  {PASS} Text clean. Preview: {q1_doc1[:100]!r}")

# 1d. Verify keys are filenames, not paths
print("\n[1d] Key format check (should be filename only, not full path):")
sample_keys = list(parsed[1].keys())
for k in sample_keys[:3]:
    if os.sep in k:
        print(f"  {FAIL} Key contains path separator: {k!r}")
    else:
        print(f"  {PASS} Key is filename only: {k!r}")

print("\n" + "="*60)
print("  LAYER 2: answer_clustering.cluster_answers()")
print("="*60)

from answer_clustering import cluster_answers, extract_edge_cases

# 2a. Test with a known-good minimal dictionary (5 items)
print("\n[2a] Clustering Q1 answers from parsed data:")
q1_answers = parsed[1]
result = cluster_answers(q1_answers, eps=0.3, min_samples=2)

total_students = result['metadata']['total_students']
total_clusters = result['metadata']['total_clusters']
unclustered = result['unclustered']
edge_count = result['metadata']['edge_case_count']

print(f"  Total students fed in   : {total_students}")
print(f"  Total clusters formed   : {total_clusters}")
print(f"  Unclustered (noise)     : {unclustered}")
print(f"  Edge cases detected     : {edge_count}")

# Each input student_id should appear exactly once in output
all_output_ids = set(unclustered)
for cluster in result['clusters']:
    for sid in cluster['student_ids']:
        if sid in all_output_ids:
            print(f"  {FAIL} Duplicate student ID in output: {sid}")
        all_output_ids.add(sid)
input_ids = set(q1_answers.keys())
if all_output_ids == input_ids:
    print(f"  {PASS} All {total_students} student IDs accounted for exactly once in output")
else:
    missing = input_ids - all_output_ids
    extra   = all_output_ids - input_ids
    print(f"  {FAIL} ID mismatch — Missing: {missing} | Extra: {extra}")

# 2b. Cluster schema keys check
print("\n[2b] Cluster schema key validation:")
required_keys = {"cluster_id", "label", "student_ids", "answers", "edge_cases"}
for c in result['clusters']:
    missing_keys = required_keys - set(c.keys())
    if missing_keys:
        print(f"  {FAIL} Cluster {c['cluster_id']} missing keys: {missing_keys}")
    else:
        label_str = " | ".join(c['label'])
        print(f"  {PASS} Cluster {c['cluster_id']} schema OK | Label: [{label_str}] | Students: {c['student_ids']}")

# 2c. Metadata keys present
print("\n[2c] Metadata schema validation:")
required_meta = {"model_used", "algorithm", "total_students", "total_clusters",
                 "processing_time_seconds", "embedding_time_seconds", "clustering_time_seconds", "edge_case_count"}
missing_meta = required_meta - set(result['metadata'].keys())
if missing_meta:
    print(f"  {FAIL} Missing metadata keys: {missing_meta}")
else:
    print(f"  {PASS} All metadata keys present")
    print(f"       Model: {result['metadata']['model_used']} | Algo: {result['metadata']['algorithm']}")
    print(f"       Embed: {result['metadata']['embedding_time_seconds']}s | Cluster: {result['metadata']['clustering_time_seconds']}s")

# 2d. Edge case detection unit test (known formula + wrong calculation)
print("\n[2d] Edge case detector unit test:")
KNOWN_EDGE   = "The formula is F=ma. So 1000 * 2.5 = 4000 Newtons."
KNOWN_CLEAN  = "F=ma is Newton's second law: force equals mass times acceleration."
KNOWN_NOISE  = "The weather today is very sunny and warm outside."
for text, expected, label in [
    (KNOWN_EDGE, True, "edge case text"),
    (KNOWN_CLEAN, False, "clean correct answer"),
    (KNOWN_NOISE, False, "irrelevant noise"),
]:
    got = extract_edge_cases(text)
    status = PASS if got == expected else FAIL
    print(f"  {status} extract_edge_cases({label!r}): expected={expected}, got={got}")


print("\n" + "="*60)
print("  LAYER 3: main_pipeline.run_evaluation() — smoke test")
print("="*60)

from main_pipeline import run_evaluation
import io, contextlib

output_buf = io.StringIO()
try:
    with contextlib.redirect_stdout(output_buf):
        run_evaluation(DOCS_DIR)
    captured = output_buf.getvalue()
    
    # Verify each question block appears in terminal output
    all_present = all(f"EVALUATING QUESTION {q}" in captured for q in range(1, 11))
    status = PASS if all_present else FAIL
    print(f"  {status} All 10 question blocks appear in terminal output")
    
    # Verify clustering results appear
    if "Cluster ID" in captured or "HALF-CREDIT" in captured or "Execution Metrics" in captured:
        print(f"  {PASS} Clustering output sections detected in terminal")
    else:
        print(f"  {FAIL} No clustering result lines found in terminal output")
        
except Exception as e:
    print(f"  {FAIL} main_pipeline raised an exception: {e}")


print("\n" + "="*60)
print("  DIAGNOSTIC COMPLETE")
print("="*60 + "\n")
