import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, confusion_matrix, classification_report

# ==========================================
# 1. Load and Clean the Dataset
# ==========================================
print("Loading dataset...")
# Make sure this path is correct for your local machine
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
# 2. Feature Engineering (Time Series Setup)
# ==========================================
print("\nPreparing time-series features...")

# Aggregate quantities by Week
weekly_sales = df.groupby(['StockCode', 'Week'])['Quantity'].sum().reset_index()

# Get a complete grid of StockCode x Week to fill missing weeks with 0
all_weeks = weekly_sales['Week'].unique()
all_items = weekly_sales['StockCode'].unique()
idx = pd.MultiIndex.from_product([all_items, all_weeks], names=['StockCode', 'Week'])

weekly_sales = weekly_sales.set_index(['StockCode', 'Week']).reindex(idx, fill_value=0).reset_index()
weekly_sales = weekly_sales.sort_values(by=['StockCode', 'Week'])

# Create Lag Features (Sales from 1, 2, and 3 weeks ago)
weekly_sales['lag_1'] = weekly_sales.groupby('StockCode')['Quantity'].shift(1)
weekly_sales['lag_2'] = weekly_sales.groupby('StockCode')['Quantity'].shift(2)
weekly_sales['lag_3'] = weekly_sales.groupby('StockCode')['Quantity'].shift(3)

# Create Rolling Mean (Average of the last 4 weeks of lags)
weekly_sales['rolling_mean_4'] = weekly_sales.groupby('StockCode')['lag_1'].transform(
    lambda x: x.rolling(4, min_periods=1).mean()
)

# Drop NaN values caused by lagging 
model_data = weekly_sales.dropna().copy()

# Add Classification Target (High Demand Flag: > 10 units)
THRESHOLD = 10
model_data['High_Demand_Flag'] = (model_data['Quantity'] > THRESHOLD).astype(int)

# ==========================================
# 3. Train-Test Split (Shared for Both Models)
# ==========================================
test_weeks = all_weeks[-4:]
train_data = model_data[~model_data['Week'].isin(test_weeks)]
test_data = model_data[model_data['Week'].isin(test_weeks)]

features = ['lag_1', 'lag_2', 'lag_3', 'rolling_mean_4']
X_train = train_data[features]
X_test = test_data[features]

# ==========================================
# 4. REGRESSION: Predict Exact Demand Quantities
# ==========================================
print("\n--- Training Regression Model (Demand Forecasting) ---")
y_train_reg = train_data['Quantity']
y_test_reg = test_data['Quantity']

rf_reg = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf_reg.fit(X_train, y_train_reg)

y_pred_reg = rf_reg.predict(X_test)
mae = mean_absolute_error(y_test_reg, y_pred_reg)
print(f"Mean Absolute Error on Test Set: {mae:.2f} units")

# Predict Next Week's Demand to Identify Stock-Out Risks
last_week_data = weekly_sales.groupby('StockCode').tail(1).copy()
last_week_data['lag_3'] = last_week_data['lag_2']
last_week_data['lag_2'] = last_week_data['lag_1']
last_week_data['lag_1'] = last_week_data['Quantity']
lag_4_vals = weekly_sales.groupby('StockCode')['Quantity'].shift(3).groupby(weekly_sales['StockCode']).tail(1).values
last_week_data['rolling_mean_4'] = (last_week_data['lag_1'] + last_week_data['lag_2'] + last_week_data['lag_3'] + lag_4_vals) / 4

X_future = last_week_data[features]
last_week_data['Predicted_Demand'] = rf_reg.predict(X_future)

# Rank and Save
top_risk = last_week_data.sort_values(by='Predicted_Demand', ascending=False).head(20)
top_risk['Description'] = top_risk['StockCode'].map(item_desc)
top_risk[['StockCode', 'Description', 'Predicted_Demand']].to_csv('stockout_predictions.csv', index=False)
print("Saved high-risk predictions to 'stockout_predictions.csv'")

# ==========================================
# 5. CLASSIFICATION: Predict High Demand Events
# ==========================================
print("\n--- Training Classification Model (High Demand Risk) ---")
y_train_clf = train_data['High_Demand_Flag']
y_test_clf = test_data['High_Demand_Flag']

# Train Classifier
rf_clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, max_depth=10, class_weight='balanced')
rf_clf.fit(X_train, y_train_clf)

# Evaluate Classifier
y_pred_clf = rf_clf.predict(X_test)
report = classification_report(y_test_clf, y_pred_clf)
print("Classification Report:\n", report)

cm = confusion_matrix(y_test_clf, y_pred_clf)

# ==========================================
# 6. Generate Visualizations
# ==========================================
print("\nGenerating visualizations...")

# --- Plot 3: Confusion Matrix (Heatmap) ---
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False,
            xticklabels=['Low Demand (<=10)', 'High Demand (>10)'],
            yticklabels=['Low Demand (<=10)', 'High Demand (>10)'],
            annot_kws={"size": 14})
plt.title('Confusion Matrix: Predicting High Demand Events', fontsize=14, fontweight='bold')
plt.xlabel('Predicted Class', fontsize=12, fontweight='bold')
plt.ylabel('Actual Class', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.show()

# --- Plot 1: Top 10 Products at Risk (Bar Chart) ---
plt.figure(figsize=(12, 6))
sns.barplot(data=top_risk.head(10), x='Predicted_Demand', y='Description', palette='Reds_r')
plt.title('Top 10 Products at Highest Risk of Stock-Out (Next Week Demand)', fontsize=14)
plt.xlabel('Forecasted Demand (Units)', fontsize=12)
plt.ylabel('Product Description', fontsize=12)
plt.tight_layout()
plt.show()

# --- Plot 2: Historical Trend for #1 At-Risk Product (Line Chart) ---
top_item_code = str(top_risk.iloc[0]['StockCode'])
top_item_desc = top_risk.iloc[0]['Description']

item_data = df[df['StockCode'] == top_item_code].copy()
item_data['Week_Start'] = item_data['Week'].dt.start_time
weekly_trend = item_data.groupby('Week_Start')['Quantity'].sum().reset_index()

plt.figure(figsize=(14, 5))
sns.lineplot(data=weekly_trend, x='Week_Start', y='Quantity', marker='o', color='crimson', linewidth=2)
plt.title(f'Historical Weekly Demand for: {top_item_desc}', fontsize=14)
plt.xlabel('Date (Weekly)', fontsize=12)
plt.ylabel('Units Sold', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()