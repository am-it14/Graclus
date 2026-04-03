import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';

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

const AVATAR_COLORS = ['av-1', 'av-2', 'av-3', 'av-4'];

// ─── Replace with your real backend clusters URL ─────────────────────────────
const CLUSTERS_API_URL = 'http://localhost:8000/api/clusters';
// ────────────────────────────────────────────────────────────────────────────

// ── Field resolvers: handle different backend naming conventions ──────────────
const getType         = (c) => c.type          || c.cluster_type    || 'partial';
const getLang         = (c) => c.language       || c.lang            || 'EN';
const getStudentCount = (c) => c.studentCount   ?? c.student_count   ?? c.answers?.length ?? 0;
const getConfidence   = (c) => c.confidence     ?? c.avg_confidence  ?? 0;
const getAnswers      = (c) => c.answers        || c.students        || [];
const getMaxMarks     = (c) => c.maxMarks       ?? c.max_marks       ?? c.max_score ?? 10;
const getKeywords     = (c) => c.keywords       || c.rubric_keywords || [];
const getLabel        = (c) => c.label          || c.cluster_label   || 'Cluster';
const getSummary      = (c) => c.summary        || c.description     || '';
const getGrade        = (c) => c.grade          ?? c.assigned_grade  ?? null;
const getClusters     = (q) => q.clusters       || q.answer_clusters || [];
const getTotalAnswers = (q) => q.totalAnswers    ?? q.total_answers   ?? q.answer_count ?? 0;
const getQTitle       = (q) => q.title          || q.question_text   || q.question     || `Question ${q.id}`;
// ─────────────────────────────────────────────────────────────────────────────

