import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Package, AlertCircle, Settings, TrendingDown } from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/products', label: 'All Products', icon: Package },
    { path: '/alerts', label: 'Alerts', icon: AlertCircle },
    { path: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen shadow-sm">
      <div className="p-6">
        <Link to="/" className="flex items-center gap-3 mb-8">
          <div className="text-2xl">📦</div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">StockGuard</h1>
            <p className="text-xs text-gray-500">Inventory AI</p>
          </div>
        </Link>
      </div>

      <nav className="px-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-red-50 text-red-700 border-l-4 border-red-600'
                  : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <Icon size={20} />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="absolute bottom-6 left-6 right-6 p-4 bg-red-50 rounded-lg border border-red-200">
        <div className="flex items-center gap-2 mb-2">
          <TrendingDown size={16} className="text-red-600" />
          <p className="text-sm font-semibold text-gray-900">Model Performance</p>
        </div>
        <p className="text-xs text-gray-600">MAE: 6.13 units</p>
        <p className="text-xs text-gray-600">Updated: Today</p>
      </div>
    </aside>
  );
};

export default Sidebar;
