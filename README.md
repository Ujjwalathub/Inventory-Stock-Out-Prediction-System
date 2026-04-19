# Inventory Stock-Out Prediction System

## Overview
A real-time machine learning system that predicts inventory demand and identifies products at highest risk of stock-out. The system uses Random Forest regression and classification models trained on historical retail transaction data.

## Features
- **Demand Forecasting**: ML-based predictions of product demand for the next period
- **Risk Scoring**: Automatic categorization into risk levels (CRITICAL, HIGH, MEDIUM, LOW)
- **Historical Trends**: Visual charts of past demand patterns by product
- **RESTful API**: Comprehensive API endpoints for integration
- **Interactive Dashboard**: React-based frontend for visualizing predictions and trends

## Tech Stack
- **Backend**: FastAPI, Python, scikit-learn
- **Frontend**: React, Vite, Tailwind CSS
- **ML Models**: Random Forest Regressor & Classifier
- **Data**: Pandas, NumPy

## Project Structure
nventory-dashboard/ # React frontend
src/
components/ # UI components
pages/ # Dashboard & Product pages
api/ # Axios API client
app.py # FastAPI backend
online_retail_II.csv # Training dataset
stockout_predictions.csv # Generated predictions
Start the backend (from project root):

API Endpoints
GET /api/v1/predictions/top-risk - Top 10 at-risk products
GET /api/v1/inventory/trends/{stock_code} - Historical demand for a product
GET /api/v1/inventory/all-products - All products with predictions
GET /health - Health check
Models
Regression Model: Predicts continuous demand values
Classification Model: Identifies high-demand risk situations
Features: Lag values (1-3 weeks), rolling 4-week averages
License -MIT License