export default function ClustersPage({ questions, setQuestions, stats, setStats }) {
  const navigate = useNavigate();
  const [expandedQ, setExpandedQ] = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);

  // ── Fetch clusters from backend on mount ──────────────────────────────────
  useEffect(() => {
    const fetchClusters = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(CLUSTERS_API_URL);
        if (!res.ok) throw new Error(`Server error ${res.status}`);
        const data = await res.json();

        /*
          Handles either backend response shape:
            { questions: [...], stats: {...} }
          OR directly:
            [ ...questions array... ]
        */
        if (Array.isArray(data)) {
          setQuestions(data);
        } else {
          setQuestions(data.questions || []);
          if (data.stats && setStats) setStats(data.stats);
        }
      } catch (err) {
        setError(err.message || 'Failed to load clusters.');
      } finally {
        setLoading(false);
      }
    };

    fetchClusters();
  }, []); // runs once on mount

  const data = questions || [];
  const st   = stats    || {};

  const totalClusters  = data.reduce((sum, q) => sum + getClusters(q).length, 0);
  const gradedClusters = data.reduce(
    (sum, q) => sum + getClusters(q).filter(c => getGrade(c) !== null).length,
    0
  );

  const getQuestionProgress = (q) => {
    const clusters = getClusters(q);
    const graded   = clusters.filter(c => getGrade(c) !== null).length;
    const total    = clusters.length;
    return { graded, total, percent: total > 0 ? Math.round((graded / total) * 100) : 0 };
  };

  const toggleExpand = (qId) => setExpandedQ(expandedQ === qId ? null : qId);

  // ── Loading ───────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="app-bg">
        <Navbar activeStep={2} />
        <div className="clusters-page" style={{ textAlign: 'center', paddingTop: 80 }}>
          <div className="processing-spinner" style={{ margin: '0 auto 24px' }} />
          <h2 style={{ color: 'var(--text-primary)' }}>Loading clusters…</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Fetching processed data from server</p>
        </div>
      </div>
    );
  }

  // ── Error ─────────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="app-bg">
        <Navbar activeStep={2} />
        <div className="clusters-page" style={{ textAlign: 'center', paddingTop: 80 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
          <h2 style={{ color: 'var(--text-primary)' }}>Failed to load clusters</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>{error}</p>
          <button className="btn-primary" onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  // ── Empty ─────────────────────────────────────────────────────────────────
  if (data.length === 0) {
    return (
      <div className="app-bg">
        <Navbar activeStep={2} />
        <div className="clusters-page" style={{ textAlign: 'center', paddingTop: 80 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📭</div>
          <h2 style={{ color: 'var(--text-primary)' }}>No clusters yet</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>
            Upload and process exam papers first.
          </p>
          <button className="btn-primary" onClick={() => navigate('/')}>← Go to Upload</button>
        </div>
      </div>
    );
  }

  // ── Main render ───────────────────────────────────────────────────────────
  return (
    <div className="app-bg">
      <Navbar activeStep={2} />

      <div className="clusters-page">
        <div className="page-header">
          <h1>Answer Clusters by Question</h1>
          <p>
            {data.length} questions • {totalClusters} total clusters •{' '}
            <strong style={{ color: 'var(--accent-emerald)' }}>{gradedClusters}</strong> / {totalClusters} graded
          </p>
        </div>

        {/* Stats bar */}
        <div className="stats-bar">
          <div className="stat-card">
            <div className="stat-label">Total Sheets</div>
            <div className="stat-value indigo">{st.totalSheets ?? st.total_sheets ?? st.sheet_count ?? '—'}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Questions</div>
            <div className="stat-value cyan">{st.totalQuestions ?? st.total_questions ?? data.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Total Clusters</div>
            <div className="stat-value emerald">{st.totalClusters ?? st.total_clusters ?? totalClusters}</div>
          </div>
        </div>

        {/* Question list */}
        <div className="questions-list">
          {data.map((question, qIndex) => {
            const clusters   = getClusters(question);
            const prog       = getQuestionProgress(question);
            const isExpanded = expandedQ === question.id;

            return (
              <div
                key={question.id}
                className={`question-box ${isExpanded ? 'expanded' : ''}`}
                style={{ animationDelay: `${qIndex * 0.06}s` }}
              >
                {/* Question header */}
                <div className="question-header" onClick={() => toggleExpand(question.id)}>
                  <div className="question-number">Q{question.id}</div>
                  <div className="question-info">
                    <h2 className="question-title">{getQTitle(question)}</h2>
                    <div className="question-meta">
                      <span>{getTotalAnswers(question)} answers</span>
                      <span>•</span>
                      <span>{clusters.length} clusters</span>
                      <span>•</span>
                      <span className={prog.graded === prog.total ? 'text-emerald' : ''}>
                        {prog.graded}/{prog.total} graded
                      </span>
                    </div>
                  </div>
                  <div className="question-progress-wrap">
                    <div className="question-progress-bar">
                      <div className="question-progress-fill" style={{ width: `${prog.percent}%` }} />
                    </div>
                    <span className="question-progress-label">{prog.percent}%</span>
                  </div>
                  <div className={`question-expand-icon ${isExpanded ? 'rotated' : ''}`}>▾</div>
                </div>

                {/* Expanded cluster cards */}
                {isExpanded && (
                  <div className="question-clusters">
                    <div className="question-clusters-grid">
                      {clusters.map((cluster, cIndex) => {
                        const type         = getType(cluster);
                        const answers      = getAnswers(cluster);
                        const studentCount = getStudentCount(cluster);
                        const confidence   = getConfidence(cluster);
                        const keywords     = getKeywords(cluster);
                        const grade        = getGrade(cluster);
                        const maxMarks     = getMaxMarks(cluster);

                        return (
                          <div
                            key={cluster.id}
                            className={`cluster-mini-card type-${type}`}
                            style={{ animationDelay: `${cIndex * 0.05}s` }}
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/grade/${question.id}/${cluster.id}`);
                            }}
                          >
                            <div className="cluster-mini-header">
                              <span className={`cluster-type-badge ${TYPE_BADGES[type] || 'badge-partial'}`}>
                                {TYPE_LABELS[type] || type}
                              </span>
                              <span className="cluster-lang-badge">🌐 {getLang(cluster)}</span>
                              <span className={`grade-badge ${grade !== null ? 'graded' : 'ungraded'}`}>
                                {grade !== null ? `${grade}/${maxMarks}` : 'Not Graded'}
                              </span>
                            </div>

                            <h4 className="cluster-mini-title">{getLabel(cluster)}</h4>
                            <p className="cluster-mini-summary">{getSummary(cluster)}</p>

                            <div className="cluster-keywords">
                              {keywords.slice(0, 5).map((kw) => (
                                <span key={kw} className="keyword-chip">{kw}</span>
                              ))}
                              {keywords.length > 5 && (
                                <span className="keyword-chip" style={{ opacity: 0.5 }}>
                                  +{keywords.length - 5}
                                </span>
                              )}
                            </div>

                            <div className="cluster-mini-footer">
                              <div className="cluster-students">
                                <div className="student-avatars">
                                  {answers.slice(0, 3).map((a, i) => (
                                    <div
                                      key={a.studentId || a.student_id || i}
                                      className={`student-avatar ${AVATAR_COLORS[i]}`}
                                    >
                                      {(a.name || a.student_name || '?').split(' ').map(n => n[0]).join('')}
                                    </div>
                                  ))}
                                </div>
                                <span className="cluster-mini-count">{studentCount} students</span>
                              </div>
                              <span className="cluster-mini-conf">
                                {(confidence * 100).toFixed(0)}% conf
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}