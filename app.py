from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import os
import webbrowser
import threading
import time
from pathlib import Path

# ==========================================
# Initialize FastAPI App
# ==========================================
app = FastAPI(
    title="Inventory Stock-Out Prediction API",
    description="Real-time ML predictions for inventory management",
    version="1.0.0"
)

# Enable CORS for React frontend (running on localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files from built frontend (if exists)
frontend_dist = Path(__file__).parent / "inventory-dashboard" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="static")
    print(f"✅ Static files mounted from {frontend_dist / 'assets'}")

# ==========================================
# Global Variables for Caching
# ==========================================
df = None
weekly_sales = None
rf_reg = None
rf_clf = None
item_desc = None
predictions_cache = None
all_weeks = None


# ==========================================
# Pydantic Models (for API responses)
# ==========================================
class PredictionItem(BaseModel):
    StockCode: str
    Description: str
    Predicted_Demand: float


class TrendDataPoint(BaseModel):
    Week_Start: str
    Quantity: int


# ==========================================
# Load and Train Models (Called on Startup)
# ==========================================
def load_and_train_models():
    """Load data, train ML models, and generate predictions"""
    global df, weekly_sales, rf_reg, rf_clf, item_desc, predictions_cache, all_weeks

    print("Loading dataset...")
    df = pd.read_csv(r"E:\Done\online_retail_II.csv")

    # Clean 'InvoiceDate': Remove ' INVALID' text and convert to datetime
    df['InvoiceDate'] = df['InvoiceDate'].str.replace(' INVALID', '', regex=False)
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')

    # Clean 'Quantity': Convert to numeric and filter for valid positive quantities (exclude returns)
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    df = df[df['Quantity'] > 0]

    # Drop rows with missing crucial data
    df = df.dropna(subset=['InvoiceDate', 'StockCode', 'Quantity'])

    # Clean text columns
    df['StockCode'] = df['StockCode'].astype(str)
    df['Description'] = df['Description'].astype(str)

    # Extract Date components
    df['Week'] = df['InvoiceDate'].dt.to_period('W')

    print(f"Dataset shape after cleaning: {df.shape}")

    # Map StockCode to Description for later reference
    item_desc = df.groupby('StockCode')['Description'].first().to_dict()

    # ==========================================
    # Feature Engineering (Time Series Setup)
    # ==========================================
    print("\nPreparing time-series features...")

    # Aggregate quantities by Week
    weekly_sales = df.groupby(['StockCode', 'Week'])['Quantity'].sum().reset_index()

    # Get a complete grid of StockCode x Week to fill missing weeks with 0
    all_weeks_temp = weekly_sales['Week'].unique()
    all_items = weekly_sales['StockCode'].unique()
    idx = pd.MultiIndex.from_product([all_items, all_weeks_temp], names=['StockCode', 'Week'])

    weekly_sales = weekly_sales.set_index(['StockCode', 'Week']).reindex(idx, fill_value=0).reset_index()
    weekly_sales = weekly_sales.sort_values(by=['StockCode', 'Week'])
    
    all_weeks = all_weeks_temp

    # Create Lag Features
    weekly_sales['lag_1'] = weekly_sales.groupby('StockCode')['Quantity'].shift(1)
    weekly_sales['lag_2'] = weekly_sales.groupby('StockCode')['Quantity'].shift(2)
    weekly_sales['lag_3'] = weekly_sales.groupby('StockCode')['Quantity'].shift(3)

    # Create Rolling Mean
    weekly_sales['rolling_mean_4'] = weekly_sales.groupby('StockCode')['lag_1'].transform(
        lambda x: x.rolling(4, min_periods=1).mean()
    )

    # Drop NaN values caused by lagging
    model_data = weekly_sales.dropna().copy()

    # Add Classification Target
    THRESHOLD = 10
    model_data['High_Demand_Flag'] = (model_data['Quantity'] > THRESHOLD).astype(int)

    # ==========================================
    # Train-Test Split
    # ==========================================
    test_weeks = all_weeks[-4:]
    train_data = model_data[~model_data['Week'].isin(test_weeks)]
    test_data = model_data[model_data['Week'].isin(test_weeks)]

    features = ['lag_1', 'lag_2', 'lag_3', 'rolling_mean_4']
    X_train = train_data[features]
    X_test = test_data[features]

    # ==========================================
    # Train Regression Model
    # ==========================================
    print("\n--- Training Regression Model (Demand Forecasting) ---")
    y_train_reg = train_data['Quantity']
    y_test_reg = test_data['Quantity']

    rf_reg = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf_reg.fit(X_train, y_train_reg)

    from sklearn.metrics import mean_absolute_error
    y_pred_reg = rf_reg.predict(X_test)
    mae = mean_absolute_error(y_test_reg, y_pred_reg)
    print(f"Mean Absolute Error on Test Set: {mae:.2f} units")

    # ==========================================
    # Generate Predictions for Next Week
    # ==========================================
    print("\nGenerating predictions for dashboard...")
    last_week_data = weekly_sales.groupby('StockCode').tail(1).copy()
    last_week_data['lag_3'] = last_week_data['lag_2']
    last_week_data['lag_2'] = last_week_data['lag_1']
    last_week_data['lag_1'] = last_week_data['Quantity']
    
    lag_4_vals = weekly_sales.groupby('StockCode')['Quantity'].shift(3).groupby(weekly_sales['StockCode']).tail(1).values
    last_week_data['rolling_mean_4'] = (last_week_data['lag_1'] + last_week_data['lag_2'] + last_week_data['lag_3'] + lag_4_vals) / 4

    X_future = last_week_data[features]
    last_week_data['Predicted_Demand'] = rf_reg.predict(X_future)

    # Rank and cache top 10
    top_risk = last_week_data.sort_values(by='Predicted_Demand', ascending=False).head(10)
    top_risk['Description'] = top_risk['StockCode'].map(item_desc)
    
    predictions_cache = top_risk[['StockCode', 'Description', 'Predicted_Demand']].reset_index(drop=True)
    predictions_cache['Predicted_Demand'] = predictions_cache['Predicted_Demand'].round(2)

    # Also save to CSV for reference
    predictions_cache.to_csv(r'E:\Done\stockout_predictions.csv', index=False)
    print(f"Saved {len(predictions_cache)} top predictions to CSV")

    # Train Classification Model (for future use)
    print("\n--- Training Classification Model (High Demand Risk) ---")
    y_train_clf = train_data['High_Demand_Flag']
    y_test_clf = test_data['High_Demand_Flag']

    rf_clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, max_depth=10, class_weight='balanced')
    rf_clf.fit(X_train, y_train_clf)

    print("✅ Models trained and ready!")


