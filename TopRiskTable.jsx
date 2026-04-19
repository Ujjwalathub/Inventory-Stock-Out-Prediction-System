import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { Badge } from '../ui/index';
import { formatNumber, getRiskLevelColor, getRiskLevelLabel } from '../../utils/formatters';

const TopRiskTable = ({ data, isLoading, isError }) => {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Top 10 Products at Risk</h3>
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-12 bg-gray-200 rounded-lg"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Top 10 Products at Risk</h3>
        <div className="text-center py-8">
          <p className="text-red-600 font-medium">Failed to load predictions</p>
          <p className="text-gray-500 text-sm mt-1">Please try refreshing the page</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Top 10 Products at Risk</h3>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              <th className="text-left px-4 py-3 font-semibold text-gray-700 text-sm">Stock Code</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-700 text-sm">Description</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-700 text-sm">Predicted Demand</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-700 text-sm">Risk Level</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-700 text-sm"></th>
            </tr>
          </thead>
          <tbody>
            {data && data.length > 0 ? (
              data.map((item, index) => {
                const riskLevel = getRiskLevelLabel(item.Predicted_Demand);
                const riskColor = getRiskLevelColor(item.Predicted_Demand);
                
                return (
                  <tr
                    key={`${item.StockCode}-${index}`}
                    className="border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer"
                    onClick={() => navigate(`/product/${item.StockCode}`)}
                  >
                    <td className="px-4 py-4 font-mono font-semibold text-gray-900">{item.StockCode}</td>
                    <td className="px-4 py-4 text-gray-700 truncate max-w-xs">{item.Description}</td>
                    <td className="px-4 py-4">
                      <span className="font-bold text-lg text-red-600">
                        {formatNumber(item.Predicted_Demand)}
                      </span>
                      <span className="text-gray-500 text-sm ml-1">units</span>
                    </td>
                    <td className="px-4 py-4">
                      <Badge variant={riskLevel.toLowerCase()}>
                        {riskLevel}
                      </Badge>
                    </td>
                    <td className="px-4 py-4 text-right">
                      <ChevronRight size={18} className="text-gray-400" />
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan="5" className="px-4 py-8 text-center text-gray-500">
                  No data available
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TopRiskTable;
