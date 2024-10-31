import xgboost as xgb
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple
from datetime import datetime, timedelta

def get_season(date):
    Y = 2000  # Dummy leap year to handle Feb 29
    seasons = [('winter', (datetime(Y, 1, 1).date(), datetime(Y, 2, 29).date())),
               ('spring', (datetime(Y, 3, 1).date(), datetime(Y, 5, 31).date())),
               ('summer', (datetime(Y, 6, 1).date(), datetime(Y, 8, 31).date())),
               ('fall',   (datetime(Y, 9, 1).date(), datetime(Y, 11, 30).date())),
               ('winter', (datetime(Y, 12, 1).date(), datetime(Y, 12, 31).date()))]
    date = date.replace(year=Y)
    return next(season for season, (start, end) in seasons if start <= date <= end)

def predict_next_purchase_dates(historic_data: List[Tuple[datetime, float]], days_into_the_future: int) -> List[datetime]:
    if not historic_data:
        return []

    historic_dates = list({i[0].date() for i in historic_data if i[1] > 0})
    historic_dates.sort()

    min_date = historic_dates[0]
    max_date = historic_dates[-1]
    all_dates = [min_date + timedelta(days=i) for i in range((max_date - min_date).days + 1)]

    features = []
    labels = []
    for date in all_dates:
        feature_vector = [
            np.sin(2 * np.pi * date.day / 31),
            np.cos(2 * np.pi * date.day / 31),
            np.sin(2 * np.pi * date.month / 12),
            np.cos(2 * np.pi * date.month / 12),
            (date.weekday() == 0),
            (date.weekday() == 1),
            (date.weekday() == 2),
            (date.weekday() == 3),
            (date.weekday() == 4),
            (date.weekday() == 5),
            (date.weekday() == 6),
            (get_season(date) == 'summer'),
            (get_season(date) == 'fall'),
            (get_season(date) == 'winter'),
            (get_season(date) == 'spring'),
        ]
        features.append(feature_vector)
        labels.append(int(date in historic_dates))
    
    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(features, labels)
    xgb.plot_importance(model, importance_type='weight')
    plt.show()
    
    last_date = max_date
    future_dates = [last_date + timedelta(days=i) for i in range(1, days_into_the_future + 1)]
    future_features = []

    for date in future_dates:
        feature_vector = [
            np.sin(2 * np.pi * date.day / 31),
            np.cos(2 * np.pi * date.day / 31),
            np.sin(2 * np.pi * date.month / 12),
            np.cos(2 * np.pi * date.month / 12),
            (date.weekday() == 0),
            (date.weekday() == 1),
            (date.weekday() == 2),
            (date.weekday() == 3),
            (date.weekday() == 4),
            (date.weekday() == 5),
            (date.weekday() == 6),
            (get_season(date) == 'summer'),
            (get_season(date) == 'fall'),
            (get_season(date) == 'winter'),
            (get_season(date) == 'spring'),
        ]
        future_features.append(feature_vector)

    predictions = model.predict(future_features)
    predicted_purchase_dates = [date for date, pred in zip(future_dates, predictions) if pred == 1]

    return predicted_purchase_dates

def generate_purchase_data(start_date: datetime, end_date: datetime) -> list:
    import random
    current_data = []
    day = start_date
    friday_counter = 0  # Track every 4th Friday

    while day <= end_date:
        # Monday (100% chance of purchase)
        if day.weekday() == 0:  # Monday
            current_data.append((day, round(random.uniform(20, 30), 2)))
        
        # Thursday (80% chance of purchase)
        elif day.weekday() == 3 and get_season(day.date()) == 'summer':  # Thursday
            if random.random() < 0.8:  # 80% probability
                current_data.append((day, round(random.uniform(15, 25), 2)))

        day += timedelta(days=1)

    return current_data

start_date = datetime(2009, 12, 1)
end_date = datetime(2010, 12, 31)
current_data = generate_purchase_data(start_date, end_date)

predicted_dates = predict_next_purchase_dates(current_data, days_into_the_future=220)
print("days")
for date in predicted_dates:
    print(date.isoweekday())

# Plotting
plt.figure(figsize=(12, 6))

# Plot historical purchase dates
historic_dates = [i[0].date() for i in current_data if i[1] > 0]
plt.plot(historic_dates, [1] * len(historic_dates), 'bo', label='Historical Purchases')

# Plot predicted purchase dates
plt.plot(predicted_dates, [1] * len(predicted_dates), 'rx', label='Predicted Purchases')

# Formatting plot
plt.xlabel('Date')
plt.ylabel('Purchase (1=Yes)')
plt.title('Historical and Predicted Purchase Dates')
plt.legend()
plt.grid(True)
plt.show()