import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';

const PROCESSING_STEPS = [
  'Uploading files to server...',
  'Extracting pages from PDFs...',
  'Running OCR on handwritten text...',
  'Generating sentence embeddings...',
  'Detecting languages (EN / HI)...',
  'Grouping answers by question number...',
  'Clustering Q1 answers with DBSCAN...',
  'Clustering Q2–Q5 answers...',
  'Clustering Q6–Q10 answers...',
  'Identifying edge-case answers...',
  'Comparing clusters against parent sheet...',
  'Building rubric keyword index...',
  'Finalizing all clusters...',
];

// ─── Replace with your real backend URL ──────────────────────────────────────
const UPLOAD_API_URL = 'http://localhost:8000/api/upload';
// ─────────────────────────────────────────────────────────────────────────────

export default function UploadPage() {
  // ── Answer sheets (multiple PDFs) ─────────────────────────────────────────
  const [answerFiles, setAnswerFiles]       = useState([]);
  const [answerDragging, setAnswerDragging] = useState(false);
  const answerFileRef = useRef(null);

  // ── Parent / rubric sheet (single PDF) ───────────────────────────────────
  const [parentFile, setParentFile]         = useState(null);
  const [parentDragging, setParentDragging] = useState(false);
  const parentFileRef = useRef(null);

  // ── Processing state ──────────────────────────────────────────────────────
  const [processing, setProcessing]     = useState(false);
  const [currentStep, setCurrentStep]   = useState(0);
  const [progress, setProgress]         = useState(0);
  const [uploadError, setUploadError]   = useState(null);

  const navigate = useNavigate();

  // ── Helpers ───────────────────────────────────────────────────────────────
  const formatFileSize = (bytes) => {
    if (bytes < 1024)    return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  };
  const isPDF = (f) => f?.type === 'application/pdf';

  // ── Answer sheets handlers ────────────────────────────────────────────────
  const addAnswerFiles = useCallback((incoming) => {
    const pdfs = Array.from(incoming).filter(isPDF);
    if (!pdfs.length) return;
    setAnswerFiles(prev => {
      const existing = new Set(prev.map(f => `${f.name}-${f.size}`));
      return [...prev, ...pdfs.filter(f => !existing.has(`${f.name}-${f.size}`))];
    });
  }, []);

  const removeAnswerFile = useCallback((index) => {
    setAnswerFiles(prev => prev.filter((_, i) => i !== index));
  }, []);

  const handleAnswerDrop = useCallback((e) => {
    e.preventDefault();
    setAnswerDragging(false);
    addAnswerFiles(e.dataTransfer.files);
  }, [addAnswerFiles]);

  // ── Parent sheet handlers ─────────────────────────────────────────────────
  const handleParentFile = useCallback((f) => {
    if (isPDF(f)) setParentFile(f);
  }, []);

  const handleParentDrop = useCallback((e) => {
    e.preventDefault();
    setParentDragging(false);
    handleParentFile(e.dataTransfer.files[0]);
  }, [handleParentFile]);

  // ── Step ticker (visual feedback while backend works) ─────────────────────
  const startStepTicker = () => {
    let step = 0;
    const id = setInterval(() => {
      step++;
      if (step < PROCESSING_STEPS.length - 1) {
        setCurrentStep(step);
        setProgress(Math.round((step / (PROCESSING_STEPS.length - 1)) * 85));
      } else {
        clearInterval(id);
      }
    }, 3000);
    return id;
  };

  // ── Main upload ───────────────────────────────────────────────────────────
  const canProcess = answerFiles.length > 0 && parentFile !== null;

  const handleProcess = useCallback(async () => {
    if (!canProcess) return;

    setProcessing(true);
    setProgress(0);
    setCurrentStep(0);
    setUploadError(null);

    const tickerId = startStepTicker();

    try {
      const formData = new FormData();

      // Student answer sheets → field "papers" (multiple)
      answerFiles.forEach(f => formData.append('papers', f));

      // Parent / rubric sheet → field "parent_sheet" (single)
      // Backend uses this to compare against clusters and assign
      // suggested grades / cluster types (correct / partial / incorrect)
      formData.append('parent_sheet', parentFile);

      const res = await fetch(UPLOAD_API_URL, {
        method: 'POST',
        body: formData,
        // ⚠️ Do NOT set Content-Type manually — browser sets multipart boundary
      });

      clearInterval(tickerId);

      if (!res.ok) {
        const msg = await res.text();
        throw new Error(`Server error ${res.status}: ${msg}`);
      }

      /*
        Backend flow (server-side):
          1. Save parent_sheet
          2. OCR all papers
          3. Embed + cluster answers
          4. Compare each cluster centroid vs parent_sheet embedding
          5. Assign cluster type (correct / partial / incorrect / edge-case)
          6. Store results — ClustersPage fetches via GET /api/clusters
      */

      setCurrentStep(PROCESSING_STEPS.length - 1);
      setProgress(100);
      setTimeout(() => navigate('/clusters'), 400);

    } catch (err) {
      clearInterval(tickerId);
      setProcessing(false);
      setUploadError(err.message || 'Upload failed. Please try again.');
    }
  }, [canProcess, answerFiles, parentFile, navigate]);

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="app-bg">
      <Navbar activeStep={1} />

      <div className="upload-page">
        <div className="upload-container">

          <div className="upload-hero-icon">📄</div>
          <h1 className="upload-title">
            Upload <span className="gradient-text">Exam Papers</span>
          </h1>
          <p className="upload-description">
            Upload the student answer sheets and the parent answer sheet. The AI pipeline will OCR,
            cluster student answers, and compare each cluster against the parent sheet for grading.
          </p>

          {/* ════════════════════════════════════════════════════════════════
              SECTION 1 — Student Answer Sheets
          ════════════════════════════════════════════════════════════════ */}
          <div className="upload-section">
            <div className="upload-section-header">
              <span className="upload-section-badge">1</span>
              <div>
                <h2 className="upload-section-title">Student Answer Sheets</h2>
                <p className="upload-section-subtitle">
                  One or more scanned PDFs of handwritten student answer sheets
                </p>
              </div>
              {answerFiles.length > 0 && (
                <span className="upload-section-status done">
                  ✅ {answerFiles.length} file{answerFiles.length > 1 ? 's' : ''} ready
                </span>
              )}
            </div>

            {/* Answer drop zone */}
            <div
              className={`upload-dropzone ${answerDragging ? 'dragging' : ''} ${answerFiles.length > 0 ? 'has-file' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setAnswerDragging(true); }}
              onDragLeave={() => setAnswerDragging(false)}
              onDrop={handleAnswerDrop}
              onClick={() => answerFileRef.current?.click()}
            >
              <input
                ref={answerFileRef}
                type="file"
                accept="application/pdf"
                multiple
                style={{ display: 'none' }}
                onChange={(e) => addAnswerFiles(e.target.files)}
              />
              {answerFiles.length === 0 ? (
                <>
                  <div className="dropzone-icon">{answerDragging ? '📥' : '☁️'}</div>
                  <p className="dropzone-text">
                    {answerDragging
                      ? 'Drop PDFs here'
                      : 'Drag & drop answer PDFs, or click to browse'}
                  </p>
                  <p className="dropzone-hint">Multiple files supported • PDF only</p>
                </>
              ) : (
                <>
                  <div className="dropzone-icon">📂</div>
                  <p className="dropzone-text">
                    {answerFiles.length} file{answerFiles.length > 1 ? 's' : ''} selected — drop more to add
                  </p>
                </>
              )}
            </div>

            {/* Answer file list */}
            {answerFiles.length > 0 && (
              <div className="file-list" onClick={(e) => e.stopPropagation()}>
                {answerFiles.map((f, i) => (
                  <div key={`${f.name}-${f.size}`} className="file-preview">
                    <div className="file-preview-icon">📋</div>
                    <div className="file-preview-info">
                      <div className="file-preview-name">{f.name}</div>
                      <div className="file-preview-size">{formatFileSize(f.size)}</div>
                    </div>
                    <button className="file-remove" onClick={() => removeAnswerFile(i)}>✕</button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ── Visual divider ── */}
          <div className="upload-divider">
            <div className="upload-divider-line" />
            <span className="upload-divider-label">+ compare against</span>
            <div className="upload-divider-line" />
          </div>

          {/* ════════════════════════════════════════════════════════════════
              SECTION 2 — Parent / Rubric Answer Sheet
          ════════════════════════════════════════════════════════════════ */}
          <div className="upload-section">
            <div className="upload-section-header">
              <span className="upload-section-badge parent">2</span>
              <div>
                <h2 className="upload-section-title">Parent Answer Sheet</h2>
                <p className="upload-section-subtitle">
                  The model / rubric answer — clusters will be compared against this for grading
                </p>
              </div>
              {parentFile && (
                <span className="upload-section-status done">✅ Ready</span>
              )}
            </div>

            {/* Parent drop zone */}
            <div
              className={`upload-dropzone parent-dropzone ${parentDragging ? 'dragging' : ''} ${parentFile ? 'has-file' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setParentDragging(true); }}
              onDragLeave={() => setParentDragging(false)}
              onDrop={handleParentDrop}
              onClick={() => parentFileRef.current?.click()}
            >
              <input
                ref={parentFileRef}
                type="file"
                accept="application/pdf"
                style={{ display: 'none' }}
                onChange={(e) => handleParentFile(e.target.files[0])}
              />

              {!parentFile ? (
                <>
                  <div className="dropzone-icon">{parentDragging ? '📥' : '📑'}</div>
                  <p className="dropzone-text">
                    {parentDragging
                      ? 'Drop the parent sheet here'
                      : 'Drag & drop parent sheet, or click to browse'}
                  </p>
                  <p className="dropzone-hint">Single PDF only • Model answer / rubric sheet</p>
                </>
              ) : (
                <div
                  className="file-preview"
                  style={{ width: '100%', margin: 0, background: 'transparent', border: 'none' }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="file-preview-icon">✅</div>
                  <div className="file-preview-info">
                    <div className="file-preview-name">{parentFile.name}</div>
                    <div className="file-preview-size">{formatFileSize(parentFile.size)}</div>
                  </div>
                  <button
                    className="file-remove"
                    onClick={(e) => { e.stopPropagation(); setParentFile(null); }}
                  >
                    ✕
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* ── Validation nudges ── */}
          {answerFiles.length > 0 && !parentFile && (
            <div className="upload-hint-banner">
              📑 Also upload the parent answer sheet to enable cluster comparison.
            </div>
          )}
          {answerFiles.length === 0 && parentFile && (
            <div className="upload-hint-banner">
              📋 Also upload at least one student answer sheet.
            </div>
          )}

          {/* ── Error banner ── */}
          {uploadError && (
            <div className="upload-error-banner">⚠️ {uploadError}</div>
          )}

          {/* ── CTA + checklist ── */}
          <div className="upload-actions">
            <button
              className="btn-primary"
              disabled={!canProcess || processing}
              onClick={handleProcess}
            >
               Process &amp; Cluster
              {answerFiles.length > 1 ? ` ${answerFiles.length} Files` : ''}
            </button>

            <div className="upload-checklist">
              <span className={`upload-check ${answerFiles.length > 0 ? 'done' : ''}`}>
                {answerFiles.length > 0 ? '✅' : '⬜'}&nbsp;
                Student sheets&nbsp;
                <span style={{ opacity: 0.6 }}>
                  ({answerFiles.length} file{answerFiles.length !== 1 ? 's' : ''})
                </span>
              </span>
              <span className={`upload-check ${parentFile ? 'done' : ''}`}>
                {parentFile ? '✅' : '⬜'}&nbsp;Parent answer sheet
              </span>
            </div>
          </div>

        </div>
      </div>

      {/* ── Processing overlay ── */}
      {processing && (
        <div className="processing-overlay">
          <div className="processing-card">
            <div className="processing-spinner" />
            <h3 className="processing-title">Processing Your Papers</h3>
            <p className="processing-step">{PROCESSING_STEPS[currentStep]}</p>
            <div className="processing-bar-track">
              <div className="processing-bar-fill" style={{ width: `${progress}%` }} />
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 12 }}>
              {progress}% complete —{' '}
              {answerFiles.length} answer sheet{answerFiles.length > 1 ? 's' : ''} + parent sheet
            </p>
          </div>
        </div>
      )}
    </div>
  );
}