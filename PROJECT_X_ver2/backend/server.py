
import os
import sys
import json
import shutil
import tempfile
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ─────────────────────────────────────────────────────────────────────────────
# Path wiring
# server.py lives at:  PROJECT_X/backend/server.py
# PROJECT_X/          = one level up
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LAYER1_DIR   = PROJECT_ROOT / "layer1"
LAYER2_DIR   = PROJECT_ROOT / "layer2" / "pipeline"

sys.path.insert(0, str(LAYER1_DIR))
sys.path.insert(0, str(LAYER2_DIR))

# Load .env BEFORE importing layer1 (it needs GEMINI_API_KEY at import time)
from dotenv import load_dotenv
load_dotenv(LAYER1_DIR / ".env")

# ─────────────────────────────────────────────────────────────────────────────
# Import pipeline modules
# ─────────────────────────────────────────────────────────────────────────────
try:
    from connections import process_file as layer1_process_file
    print("[OK] layer1/connections.py loaded")
except ImportError as e:
    print(f"[ERR] Could not import layer1: {e}")
    raise

try:
    from dict_builder import build_question_dictionaries
    from answer_clustering import cluster_answers
    print("[OK] layer2 pipeline modules loaded")
except ImportError as e:
    print(f"[ERR] Could not import layer2: {e}")
    raise

# ─────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="ExamCluster API",
    version="1.0.0",
    description="OCR + Clustering backend for handwritten exam papers"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # narrow to ["http://localhost:5173"] in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# In-memory store  (swap for a DB / Redis in production)
# ─────────────────────────────────────────────────────────────────────────────
_latest_result: dict = {}


# ─────────────────────────────────────────────────────────────────────────────
# Helper: map layer2 output → frontend shape
# ─────────────────────────────────────────────────────────────────────────────
def _shape_for_frontend(pipeline_output: dict) -> dict:
    """
    layer2 output per question ("Q1", "Q2", ...):
      {
        "clusters": [
          { "cluster_id": int, "label": [kw,...], "student_ids": [...],
            "answers": { sid: text }, "edge_cases": [...] }
        ],
        "unclustered": [str, ...],
        "metadata": { ... }
      }

    Frontend expects per question:
      { id, title, totalAnswers,
        clusters: [
          { id, label, type, confidence, keywords,
            studentCount, language, summary,
            answers: [{studentId, name, text, confidence, lang}],
            grade, maxMarks }
        ]
      }
    """
    questions = []
    all_student_ids: set = set()

    sorted_keys = sorted(
        pipeline_output.keys(),
        key=lambda k: int(k.replace("Q", "")) if k.replace("Q", "").isdigit() else 999
    )

    for q_key in sorted_keys:
        q_data  = pipeline_output[q_key]
        q_num   = int(q_key.replace("Q", "")) if q_key.replace("Q", "").isdigit() else 0
        clusters_raw = q_data.get("clusters", [])
        unclustered  = q_data.get("unclustered", [])

        max_size = max(
            (len(c.get("student_ids", [])) for c in clusters_raw),
            default=0
        )

        frontend_clusters = []

        for idx, c in enumerate(clusters_raw):
            sids         = c.get("student_ids", [])
            answers_dict = c.get("answers", {})
            keywords     = c.get("label", [])
            is_edge      = bool(c.get("edge_cases"))

            # Type heuristic
            if is_edge:
                ctype = "edge-case"
            elif len(sids) == max_size and idx == 0:
                ctype = "correct"
            elif len(sids) > 1:
                ctype = "partial"
            else:
                ctype = "incorrect"

            answer_list = []
            for sid, text in answers_dict.items():
                all_student_ids.add(sid)
                name = (
                    sid.replace("_result.json", "")
                       .replace("_", " ").replace("-", " ")
                       .title().strip()
                )
                answer_list.append({
                    "studentId":  sid,
                    "name":       name,
                    "text":       str(text)[:800],
                    "confidence": 0.85,
                    "lang":       "en"
                })

            label_str  = " | ".join(keywords) if keywords else f"Cluster {idx + 1}"
            confidence = round(max(0.5, 0.95 - idx * 0.07), 2)

            frontend_clusters.append({
                "id":           f"q{q_num}-c{idx}",
                "label":        label_str,
                "type":         ctype,
                "confidence":   confidence,
                "keywords":     keywords,
                "studentCount": len(sids),
                "language":     "English",
                "summary":      f"{len(sids)} student(s) gave semantically similar answers.",
                "answers":      answer_list,
                "grade":        None,
                "maxMarks":     10
            })

        # Unclustered students get their own card
        if unclustered:
            unc_answers = []
            for sid in unclustered:
                all_student_ids.add(sid)
                name = (
                    sid.replace("_result.json", "")
                       .replace("_", " ").replace("-", " ")
                       .title().strip()
                )
                unc_answers.append({
                    "studentId":  sid,
                    "name":       name,
                    "text":       "(Unique answer — did not cluster with others)",
                    "confidence": 0.5,
                    "lang":       "en"
                })
            frontend_clusters.append({
                "id":           f"q{q_num}-unclustered",
                "label":        "Unique / Outlier Answers",
                "type":         "partial",
                "confidence":   0.5,
                "keywords":     ["unique", "outlier"],
                "studentCount": len(unclustered),
                "language":     "English",
                "summary":      f"{len(unclustered)} student(s) had answers unlike any cluster.",
                "answers":      unc_answers,
                "grade":        None,
                "maxMarks":     10
            })

        total_answers = sum(c["studentCount"] for c in frontend_clusters)
        questions.append({
            "id":           q_num,
            "title":        f"Question {q_num}",
            "totalAnswers": total_answers,
            "clusters":     frontend_clusters
        })

    questions.sort(key=lambda q: q["id"])
    total_clusters = sum(len(q["clusters"]) for q in questions)

    return {
        "questions": questions,
        "stats": {
            "totalStudents":  len(all_student_ids),
            "totalSheets":    len(all_student_ids),
            "totalQuestions": len(questions),
            "totalClusters":  total_clusters,
            "processedAt":    datetime.now().isoformat()
        }
    }



