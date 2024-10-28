import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# Generar un set de datos sintético
np.random.seed(42)
dates = pd.date_range(start="2022-01-01", periods=120, freq='D')
data = np.random.normal(loc=0, scale=1, size=120).cumsum() + 50
data += np.sin(np.linspace(0, 20, 120)) * 20  # Tendencia sinusoidal
df = pd.DataFrame(data, index=dates, columns=['Sales'])

# Aplicar Simple Moving Average (SMA) y Exponential Moving Average (EMA)
df['SMA'] = df['Sales'].rolling(window=10, min_periods=1).mean()
df['EMA'] = df['Sales'].ewm(span=10, adjust=False).mean()

# Ajustar un modelo de regresión lineal
model = LinearRegression()
X = np.arange(len(df)).reshape(-1, 1)  # Matriz 2D para sklearn
y = df['Sales'].values
model.fit(X, y)
df['Linear_Prediction'] = model.predict(X)

# Proyectar a futuro con el modelo lineal
future_dates = pd.date_range(start=df.index[-1] + pd.Timedelta(days=1), periods=30, freq='D')
future_X = np.arange(len(df), len(df) + 30).reshape(-1, 1)
future_sales = model.predict(future_X)
future_df = pd.DataFrame(future_sales, index=future_dates, columns=['Future_Linear_Prediction'])

# Proyectar SMA y EMA al futuro
# SMA (utilizar el último valor de SMA y mantener constante al futuro)
future_sma = np.full(30, df['SMA'].iloc[-1])

# EMA (continúar decayendo exponencialmente desde el último valor de EMA)
alpha = 2 / (10 + 1)
future_ema = [df['EMA'].iloc[-1]]  # Último valor de EMA
for i in range(1, 30):
    future_ema.append(alpha * future_sales[i] + (1 - alpha) * future_ema[-1])  # Fórmula de EMA

future_df['Future_SMA'] = future_sma
future_df['Future_EMA'] = future_ema

# Graficar
plt.figure(figsize=(14, 7))
plt.scatter(df.index, df['Sales'], label='Ventas', color='black', marker='o', s=20)
plt.plot(df.index, df['SMA'], label='SMA 10 días', color='green')
plt.plot(df.index, df['EMA'], label='EMA 10 días', color='red')
plt.plot(df.index, df['Linear_Prediction'], label='Regresión Lineal', color='purple')
plt.plot(future_dates, future_sales, label='Regresión Lineal a futuro', color='purple', linestyle='dashed')
plt.plot(future_dates, future_sma, label='SMA a futuro', color='green', linestyle='dashed')
plt.plot(future_dates, future_ema, label='EMA a futuro', color='red', linestyle='dashed')
plt.legend()
plt.title('Data de venta con SMA, EMA y Regresión Lineal proyectado a futuro')
plt.xlabel('Fecha')
plt.ylabel('Ventas')
plt.grid(True)
plt.show()
