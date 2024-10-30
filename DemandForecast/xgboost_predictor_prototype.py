import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import matplotlib.pyplot as plt
from datetime import timedelta

# 1. Generar datos sintéticos
np.random.seed(42)
date_range = pd.date_range(start='1/1/2022', periods=365 * 3, freq='D')  # Un año de datos diarios
data = pd.DataFrame({'Date': date_range})
data['Month'] = data['Date'].dt.month
data['DayOfWeek'] = data['Date'].dt.dayofweek  # Lunes=0, Domingo=6

# Añadir columna de demanda con ceros en todos los días
data['Demand'] = 0

# Agregar compras en jueves y viernes de verano (junio a agosto)
for i in range(len(data)):
    if data.loc[i, 'Month'] in [6, 7, 8] and data.loc[i, 'DayOfWeek'] in [3, 4]:  # Jueves=3, Viernes=4
        data.loc[i, 'Demand'] = np.random.randint(3, 8)  # Cantidad entre 3 y 7

# 2. Crear variables objetivo y características para la clasificación
data['IsPurchaseDay'] = (data['Demand'] > 0).astype(int)  # 1 si hay compra, 0 si no

# Crear variables de calendario como características
data['IsSummer'] = data['Month'].apply(lambda x: 1 if x in [6, 7, 8] else 0)  # Verano es 1
X_class = data[['DayOfWeek', 'IsSummer']]
y_class = data['IsPurchaseDay']

# 3. Dividir datos para entrenamiento y prueba para la clasificación
X_train_class, X_test_class, y_train_class, y_test_class = train_test_split(X_class, y_class, test_size=0.2, random_state=42)

# 4. Entrenar el modelo de clasificación
model_class = xgb.XGBClassifier(objective='binary:logistic', use_label_encoder=False, eval_metric='logloss')
model_class.fit(X_train_class, y_train_class)

# Predicciones y evaluación del modelo de clasificación
y_pred_class = model_class.predict(X_test_class)
accuracy = accuracy_score(y_test_class, y_pred_class)
print(f'Accuracy del modelo de clasificación: {accuracy:.2f}')

# 5. Usar el modelo de clasificación para predecir los días con compra
data['PredictedIsPurchaseDay'] = model_class.predict(X_class)

# 6. Preparar datos para el modelo de regresión
data_with_purchase = data[data['PredictedIsPurchaseDay'] == 1].copy()  # Solo días predichos con compra
X_reg = data_with_purchase[['DayOfWeek', 'IsSummer']]
y_reg = data_with_purchase['Demand']

# Dividir datos de regresión
X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(X_reg, y_reg, test_size=0.2, random_state=42)

# 7. Entrenar el modelo de regresión para predecir cantidad de compra
model_reg = xgb.XGBRegressor(objective='reg:squarederror')
model_reg.fit(X_train_reg, y_train_reg)

# Predicciones y evaluación del modelo de regresión
y_pred_reg = model_reg.predict(X_test_reg)
rmse = np.sqrt(mean_squared_error(y_test_reg, y_pred_reg))
print(f'RMSE del modelo de regresión: {rmse:.2f}')

# 8. Proyectar demanda para un año futuro
# Datos de referencia
start_date = data['Date'].max() + timedelta(days=1)
future_dates = pd.date_range(start=start_date, periods=365, freq='D')
future_data = pd.DataFrame({'Date': future_dates})
future_data['Month'] = future_data['Date'].dt.month
future_data['DayOfWeek'] = future_data['Date'].dt.dayofweek

# Añadir características necesarias para el modelo
future_data['IsSummer'] = future_data['Month'].apply(lambda x: 1 if x in [6, 7, 8] else 0)  # Indica si es verano

# 9. Predicción de los días de compra (clasificación)
X_future_class = future_data[['DayOfWeek', 'IsSummer']]
future_data['PredictedIsPurchaseDay'] = model_class.predict(X_future_class)

# Filtrar solo los días en los que se predice que habrá compra
future_data_with_purchase = future_data[future_data['PredictedIsPurchaseDay'] == 1].copy()

# 10. Predicción de la cantidad de compra (regresión)
X_future_reg = future_data_with_purchase[['DayOfWeek', 'IsSummer']]
future_data_with_purchase['PredictedDemand'] = model_reg.predict(X_future_reg)

# 11. Visualización de la proyección de demanda para el próximo año
plt.figure(figsize=(14, 7))
plt.plot(data['Date'], data['Demand'], label='Demanda Real')
plt.plot(future_data_with_purchase['Date'], future_data_with_purchase['PredictedDemand'], 'ro', label='Demanda Predicha (Futuro)', markersize=5)
plt.xlabel('Fecha')
plt.ylabel('Demanda')
plt.title('Demanda Real y Predicha para el Año Próximo')
plt.legend()
plt.show()
