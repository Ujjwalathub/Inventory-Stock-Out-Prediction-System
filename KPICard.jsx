import React from 'react';
import { TrendingDown, AlertTriangle, Package } from 'lucide-react';

const KPICard = ({ title, value, icon: Icon, trend, color = 'red' }) => {
  const colorClasses = {
    red: 'bg-red-50 border-red-200',
    orange: 'bg-orange-50 border-orange-200',
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
  };

  const iconColorClasses = {
    red: 'bg-red-100 text-red-600',
    orange: 'bg-orange-100 text-orange-600',
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
  };

  return (
    <div className={`${colorClasses[color]} border rounded-xl p-6`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-600 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          {trend && (
            <p className={`text-sm mt-2 ${trend > 0 ? 'text-red-600' : 'text-green-600'}`}>
              {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}% from last week
            </p>
          )}
        </div>
        <div className={`${iconColorClasses[color]} p-3 rounded-lg`}>
          <Icon size={24} />
        </div>
      </div>
    </div>
  );
};

export const KPIGrid = ({ topRiskItem, totalAtRisk, criticalCount }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <KPICard
        title="Total Items at Risk"
        value={totalAtRisk || 0}
        icon={AlertTriangle}
        color="red"
        trend={5}
      />
      <KPICard
        title="Critical Risk Count"
        value={criticalCount || 0}
        icon={TrendingDown}
        color="orange"
        trend={-2}
      />
      <KPICard
        title="Top Risk Item"
        value={topRiskItem?.StockCode || '—'}
        icon={Package}
        color="blue"
      />
    </div>
  );
};

export default KPICard;
