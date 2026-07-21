import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import AppDetailView from './pages/AppDetailView';
import CompareApps from './pages/CompareApps';
import ChatbotPage from './pages/ChatbotPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="/analyze" element={<Navigate to="/analyze/1" replace />} />
          <Route path="analyze/:appId" element={<AppDetailView />} />
          <Route path="compare" element={<CompareApps />} />
          <Route path="chatbot" element={<ChatbotPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
