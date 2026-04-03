import { Link } from 'react-router-dom';

export default function Navbar({ activeStep = 1 }) {
  const steps = [
    { num: 1, label: 'Upload', path: '/' },
    { num: 2, label: 'Clusters', path: '/clusters' },
    { num: 3, label: 'Grading', path: null },
  ];

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        <div className="navbar-logo">G</div>
        <div>
          <div className="navbar-title">GradeFlow</div>
          <div className="navbar-subtitle">AI-Powered Exam Grading</div>
        </div>
      </Link>

      <div className="navbar-steps">
        {steps.map((step, i) => (
          <span key={step.num} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {step.path ? (
              <Link
                to={step.path}
                className={`step-indicator ${activeStep === step.num ? 'active' : ''} ${activeStep > step.num ? 'completed' : ''}`}
              >
                <span className="step-dot" />
                {step.label}
              </Link>
            ) : (
              <span
                className={`step-indicator ${activeStep === step.num ? 'active' : ''} ${activeStep > step.num ? 'completed' : ''}`}
              >
                <span className="step-dot" />
                {step.label}
              </span>
            )}
            {i < steps.length - 1 && <span className="step-connector" />}
          </span>
        ))}
      </div>
    </nav>
  );
}
