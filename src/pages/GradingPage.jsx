import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';

// ─── Backend grade endpoint ───────────────────────────────────────────────────
const GRADE_API_URL = 'http://localhost:8000/api/grade';
// ─────────────────────────────────────────────────────────────────────────────

const TYPE_BADGES = {
  correct:    'badge-correct',
  'edge-case':'badge-edge-case',
  partial:    'badge-partial',
  incorrect:  'badge-incorrect',
  blank:      'badge-blank',
};

const TYPE_LABELS = {
  correct:    'Correct',
  'edge-case':'Edge Case',
  partial:    'Partial',
  incorrect:  'Incorrect',
  blank:      'Blank',
};

function highlightKeywords(text, keywords) {
  if (!text || !keywords || keywords.length === 0) return text;

  const escaped = keywords.map(k =>
    k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  );
  const regex = new RegExp(`(${escaped.join('|')})`, 'gi');

  const parts = text.split(regex);
  return parts.map((part, i) => {
    if (keywords.some(k => k.toLowerCase() === part.toLowerCase())) {
      return <span key={i} className="keyword-highlight">{part}</span>;
    }
    return part;
  });
}

export default function GradingPage({ questions, setQuestions }) {
  const { questionId, clusterId } = useParams();
  const navigate = useNavigate();
  const [gradeValue, setGradeValue] = useState('');
  const [feedback, setFeedback]     = useState('');
  const [showToast, setShowToast]   = useState(false);
  const [saving, setSaving]         = useState(false);

  // ── If navigated directly (no React state), redirect to upload ──────────
  if (!questions || questions.length === 0) {
    return (
      <div className="app-bg">
        <Navbar activeStep={3} />
        <div className="grading-page" style={{ textAlign: 'center', paddingTop: 80 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📭</div>
          <h2 style={{ color: 'var(--text-primary)' }}>No data loaded</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>
            Please upload and process answer sheets first.
          </p>
          <Link to="/" className="btn-primary" style={{ display: 'inline-flex' }}>
            ← Go to Upload
          </Link>
        </div>
      </div>
    );
  }

  const question = useMemo(
    () => questions.find(q => q.id === parseInt(questionId)),
    [questions, questionId]
  );

  const cluster = useMemo(
    () => question?.clusters?.find(c => c.id === clusterId),
    [question, clusterId]
  );

  // Pre-fill grade input if already graded
  useEffect(() => {
    if (cluster?.grade !== null && cluster?.grade !== undefined) {
      setGradeValue(String(cluster.grade));
    }
  }, [cluster]);

  if (!question || !cluster) {
    return (
      <div className="app-bg">
        <Navbar activeStep={3} />
        <div className="grading-page" style={{ textAlign: 'center', paddingTop: 80 }}>
          <h2>Cluster not found</h2>
          <Link to="/clusters" className="btn-secondary" style={{ marginTop: 20, display: 'inline-flex' }}>
            ← Back to Clusters
          </Link>
        </div>
      </div>
    );
  }

  const handleApplyGrade = async () => {
    const numericGrade = parseFloat(gradeValue);
    if (isNaN(numericGrade) || numericGrade < 0 || numericGrade > cluster.maxMarks) return;

    // 1. Update local React state immediately (instant UI feedback)
    const updated = questions.map(q => {
      if (q.id !== question.id) return q;
      return {
        ...q,
        clusters: q.clusters.map(c =>
          c.id === cluster.id ? { ...c, grade: numericGrade, feedback } : c
        ),
      };
    });
    setQuestions(updated);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);

    // 2. Persist to backend (non-blocking — UI already updated)
    setSaving(true);
    try {
      await fetch(GRADE_API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          questionId: question.id,
          clusterId:  cluster.id,
          grade:      numericGrade,
          feedback:   feedback
        })
      });
    } catch (e) {
      // Backend save failed — grade is still saved locally in React state
      console.warn('Grade save to backend failed (grade kept locally):', e);
    } finally {
      setSaving(false);
    }
  };

  const isValidGrade = (() => {
    const num = parseFloat(gradeValue);
    return !isNaN(num) && num >= 0 && num <= cluster.maxMarks;
  })();

  const getConfidenceClass = (conf) => {
    if (conf >= 0.85) return '';
    if (conf >= 0.6)  return 'medium';
    return 'low';
  };

  return (
    <div className="app-bg">
      <Navbar activeStep={3} />

      <div className="grading-page">
        {/* Header */}
        <div className="grading-header">
          <Link to="/clusters" className="grading-back">← Back to Clusters</Link>

          <div className="grading-question-badge">
            <span className="question-number-inline">Q{question.id}</span>
            <span className="question-title-inline">{question.title}</span>
          </div>

          <div className="grading-cluster-info">
            <h1>{cluster.label}</h1>
            <span className={`cluster-type-badge ${TYPE_BADGES[cluster.type] || 'badge-partial'}`}>
              {TYPE_LABELS[cluster.type] || cluster.type}
            </span>
            <span className="cluster-lang-badge">🌐 {cluster.language || 'English'}</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', marginTop: 8, fontSize: 14 }}>
            {cluster.summary}
          </p>
        </div>

        {/* Grade panel */}
        <div className="grade-panel">
          <div className="grade-panel-title">
            Assign Grade to All {cluster.studentCount} Students in This Cluster
          </div>
          <div className="grade-input-row">
            <div className="grade-input-group">
              <label>Score:</label>
              <input
                className="grade-input"
                type="number"
                min="0"
                max={cluster.maxMarks}
                step="0.5"
                value={gradeValue}
                onChange={(e) => setGradeValue(e.target.value)}
                placeholder="0"
              />
              <span className="grade-max">/ {cluster.maxMarks}</span>
            </div>

            <div className="grade-feedback">
              <textarea
                placeholder="Optional feedback for this cluster..."
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                rows={1}
              />
            </div>

            <button
              className="btn-apply-grade"
              disabled={!isValidGrade || saving}
              onClick={handleApplyGrade}
            >
              {saving ? 'Saving…' : `✓ Apply to ${cluster.studentCount} Students`}
            </button>
          </div>
          <p className="grade-apply-info">
            This grade will be applied to <strong>{cluster.studentCount} students</strong> simultaneously for Q{question.id}.
            {cluster.grade !== null && cluster.grade !== undefined && (
              <span> Currently graded: <strong>{cluster.grade}/{cluster.maxMarks}</strong></span>
            )}
          </p>
        </div>

        {/* Keywords */}
        <div style={{ marginBottom: 'var(--space-lg)' }}>
          <div className="answers-section-title">Rubric Keywords</div>
          <div className="cluster-keywords">
            {(cluster.keywords || []).map((kw) => (
              <span key={kw} className="keyword-chip">{kw}</span>
            ))}
            {(!cluster.keywords || cluster.keywords.length === 0) && (
              <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>No keywords extracted</span>
            )}
          </div>
        </div>

        {/* Student answers */}
        <div className="answers-section-title">
          Student Answers ({(cluster.answers || []).length} shown of {cluster.studentCount})
        </div>

        {(cluster.answers || []).map((answer, index) => (
          <div
            key={answer.studentId || index}
            className="answer-card"
            style={{ animationDelay: `${index * 0.06}s` }}
          >
            <div className="answer-card-header">
              <div className="answer-student">
                <div className="answer-student-avatar">
                  {(answer.name || '?').split(' ').map(n => n[0]).join('').slice(0, 2)}
                </div>
                <div>
                  <div className="answer-student-name">{answer.name || 'Unknown'}</div>
                  <div className="answer-student-id">{answer.studentId}</div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span className="answer-lang-badge">
                  {answer.lang === 'hi' ? '🇮🇳 Hindi' : '🇬🇧 English'}
                </span>
                <div className="answer-confidence">
                  <div className="confidence-bar">
                    <div
                      className={`confidence-fill ${getConfidenceClass(answer.confidence)}`}
                      style={{ width: `${(answer.confidence || 0) * 100}%` }}
                    />
                  </div>
                  <span>{((answer.confidence || 0) * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>

            <div className="answer-text">
              {answer.text
                ? highlightKeywords(answer.text, cluster.keywords || [])
                : <em style={{ color: 'var(--text-muted)' }}>No text extracted</em>
              }
            </div>
          </div>
        ))}
      </div>

      {showToast && (
        <div className="toast">
          ✅ Grade {gradeValue}/{cluster.maxMarks} applied to {cluster.studentCount} students (Q{question.id})
        </div>
      )}
    </div>
  );
}
