from datetime import datetime, timedelta
from calendar import monthrange
from typing import List, Tuple
from collections import Counter
import xgboost as xgb
import numpy as np
import matplotlib.pyplot as plt

def is_in_last_7_days_of_month(date: datetime) -> bool:
    last_day = monthrange(date.year, date.month)[1]
    threshold_day = last_day - 6
    return(date.day >= threshold_day)

def get_season(month: int) -> int:
    """Determina la temporada a partir del mes."""
    if month in [12, 1, 2]:
        return 1  # Invierno
    elif month in [3, 4, 5]:
        return 2  # Primavera
    elif month in [6, 7, 8]:
        return 3  # Verano
    else:
        return 4  # Otoño
    
def calculate_sma_intervals(dates: List[datetime.date], window: int = 5) -> List[float]:
    """Calcula el promedio móvil simple de los intervalos entre compras."""
    intervals = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
    sma_intervals = [np.mean(intervals[max(0, i - window + 1):i + 1]) if i >= window - 1 else np.nan for i in range(len(intervals))]
    return [np.nan] + sma_intervals

def predict_next_purchase_dates(historic_data: List[Tuple[datetime, float]], days_into_the_future: int) -> List[datetime]:
    if not historic_data:
        return []

    historic_dates = list({i[0].date() for i in historic_data if i[1] > 0})
    historic_dates.sort()

    min_date = historic_dates[0]
    max_date = historic_dates[-1]
    all_dates = [min_date + timedelta(days=i) for i in range((max_date - min_date).days + 1)]
    
    last_purchase_date = min_date
    sma_intervals = calculate_sma_intervals(historic_dates)
    sma_interval_dict = dict(zip(historic_dates, sma_intervals))

    features = []
    labels = []

    for date in all_dates:
        feature_vector = [
            # date.toordinal(),
            date.weekday(),
            date.month,
            get_season(date.month),
            # last_purchase_date.toordinal(),
            (date - last_purchase_date).days,
            int(date.day <= 7),
            is_in_last_7_days_of_month(date),
            # sma_interval_dict.get(date, np.nan)
        ]
        features.append(feature_vector)
        labels.append(int(date in historic_dates))

        if date in historic_dates:
            last_purchase_date = date

    counter = Counter(labels)
    scale_pos_weight = counter[0] / counter[1]

    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=200,
        max_depth=60,
        learning_rate=0.05,
        gamma=1,
        reg_alpha=0.5,
        scale_pos_weight=scale_pos_weight
    )

    model.fit(features, labels)
    print(features[1])
    print(features[-2])
    xgb.plot_importance(model, importance_type='weight')
    plt.show()

    last_date = max_date
    future_dates = [last_date + timedelta(days=i) for i in range(1, days_into_the_future + 1)]
    future_features = []

    for date in future_dates:
        feature_vector = [
            # date.toordinal(),
            date.weekday(),
            date.month,
            get_season(date.month),
            # last_purchase_date.toordinal(),
            (date - last_purchase_date).days,
            int(date.day <= 7),
            is_in_last_7_days_of_month(date),
            # sma_interval_dict.get(date, np.nan)
        ]
        future_features.append(feature_vector)

        if model.predict([feature_vector])[0] == 1:
            last_purchase_date = date

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
        elif day.weekday() == 3:  # Thursday
            if random.random() < 0.8:  # 80% probability
                current_data.append((day, round(random.uniform(15, 25), 2)))
        
        # Friday (purchase only every 4th Friday)
        elif day.weekday() == 4:  # Friday
            if friday_counter % 4 == 0:
                current_data.append((day, round(random.uniform(10, 20), 2)))
            friday_counter += 1

        day += timedelta(days=1)

    return current_data

# Generate data from October 1, 2009 to December 31, 2010
start_date = datetime(2008, 12, 1)
end_date = datetime(2010, 12, 31)
current_data = generate_purchase_data(start_date, end_date)

predicted_dates = predict_next_purchase_dates(current_data, days_into_the_future=3000)
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