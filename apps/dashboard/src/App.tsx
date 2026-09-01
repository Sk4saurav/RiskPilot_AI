import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './layouts/DashboardLayout';
import { CaseQueue } from './pages/CaseQueue';
import { CaseDetail } from './pages/CaseDetail';
import { Analytics } from './pages/Analytics';
import { ReliabilityLab } from './pages/ReliabilityLab';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<Navigate to="/cases" replace />} />
          <Route path="cases" element={<CaseQueue />} />
          <Route path="cases/:id" element={<CaseDetail />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="reliability-lab" element={<ReliabilityLab />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
