import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
import numpy as np 

# Generate the dates and the synthetic data
dates = pd.date_range(start='2023-01-01', periods=365*3, freq='D')
data = {
    'ds': dates,
    'y': (0.05 * dates.dayofyear) + 10 * np.sin(dates.dayofyear / 20) + np.random.normal(scale=0.5, size=len(dates))
}
df = pd.DataFrame(data)

# Initialize and fit the Prophet model
model = Prophet()
model.fit(df)

# Create a dataframe for future predictions and get the forecast
future = model.make_future_dataframe(periods=90)
forecast = model.predict(future)

# Plot the forecast along with the actual data
fig = model.plot(forecast)
ax = fig.gca()
ax.plot(df['ds'], df['y'], 'k.', alpha=0.5)

# Add titles and labels
plt.title('Forecast of the Synthetic Data with Training Data Points')
plt.ylabel('Values')
plt.xlabel('Date')

plt.show()