@app.get("/api/health")
def health():
    return {
        "status":      "ok",
        "timestamp":   datetime.now().isoformat(),
        "hasClusters": bool(_latest_result)
    }


@app.post("/api/upload")
async def upload_and_process(
    papers:       list[UploadFile] = File(...),
    parent_sheet: UploadFile       = File(...)
):
    """
    Full pipeline:
      1. Save uploaded PDFs to a temp directory
      2. Run layer1 OCR (Gemini Vision) on each PDF -> *_result.json
      3. Run layer2 clustering on the JSON output directory
      4. Shape and store results
      5. Return { status: "success" }
    """
    global _latest_result

    session_id  = str(uuid.uuid4())[:8]
    session_dir = Path(tempfile.mkdtemp(prefix=f"examcluster_{session_id}_"))
    input_dir   = session_dir / "input"
    output_dir  = session_dir / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    print(f"\n[{session_id}] Upload session started — {len(papers)} paper(s)")

    try:
        # 1. Save PDFs
        saved = []
        for upload in papers:
            fname = upload.filename or "unnamed.pdf"
            if not fname.lower().endswith(".pdf"):
                continue
            dest = input_dir / fname
            dest.write_bytes(await upload.read())
            saved.append(str(dest))
            print(f"  Saved: {fname}")

        if not saved:
            raise HTTPException(400, "No valid PDF files uploaded.")

        # Save parent/rubric sheet
        parent_bytes = await parent_sheet.read()
        (session_dir / "parent_sheet.pdf").write_bytes(parent_bytes)

        # 2. Layer 1 — OCR
        ocr_errors = []
        for fp in saved:
            stem = Path(fp).stem
            print(f"\n  [OCR] {Path(fp).name}")
            try:
                result = layer1_process_file(fp)
                out_f  = output_dir / f"{stem}_result.json"
                out_f.write_text(
                    json.dumps(result, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )
                print(f"  [OCR] Done -> {out_f.name}")
            except Exception as e:
                ocr_errors.append(f"{Path(fp).name}: {e}")
                print(f"  [OCR] Error: {e}")

        json_files = list(output_dir.glob("*_result.json"))
        if not json_files:
            detail = "OCR produced no output."
            if ocr_errors:
                detail += " Errors: " + "; ".join(ocr_errors)
            raise HTTPException(500, detail)

        print(f"\n  [OCR] {len(json_files)} result(s) written")

        # 3. Layer 2 — Cluster
        print("  [Cluster] Building question dictionaries...")
        parsed = build_question_dictionaries(str(output_dir))

        pipeline_output = {}
        for q_num, answers_dict in parsed.items():
            if not answers_dict:
                continue
            print(f"  [Cluster] Q{q_num} — {len(answers_dict)} answer(s)")
            pipeline_output[f"Q{q_num}"] = cluster_answers(
                answers_dict, eps=0.3, min_samples=2
            )

        if not pipeline_output:
            raise HTTPException(
                500,
                "Clustering produced no output. "
                "Ensure OCR JSON files have an 'answers' key."
            )

        n_clusters = sum(len(v.get("clusters", [])) for v in pipeline_output.values())
        print(f"  [Cluster] Done — {len(pipeline_output)} question(s), {n_clusters} cluster(s)")

        # 4. Shape and store
        _latest_result = _shape_for_frontend(pipeline_output)

        return JSONResponse(content={
            "status":    "success",
            "session":   session_id,
            "questions": len(pipeline_output),
            "clusters":  n_clusters,
            "sheets":    len(json_files)
        })

    finally:
        shutil.rmtree(session_dir, ignore_errors=True)


@app.get("/api/clusters")
def get_clusters():
    """Returns the most recently processed cluster results."""
    if not _latest_result:
        raise HTTPException(
            404,
            "No cluster data available. Upload answer sheets first."
        )
    return JSONResponse(content=_latest_result)


@app.post("/api/grade")
def save_grade(
    questionId: int   = Body(...),
    clusterId:  str   = Body(...),
    grade:      float = Body(...),
    feedback:   str   = Body(default="")
):
    
    global _latest_result

    if not _latest_result:
        raise HTTPException(404, "No cluster data loaded.")

    for question in _latest_result.get("questions", []):
        if question["id"] == questionId:
            for cluster in question.get("clusters", []):
                if cluster["id"] == clusterId:
                    cluster["grade"]    = grade
                    cluster["feedback"] = feedback
                    return {"status": "saved", "clusterId": clusterId, "grade": grade}

    raise HTTPException(404, f"Cluster '{clusterId}' not found in Q{questionId}.")
