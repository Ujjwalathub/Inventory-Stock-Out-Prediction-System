import React from 'react';

const Header = () => {
    return (
        <header className="bg-gradient-to-r from-red-600 to-red-700 shadow-md">
            <div className="max-w-7xl mx-auto px-6 py-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="text-white text-3xl font-bold">📦</div>
                        <div>
                            <h1 className="text-white text-2xl font-bold">Stock-Out Dashboard</h1>
                            <p className="text-red-100 text-sm">ML-Powered Inventory Risk Management</p>
                        </div>
                    </div>
                    <div className="text-white text-right">
                        <p className="text-sm">Last Updated: {new Date().toLocaleDateString()}</p>
                        <p className="text-xs text-red-100">Powered by FastAPI + React</p>
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
