import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { mockQuestions, processingStats } from '../data/mockData';

const TYPE_BADGES = {
  correct: 'badge-correct',
  'edge-case': 'badge-edge-case',
  partial: 'badge-partial',
  incorrect: 'badge-incorrect',
  blank: 'badge-blank',
};

const TYPE_LABELS = {
  correct: 'Correct',
  'edge-case': 'Edge Case',
  partial: 'Partial',
  incorrect: 'Incorrect',
  blank: 'Blank',
};

const AVATAR_COLORS = ['av-1', 'av-2', 'av-3', 'av-4'];

export default function ClustersPage({ questions, setQuestions, stats }) {
  const navigate = useNavigate();
  const [expandedQ, setExpandedQ] = useState(null);

  useEffect(() => {
    if (!questions) {
      setQuestions(mockQuestions);
    }
  }, [questions, setQuestions]);

  const data = questions || mockQuestions;
  const st = stats || processingStats;

  const totalClusters = data.reduce((sum, q) => sum + q.clusters.length, 0);
  const gradedClusters = data.reduce(
    (sum, q) => sum + q.clusters.filter(c => c.grade !== null).length,
    0
  );

  const getQuestionProgress = (q) => {
    const graded = q.clusters.filter(c => c.grade !== null).length;
    return { graded, total: q.clusters.length, percent: Math.round((graded / q.clusters.length) * 100) };
  };

  const toggleExpand = (qId) => {
    setExpandedQ(expandedQ === qId ? null : qId);
  };

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
            <div className="stat-value indigo">{st.totalSheets}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Questions</div>
            <div className="stat-value cyan">{st.totalQuestions}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Total Clusters</div>
            <div className="stat-value emerald">{st.totalClusters}</div>
          </div>
          {/* <div className="stat-card">
            <div className="stat-label">Processing Time</div>
            <div className="stat-value amber">{st.totalTime}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Tokens Used</div>
            <div className="stat-value violet">{st.tokensUsed.toLocaleString()}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Est. Cost</div>
            <div className="stat-value rose">{st.estimatedCost}</div>
          </div> */}
        </div>

        {/* Question boxes */}
        <div className="questions-list">
          {data.map((question, qIndex) => {
            const prog = getQuestionProgress(question);
            const isExpanded = expandedQ === question.id;

            return (
              <div
                key={question.id}
                className={`question-box ${isExpanded ? 'expanded' : ''}`}
                style={{ animationDelay: `${qIndex * 0.06}s` }}
              >
                {/* Question header — clickable to expand/collapse */}
                <div className="question-header" onClick={() => toggleExpand(question.id)}>
                  <div className="question-number">Q{question.id}</div>
                  <div className="question-info">
                    <h2 className="question-title">{question.title}</h2>
                    <div className="question-meta">
                      <span>{question.totalAnswers} answers</span>
                      <span>•</span>
                      <span>{question.clusters.length} clusters</span>
                      <span>•</span>
                      <span className={prog.graded === prog.total ? 'text-emerald' : ''}>
                        {prog.graded}/{prog.total} graded
                      </span>
                    </div>
                  </div>
                  <div className="question-progress-wrap">
                    <div className="question-progress-bar">
                      <div
                        className="question-progress-fill"
                        style={{ width: `${prog.percent}%` }}
                      />
                    </div>
                    <span className="question-progress-label">{prog.percent}%</span>
                  </div>
                  <div className={`question-expand-icon ${isExpanded ? 'rotated' : ''}`}>
                    ▾
                  </div>
                </div>

                {/* Expanded cluster cards */}
                {isExpanded && (
                  <div className="question-clusters">
                    <div className="question-clusters-grid">
                      {question.clusters.map((cluster, cIndex) => (
                        <div
                          key={cluster.id}
                          className={`cluster-mini-card type-${cluster.type}`}
                          style={{ animationDelay: `${cIndex * 0.05}s` }}
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/grade/${question.id}/${cluster.id}`);
                          }}
                        >
                          <div className="cluster-mini-header">
                            <span className={`cluster-type-badge ${TYPE_BADGES[cluster.type]}`}>
                              {TYPE_LABELS[cluster.type]}
                            </span>
                            <span className="cluster-lang-badge">🌐 {cluster.language}</span>
                            <span className={`grade-badge ${cluster.grade !== null ? 'graded' : 'ungraded'}`}>
                              {cluster.grade !== null ? `${cluster.grade}/${cluster.maxMarks}` : 'Not Graded'}
                            </span>
                          </div>

                          <h4 className="cluster-mini-title">{cluster.label}</h4>

                          <p className="cluster-mini-summary">{cluster.summary}</p>

                          <div className="cluster-keywords">
                            {cluster.keywords.slice(0, 5).map((kw) => (
                              <span key={kw} className="keyword-chip">{kw}</span>
                            ))}
                            {cluster.keywords.length > 5 && (
                              <span className="keyword-chip" style={{ opacity: 0.5 }}>
                                +{cluster.keywords.length - 5}
                              </span>
                            )}
                          </div>

                          <div className="cluster-mini-footer">
                            <div className="cluster-students">
                              <div className="student-avatars">
                                {cluster.answers.slice(0, 3).map((a, i) => (
                                  <div
                                    key={a.studentId}
                                    className={`student-avatar ${AVATAR_COLORS[i]}`}
                                  >
                                    {a.name.split(' ').map(n => n[0]).join('')}
                                  </div>
                                ))}
                              </div>
                              <span className="cluster-mini-count">
                                {cluster.studentCount} students
                              </span>
                            </div>
                            <span className="cluster-mini-conf">
                              {(cluster.confidence * 100).toFixed(0)}% conf
                            </span>
                          </div>
                        </div>
                      ))}
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
