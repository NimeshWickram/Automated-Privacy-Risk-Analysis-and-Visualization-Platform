import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import AppDetailView from './pages/AppDetailView';
import CompareApps from './pages/CompareApps';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="/analyze" element={<AppDetailView />} />
          <Route path="/compare" element={<CompareApps />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
