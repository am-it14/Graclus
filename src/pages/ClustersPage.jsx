import { useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { mockClusters, processingStats } from '../data/mockData';

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

export default function ClustersPage({ clusters, setClusters, stats }) {
  const navigate = useNavigate();

  // If accessed directly without uploading, load mock data
  useEffect(() => {
    if (!clusters) {
      setClusters(mockClusters);
    }
  }, [clusters, setClusters]);

  const data = clusters || mockClusters;
  const st = stats || processingStats;

  const gradedCount = data.filter(c => c.grade !== null).length;
  const totalStudents = data.reduce((sum, c) => sum + c.studentCount, 0);

  return (
    <div className="app-bg">
      <Navbar activeStep={2} />

      <div className="clusters-page">
        <div className="page-header">
          <h1>Answer Clusters</h1>
          <p>
            {data.length} clusters identified from {totalStudents} student answers •{' '}
            <strong style={{ color: 'var(--accent-emerald)' }}>{gradedCount}</strong> / {data.length} graded
          </p>
        </div>

        {/* Stats bar */}
        <div className="stats-bar">
          <div className="stat-card">
            <div className="stat-label">Total Sheets</div>
            <div className="stat-value indigo">{st.totalSheets}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Clusters Found</div>
            <div className="stat-value cyan">{st.totalClusters}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Processing Time</div>
            <div className="stat-value emerald">{st.totalTime}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Tokens Used</div>
            <div className="stat-value amber">{st.tokensUsed.toLocaleString()}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Est. Cost</div>
            <div className="stat-value violet">{st.estimatedCost}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Avg Confidence</div>
            <div className="stat-value rose">{(st.avgConfidence * 100).toFixed(0)}%</div>
          </div>
        </div>

        {/* Cluster cards */}
        <div className="clusters-grid">
          {data.map((cluster, index) => (
            <div
              key={cluster.id}
              className={`cluster-card type-${cluster.type} stagger-${index + 1}`}
              onClick={() => navigate(`/grade/${cluster.id}`)}
            >
              <div className="cluster-header">
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <span className={`cluster-type-badge ${TYPE_BADGES[cluster.type]}`}>
                      {TYPE_LABELS[cluster.type]}
                    </span>
                    <span className="cluster-lang-badge">🌐 {cluster.language}</span>
                  </div>
                  <h3 className="cluster-title">{cluster.label}</h3>
                  <div className="cluster-meta">
                    <span>{cluster.studentCount} students</span>
                    <span>•</span>
                    <span>{(cluster.confidence * 100).toFixed(0)}% confidence</span>
                  </div>
                </div>
              </div>

              <div className="cluster-body">
                <p className="cluster-summary">{cluster.summary}</p>
                <div className="cluster-keywords">
                  {cluster.keywords.slice(0, 6).map((kw) => (
                    <span key={kw} className="keyword-chip">{kw}</span>
                  ))}
                </div>
              </div>

              <div className="cluster-footer">
                <div className="cluster-students">
                  <div className="student-avatars">
                    {cluster.answers.slice(0, 4).map((a, i) => (
                      <div
                        key={a.studentId}
                        className={`student-avatar ${AVATAR_COLORS[i]}`}
                      >
                        {a.name.split(' ').map(n => n[0]).join('')}
                      </div>
                    ))}
                  </div>
                  {cluster.studentCount > 4 && (
                    <span>+{cluster.studentCount - 4} more</span>
                  )}
                </div>
                <span className={`grade-badge ${cluster.grade !== null ? 'graded' : 'ungraded'}`}>
                  {cluster.grade !== null ? `${cluster.grade}/${cluster.maxMarks}` : 'Not Graded'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
