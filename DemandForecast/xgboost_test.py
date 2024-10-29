import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xgboost as xgb
from sklearn.metrics import mean_squared_error

# Data auto generada
n = 730 # 2 años
np.random.seed(42)
date_range = pd.date_range(start='1/1/2020', periods=n, freq='D')  

# Serie de demanda con tendencia, temporada y ruido
trend = np.linspace(10, 20, n)  
seasonality = 5 * np.sin(2 * np.pi * date_range.dayofyear / 365)  
noise = np.random.normal(0, 2, n)  
demand = trend + seasonality + noise

data = pd.DataFrame({'Date': date_range, 'Demand': demand})
data.set_index('Date', inplace=True)

# Caracteristicas
for i in range(1, 8):  # Lags of 1 to 7 days
    data[f'Lag_{i}'] = data['Demand'].shift(i)

data['Rolling_Mean_7'] = data['Demand'].rolling(window=7).mean().shift(1)
data['Rolling_Mean_30'] = data['Demand'].rolling(window=30).mean().shift(1)

# Drop rows with NaN values due to shifting (investigar)
data.dropna(inplace=True)

X = data.drop('Demand', axis=1)
y = data['Demand']

# Entrenamiento XGBoost
X_train, X_test = X[:-60], X[-60:]
y_train, y_test = y[:-60], y[-60:]

model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100)
model.fit(X_train, y_train)

# Prediccion
y_pred = model.predict(X_test)

# Error
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
print(f'RMSE on Test Set: {rmse:.2f}')

# Prediccion a futuro
future_days = 90
last_date = data.index[-1]
future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=future_days, freq='D')

future_data = pd.DataFrame(index=future_dates, columns=X.columns)

full_data = pd.concat([data, future_data])

for date in future_dates:
    # Get lag features from previous days
    for i in range(1, 8):
        full_data.loc[date, f'Lag_{i}'] = full_data.loc[date - pd.Timedelta(days=i), 'Demand']
    # Calculate rolling means
    full_data.loc[date, 'Rolling_Mean_7'] = full_data['Demand'].shift(1).rolling(window=7).mean().loc[date]
    full_data.loc[date, 'Rolling_Mean_30'] = full_data['Demand'].shift(1).rolling(window=30).mean().loc[date]
    # Prepare features
    X_future = full_data.loc[date, X.columns].values.reshape(1, -1)
    # Predict and store the result
    full_data.loc[date, 'Demand'] = model.predict(X_future)[0]

future_predictions = full_data.loc[future_dates, 'Demand']

# Graficado
plt.figure(figsize=(14, 7))
plt.plot(data.index[-180:], y[-180:], label='Datos reales')
plt.plot(y_test.index, y_pred, label='Datos predecidos (Test)', color='red')
plt.plot(future_predictions.index, future_predictions.values, label='Datos futuros', color='green', linestyle='--')
plt.xlabel('Fecha')
plt.ylabel('Demanda')
plt.title('Datos reales vs predecidos por XGBoost')
plt.legend()
plt.show()
