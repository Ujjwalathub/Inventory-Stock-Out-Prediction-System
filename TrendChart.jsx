import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { getTrends } from '../api/axiosClient';

const TrendChart = ({ stockCode }) => {
    const [trendData, setTrendData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchTrends = async () => {
            if (!stockCode) return;

            setLoading(true);
            setError(null);
            try {
                const response = await getTrends(stockCode);
                setTrendData(response.data);
            } catch (err) {
                setError(`Failed to load trend data for ${stockCode}`);
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchTrends();
    }, [stockCode]);

    if (!stockCode) {
        return (
            <div className="bg-white rounded-lg shadow-lg p-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">📊 Historical Trend</h2>
                <div className="text-center py-12 text-gray-500">
                    Select an item from the table to view its historical demand trend.
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="bg-white rounded-lg shadow-lg p-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">📊 Historical Trend (Item: {stockCode})</h2>
                <div className="flex justify-center items-center h-64">
                    <div className="text-gray-500">Loading chart data...</div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-white rounded-lg shadow-lg p-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">📊 Historical Trend</h2>
                <div className="error text-sm">{error}</div>
            </div>
        );
    }

    if (trendData.length === 0) {
        return (
            <div className="bg-white rounded-lg shadow-lg p-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">📊 Historical Trend (Item: {stockCode})</h2>
                <div className="text-center py-8 text-gray-500">
                    No trend data available for this item.
                </div>
            </div>
        );
    }

    // Calculate statistics
    const quantities = trendData.map(d => d.Quantity);
    const avgQuantity = (quantities.reduce((a, b) => a + b, 0) / quantities.length).toFixed(1);
    const maxQuantity = Math.max(...quantities);
    const minQuantity = Math.min(...quantities);

    return (
        <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-2 mb-6">
                <span className="text-2xl">📊</span>
                <h2 className="text-xl font-bold text-gray-800">Historical Trend (Item: {stockCode})</h2>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <p className="text-blue-600 text-sm font-semibold">Avg Weekly</p>
                    <p className="text-2xl font-bold text-blue-900">{avgQuantity}</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                    <p className="text-green-600 text-sm font-semibold">Peak Demand</p>
                    <p className="text-2xl font-bold text-green-900">{maxQuantity}</p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                    <p className="text-purple-600 text-sm font-semibold">Low Demand</p>
                    <p className="text-2xl font-bold text-purple-900">{minQuantity}</p>
                </div>
            </div>

            {/* Chart */}
            <div style={{ width: '100%', height: 350 }}>
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis
                            dataKey="Week_Start"
                            tick={{ fontSize: 12 }}
                            angle={-45}
                            textAnchor="end"
                            height={80}
                        />
                        <YAxis
                            tick={{ fontSize: 12 }}
                            label={{ value: 'Units Sold', angle: -90, position: 'insideLeft', offset: 10 }}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#ffffff',
                                border: '1px solid #dc2626',
                                borderRadius: '8px',
                                padding: '10px'
                            }}
                            formatter={(value) => [`${value} units`, 'Quantity']}
                            labelFormatter={(label) => `Week: ${label}`}
                        />
                        <Legend />
                        <Line
                            type="monotone"
                            dataKey="Quantity"
                            stroke="#dc2626"
                            strokeWidth={3}
                            dot={{ fill: '#dc2626', r: 5 }}
                            activeDot={{ r: 7 }}
                            name="Weekly Quantity"
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded">
                <p className="text-sm text-gray-700">
                    📌 Showing <strong>{trendData.length}</strong> weeks of historical data for this product.
                </p>
            </div>
        </div>
    );
};

export default TrendChart;
