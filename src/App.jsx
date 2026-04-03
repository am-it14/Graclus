import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import ClustersPage from './pages/ClustersPage';
import GradingPage from './pages/GradingPage';
import './App.css';

function App() {
  const [clusters, setClusters] = useState(null);
  const [stats, setStats] = useState(null);

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={<UploadPage setClusters={setClusters} setStats={setStats} />}
        />
        <Route
          path="/clusters"
          element={<ClustersPage clusters={clusters} setClusters={setClusters} stats={stats} />}
        />
        <Route
          path="/grade/:clusterId"
          element={<GradingPage clusters={clusters} setClusters={setClusters} />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
