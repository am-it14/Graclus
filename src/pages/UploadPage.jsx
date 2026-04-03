import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { mockQuestions, processingStats } from '../data/mockData';

const PROCESSING_STEPS = [
  'Extracting pages from PDF...',
  'Running OCR on handwritten text...',
  'Generating sentence embeddings...',
  'Detecting languages (EN / HI)...',
  'Grouping answers by question number...',
  'Clustering Q1 answers with DBSCAN...',
  'Clustering Q2–Q5 answers...',
  'Clustering Q6–Q10 answers...',
  'Identifying edge-case answers...',
  'Building rubric keyword index...',
  'Finalizing all clusters...',
];

export default function UploadPage({ setQuestions, setStats }) {
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const fileRef = useRef(null);
  const navigate = useNavigate();

  const handleFile = useCallback((f) => {
    if (f && f.type === 'application/pdf') {
      setFile(f);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    handleFile(f);
  }, [handleFile]);

  const handleProcess = useCallback(() => {
    setProcessing(true);
    setProgress(0);
    setCurrentStep(0);

    const totalDuration = 4000;
    const stepInterval = totalDuration / PROCESSING_STEPS.length;
    let step = 0;

    const stepTimer = setInterval(() => {
      step++;
      if (step < PROCESSING_STEPS.length) {
        setCurrentStep(step);
        setProgress(Math.round((step / PROCESSING_STEPS.length) * 100));
      } else {
        clearInterval(stepTimer);
        setProgress(100);
        setTimeout(() => {
          setQuestions(mockQuestions);
          setStats(processingStats);
          navigate('/clusters');
        }, 400);
      }
    }, stepInterval);
  }, [setQuestions, setStats, navigate]);

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  };

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
            Upload a scanned PDF of handwritten answer sheets. Our AI pipeline will OCR the text,
            group answers by question number, and cluster similar answers for each question automatically.
          </p>

          <div
            className={`upload-dropzone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
          >
            <input
              ref={fileRef}
              type="file"
              accept="application/pdf"
              style={{ display: 'none' }}
              onChange={(e) => handleFile(e.target.files[0])}
            />

            {!file ? (
              <>
                <div className="dropzone-icon">
                  {dragging ? '📥' : '☁️'}
                </div>
                <p className="dropzone-text">
                  {dragging ? 'Drop your PDF here' : 'Drag & drop your PDF here, or click to browse'}
                </p>
                <p className="dropzone-hint">Supports scanned handwritten answer sheets • PDF only • 100 papers × 10 questions</p>
              </>
            ) : (
              <>
                <div className="dropzone-icon">✅</div>
                <p className="dropzone-text">File selected</p>
                <div className="file-preview" onClick={(e) => e.stopPropagation()}>
                  <div className="file-preview-icon">📋</div>
                  <div className="file-preview-info">
                    <div className="file-preview-name">{file.name}</div>
                    <div className="file-preview-size">{formatFileSize(file.size)}</div>
                  </div>
                  <button
                    className="file-remove"
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                    }}
                  >
                    ✕
                  </button>
                </div>
              </>
            )}
          </div>

          <div className="upload-actions">
            <button
              className="btn-primary"
              disabled={!file}
              onClick={handleProcess}
            >
               Process & Cluster Answers
            </button>
            {/* <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              Typically takes 5–8 minutes for 100 sheets × 10 questions
            </p> */}
          </div>
        </div>
      </div>

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
              {progress}% complete
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
