import pandas as pd
from neuralprophet import NeuralProphet
import matplotlib.pyplot as plt
import numpy as np 
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Generate the dates and the synthetic data
dates = pd.date_range(start='2023-01-01', periods=365*3, freq='D')
data = {
    'ds': dates,
    'y': (0.05 * dates.dayofyear) + 10 * np.sin(dates.dayofyear / 20) + np.random.normal(scale=0.5, size=len(dates))
}
df = pd.DataFrame(data)

# Initialize and fit the NeuralProphet model
model = NeuralProphet(batch_size=16)
metrics = model.fit(df, freq='D')

# Create a dataframe for future predictions and get the forecast
future = model.make_future_dataframe(df, periods=90)
forecast = model.predict(future)

# Plotting 
plt.figure(figsize=(10, 5))
plt.plot(df['ds'], df['y'], 'k.', alpha=0.5, label='Historical Data')
plt.plot(forecast['ds'], forecast['yhat1'], 'r-', label='Forecast')  # Ensure 'yhat1' is the correct column name
plt.title('Forecast of the Synthetic Data with Training Data Points')
plt.xlabel('Date')
plt.ylabel('Values')
plt.legend()
plt.show()