# ==========================================
# API Endpoints
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Load models when the app starts"""
    load_and_train_models()


@app.get("/api/v1")
async def api_root():
    """API welcome endpoint"""
    return {
        "message": "🚀 Inventory Stock-Out Prediction API",
        "endpoints": {
            "top_risk": "/api/v1/predictions/top-risk",
            "trends": "/api/v1/inventory/trends/{stock_code}",
            "all_products": "/api/v1/inventory/all-products",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "models_loaded": predictions_cache is not None}


@app.get("/api/v1/predictions/top-risk")
async def get_top_risk_predictions():
    """
    Get the top 10 products at highest risk of stock-out
    Returns: JSON with top 10 predictions sorted by forecasted demand
    """
    if predictions_cache is None:
        raise HTTPException(status_code=503, detail="Models not yet loaded. Please try again in a moment.")
    
    result = []
    for _, row in predictions_cache.iterrows():
        result.append({
            "StockCode": str(row['StockCode']),
            "Description": str(row['Description']),
            "Predicted_Demand": float(row['Predicted_Demand']),
            "Risk_Level": "CRITICAL" if float(row['Predicted_Demand']) > 200 else "HIGH" if float(row['Predicted_Demand']) > 100 else "MEDIUM" if float(row['Predicted_Demand']) > 50 else "LOW"
        })
    
    return {
        "status": "success",
        "last_updated": pd.Timestamp.now().isoformat(),
        "data": result
    }


@app.get("/api/v1/inventory/trends/{stock_code}")
async def get_product_trends(stock_code: str):
    """
    Get historical weekly demand for a specific product
    Returns: JSON with historical data for charting
    """
    if df is None:
        raise HTTPException(status_code=503, detail="Data not yet loaded.")
    
    stock_code = str(stock_code).strip()
    
    # Filter data for the specific stock code
    item_data = df[df['StockCode'] == stock_code].copy()
    
    if item_data.empty:
        raise HTTPException(status_code=404, detail=f"No data found for stock code: {stock_code}")
    
    # Get product description
    product_description = item_desc.get(stock_code, "Unknown")
    
    # Aggregate by week
    item_data['Week_Start'] = item_data['Week'].dt.start_time
    weekly_trend = item_data.groupby('Week_Start')['Quantity'].sum().reset_index()
    weekly_trend = weekly_trend.sort_values('Week_Start')
    
    # Format for frontend
    historical_data = []
    for _, row in weekly_trend.iterrows():
        historical_data.append({
            "Week_Start": row['Week_Start'].strftime('%Y-%m-%d'),
            "Quantity": int(row['Quantity'])
        })
    
    return {
        "status": "success",
        "StockCode": stock_code,
        "Description": product_description,
        "historical_data": historical_data
    }


@app.get("/api/v1/inventory/all-products")
async def get_all_products():
    """
    Get all products with their current inventory status
    Returns: JSON with all products
    """
    if predictions_cache is None:
        raise HTTPException(status_code=503, detail="Models not yet loaded.")
    
    # For now, returning the same as top risk but could include all products
    result = []
    for _, row in predictions_cache.iterrows():
        result.append({
            "StockCode": str(row['StockCode']),
            "Description": str(row['Description']),
            "Predicted_Demand": float(row['Predicted_Demand']),
            "Risk_Level": "CRITICAL" if float(row['Predicted_Demand']) > 200 else "HIGH" if float(row['Predicted_Demand']) > 100 else "MEDIUM" if float(row['Predicted_Demand']) > 50 else "LOW"
        })
    
    return {
        "status": "success",
        "last_updated": pd.Timestamp.now().isoformat(),
        "data": result
    }


# ==========================================
# Serve Frontend (SPA routing)
# ==========================================
@app.get("/")
async def serve_frontend_root():
    """Serve the frontend index.html for SPA routing"""
    frontend_index = Path(__file__).parent / "inventory-dashboard" / "dist" / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    return {
        "message": "🚀 Inventory Stock-Out Prediction API",
        "note": "Frontend not built. Run 'npm run build' in inventory-dashboard/",
        "endpoints": {
            "api": "/api/v1",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/{full_path:path}")
async def serve_frontend_routes(full_path: str):
    """Serve frontend for all other routes (SPA routing)"""
    # Don't serve index.html for API routes
    if full_path.startswith("api/") or full_path.startswith("health") or full_path.startswith("docs"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Serve the frontend index.html for SPA routing
    frontend_index = Path(__file__).parent / "inventory-dashboard" / "dist" / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    
    raise HTTPException(status_code=404, detail="Not found")


# Keep legacy endpoints for backward compatibility
@app.get("/api/predictions", response_model=list[PredictionItem])
async def get_predictions_legacy():
    """Legacy endpoint - use /api/v1/predictions/top-risk instead"""
    if predictions_cache is None:
        raise HTTPException(status_code=503, detail="Models not yet loaded. Please try again in a moment.")
    
    result = []
    for _, row in predictions_cache.iterrows():
        result.append(
            PredictionItem(
                StockCode=str(row['StockCode']),
                Description=str(row['Description']),
                Predicted_Demand=float(row['Predicted_Demand'])
            )
        )
    return result


@app.get("/api/trends/{stock_code}", response_model=list[TrendDataPoint])
async def get_trends_legacy(stock_code: str):
    """Legacy endpoint - use /api/v1/inventory/trends/{stock_code} instead"""
    if df is None:
        raise HTTPException(status_code=503, detail="Data not yet loaded.")
    
    stock_code = str(stock_code).strip()
    
    # Filter data for the specific stock code
    item_data = df[df['StockCode'] == stock_code].copy()
    
    if item_data.empty:
        raise HTTPException(status_code=404, detail=f"No data found for stock code: {stock_code}")
    
    # Aggregate by week
    item_data['Week_Start'] = item_data['Week'].dt.start_time
    weekly_trend = item_data.groupby('Week_Start')['Quantity'].sum().reset_index()
    weekly_trend = weekly_trend.sort_values('Week_Start')
    
    # Format for frontend
    result = []
    for _, row in weekly_trend.iterrows():
        result.append(
            TrendDataPoint(
                Week_Start=row['Week_Start'].strftime('%Y-%m-%d'),
                Quantity=int(row['Quantity'])
            )
        )
    return result


# ==========================================
# Run the Server
# ==========================================
def open_browser():
    """Open the dashboard in the default browser after a short delay"""
    time.sleep(2)  # Wait for server to fully start
    frontend_dist = Path(__file__).parent / "inventory-dashboard" / "dist"
    
    if frontend_dist.exists():
        # Frontend is built, open from backend
        webbrowser.open('http://localhost:8000')
        print("🌐 Opening dashboard from backend (http://localhost:8000)")
    else:
        # Frontend is not built, open dev server
        webbrowser.open('http://localhost:5173')
        print("🌐 Opening dashboard from dev server (http://localhost:5173)")
        print("ℹ️  Make sure to run 'npm run dev' in the inventory-dashboard folder")


if __name__ == "__main__":
    import uvicorn
    
    # Open browser in a separate thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    print("\n" + "="*60)
    print("🚀 Starting Inventory Dashboard API Server")
    print("="*60)
    print("📊 API Docs: http://localhost:8000/docs")
    print("📊 API Root: http://localhost:8000/api/v1")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
