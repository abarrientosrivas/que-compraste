import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from xgboost import XGBClassifier
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Generate date range for 5 years
start_date = datetime(2015, 1, 1)
end_date = datetime(2019, 12, 31)
all_dates = pd.date_range(start_date, end_date)

# Initialize an empty DataFrame
data = pd.DataFrame({'date': all_dates})

# Define seasons
def get_season(date):
    Y = 2000  # Dummy leap year to handle Feb 29
    seasons = [('winter', (datetime(Y, 1, 1), datetime(Y, 2, 29))),
               ('spring', (datetime(Y, 3, 1), datetime(Y, 5, 31))),
               ('summer', (datetime(Y, 6, 1), datetime(Y, 8, 31))),
               ('fall',   (datetime(Y, 9, 1), datetime(Y, 11, 30))),
               ('winter', (datetime(Y, 12, 1), datetime(Y, 12, 31)))]
    date = date.replace(year=Y)
    return next(season for season, (start, end) in seasons if start <= date <= end)

def get_season_num(date):
    Y = 2000  # Dummy leap year to handle Feb 29
    seasons = [(2, (datetime(Y, 1, 1), datetime(Y, 2, 29))),
               (3, (datetime(Y, 3, 1), datetime(Y, 5, 31))),
               (0, (datetime(Y, 6, 1), datetime(Y, 8, 31))),
               (1,   (datetime(Y, 9, 1), datetime(Y, 11, 30))),
               (2, (datetime(Y, 12, 1), datetime(Y, 12, 31)))]
    date = date.replace(year=Y)
    return next(season for season, (start, end) in seasons if start <= date <= end)

# Apply season function
data['season'] = data['date'].apply(get_season)
data['season_num'] = data['date'].apply(get_season_num)

# Extract day of the week
data['day_of_week'] = data['date'].dt.day_name()

# Define the pattern
def is_pattern_date(row):
    if row['season'] == 'summer' and row['day_of_week'] == 'Monday':
        if random.random() < 0.6:  # 60% probability
            return 1
        else:
            return 0
    elif row['season'] == 'fall' and row['day_of_week'] == 'Wednesday':
        return 1
    elif row['season'] == 'winter' and row['day_of_week'] == 'Friday':
        if random.random() < 0.8:  # 80% probability
            return 1
        else:
            return 0
    elif row['season'] == 'spring' and row['day_of_week'] == 'Sunday':
        return 1
    else:
        return 0

# Apply pattern function
data['target'] = data.apply(is_pattern_date, axis=1)

# Assign random values between 4 and 7 to pattern dates
data['value'] = data['target'].apply(lambda x: np.random.randint(4, 8) if x == 1 else np.nan)

# Numerical day of the week
data['day_of_week_num'] = data['date'].dt.weekday  # Monday=0, Sunday=6
data['day_of_week_sin'] = np.sin(2 * np.pi * data['day_of_week_num'] / 7)
data['day_of_week_cos'] = np.cos(2 * np.pi * data['day_of_week_num'] / 7)

# Month
data['month'] = data['date'].dt.month

# Day of the month
data['day'] = data['date'].dt.day

# Is weekend
data['is_weekend'] = data['day_of_week_num'].apply(lambda x: 1 if x >= 5 else 0)

# One-hot encode seasons
season_dummies = pd.get_dummies(data['season'], prefix='season')
data = pd.concat([data, season_dummies], axis=1)

# Prepare feature set
feature_cols = ['day_of_week_sin', 'day_of_week_cos', 'month', 'day', 'is_weekend', 'season_num']
print(feature_cols)
X = data[feature_cols]
y = data['target']

# Split data into training and testing sets
X_train = X[data['date'] <= datetime(2019, 6, 30)]
y_train = y[data['date'] <= datetime(2019, 6, 30)]
X_test = X[data['date'] > datetime(2019, 6, 30)]
y_test = y[data['date'] > datetime(2019, 6, 30)]

# Initialize and train the model
model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
model.fit(X_train, y_train)
xgb.plot_importance(model, importance_type='weight')

# Predictions on the test set
y_pred = model.predict(X_test)

# Evaluation
print("Classification Report on Test Data:\n", classification_report(y_test, y_pred))

# Generate future dates
future_start_date = end_date + timedelta(days=1)
future_end_date = future_start_date + timedelta(days=179)
future_dates = pd.date_range(future_start_date, future_end_date)

# Create DataFrame for future dates
future_data = pd.DataFrame({'date': future_dates})

# Extract features from future dates
future_data['season'] = future_data['date'].apply(get_season)
future_data['season_num'] = future_data['date'].apply(get_season_num)
future_data['day_of_week_num'] = future_data['date'].dt.weekday
future_data['day_of_week_sin'] = np.sin(2 * np.pi * future_data['day_of_week_num'] / 7)
future_data['day_of_week_cos'] = np.cos(2 * np.pi * future_data['day_of_week_num'] / 7)
future_data['month'] = future_data['date'].dt.month
future_data['day'] = future_data['date'].dt.day
future_data['is_weekend'] = future_data['day_of_week_num'].apply(lambda x: 1 if x >= 5 else 0)
season_dummies_future = pd.get_dummies(future_data['season'], prefix='season')
future_data = pd.concat([future_data, season_dummies_future], axis=1)

# Ensure all season columns are present
for col in season_dummies.columns:
    if col not in future_data:
        future_data[col] = 0

# Prepare feature set
X_future = future_data[feature_cols]
print(X_future)

# Predict
future_data['predicted_target'] = model.predict(X_future)

# Assign random values between 4 and 7 to predicted pattern dates
future_data['value'] = future_data['predicted_target'].apply(lambda x: np.random.randint(4, 8) if x == 1 else np.nan)

# Function to verify if the prediction matches the expected pattern
def verify_pattern(row):
    day_name = row['date'].day_name()
    season = row['season']
    if season == 'summer' and day_name == 'Monday':
        return True
    elif season == 'fall' and day_name == 'Wednesday':
        return True
    elif season == 'winter' and day_name == 'Friday':
        return True
    elif season == 'spring' and day_name == 'Sunday':
        return True
    else:
        return False

# Apply verification
predicted_pattern_dates = future_data[future_data['predicted_target'] == 1]
predicted_pattern_dates['is_correct'] = predicted_pattern_dates.apply(verify_pattern, axis=1)

# Check if all predicted dates match the expected pattern
accuracy = predicted_pattern_dates['is_correct'].mean()
print(f"Accuracy of pattern prediction: {accuracy * 100:.2f}%")

# Display predicted dates and values
print(predicted_pattern_dates[['date', 'value', 'season', 'day_of_week_num', 'is_correct']])

import matplotlib.pyplot as plt

# Plot the predicted pattern dates with values
plt.figure(figsize=(12, 6))

# Plot actual values from the generated 5-year data
plt.scatter(data[data['target'] == 1]['date'], data[data['target'] == 1]['value'], color='blue', label='Historical Pattern', alpha=0.6)

# Plot predicted pattern dates in the future data
plt.scatter(predicted_pattern_dates['date'], predicted_pattern_dates['value'], color='red', label='Predicted Pattern', alpha=0.6)

# Add labels and legend
plt.xlabel('Date')
plt.ylabel('Value')
plt.title('Historical vs Predicted Pattern Dates')
plt.legend()
plt.show()
