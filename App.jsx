import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Sidebar from './components/layout/Sidebar';
import Topbar from './components/layout/Topbar';
import Dashboard from './pages/Dashboard';
import ProductDetail from './pages/ProductDetail';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 10, // 10 minutes
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="flex h-screen bg-gray-100">
          {/* Sidebar */}
          <Sidebar />

          {/* Main Content Area */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Topbar */}
            <Topbar />

            {/* Page Content */}
            <main className="flex-1 overflow-auto">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/product/:stockCode" element={<ProductDetail />} />
                <Route path="/products" element={<div className="p-8"><p className="text-gray-600">Products page - coming soon</p></div>} />
                <Route path="/alerts" element={<div className="p-8"><p className="text-gray-600">Alerts page - coming soon</p></div>} />
                <Route path="/settings" element={<div className="p-8"><p className="text-gray-600">Settings page - coming soon</p></div>} />
              </Routes>
            </main>
          </div>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
