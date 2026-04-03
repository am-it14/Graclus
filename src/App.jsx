import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import ClustersPage from './pages/ClustersPage';
import GradingPage from './pages/GradingPage';
import './App.css';

function App() {
  const [questions, setQuestions] = useState(null);
  const [stats, setStats] = useState(null);

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={<UploadPage setQuestions={setQuestions} setStats={setStats} />}
        />
        <Route
          path="/clusters"
          element={<ClustersPage questions={questions} setQuestions={setQuestions} stats={stats} />}
        />
        <Route
          path="/grade/:questionId/:clusterId"
          element={<GradingPage questions={questions} setQuestions={setQuestions} />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
