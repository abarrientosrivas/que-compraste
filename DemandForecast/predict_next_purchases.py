import xgboost as xgb
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import random
from typing import List, Tuple, Dict
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

    last_purchase_date = None
    for date in all_dates:
        days_since_last_purchase = (date - last_purchase_date).days if last_purchase_date else np.nan

        feature_vector = [
            np.sin(2 * np.pi * date.day / 31),     # day
            np.cos(2 * np.pi * date.day / 31),
            np.sin(2 * np.pi * date.month / 12),   # month
            np.cos(2 * np.pi * date.month / 12),
            (date.weekday() == 0),                 # day of the week
            (date.weekday() == 1),
            (date.weekday() == 2),
            (date.weekday() == 3),
            (date.weekday() == 4),
            (date.weekday() == 5),
            (date.weekday() == 6),
            (get_season(date) == 'summer'),        # season
            (get_season(date) == 'fall'),
            (get_season(date) == 'winter'),
            (get_season(date) == 'spring'),
            days_since_last_purchase,              # days since last purchase
        ]
        features.append(feature_vector)
        labels.append(int(date in historic_dates))
        if date in historic_dates:
            last_purchase_date = date
    
    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(features, labels)
    
    last_date = max_date
    future_dates = [last_date + timedelta(days=i) for i in range(1, days_into_the_future + 1)]
    predicted_purchase_dates = []

    for date in future_dates:
        days_since_last_purchase = (date - last_purchase_date).days if last_purchase_date else np.nan

        feature_vector = [
            np.sin(2 * np.pi * date.day / 31),     # day
            np.cos(2 * np.pi * date.day / 31),
            np.sin(2 * np.pi * date.month / 12),   # month
            np.cos(2 * np.pi * date.month / 12),
            (date.weekday() == 0),                 # day of the week
            (date.weekday() == 1),
            (date.weekday() == 2),
            (date.weekday() == 3),
            (date.weekday() == 4),
            (date.weekday() == 5),
            (date.weekday() == 6),
            (get_season(date) == 'summer'),        # season
            (get_season(date) == 'fall'),
            (get_season(date) == 'winter'),
            (get_season(date) == 'spring'),
            days_since_last_purchase,              # days since last purchase
        ]
        prediction = model.predict([feature_vector])[0]
        if prediction == 1:
            predicted_purchase_dates.append(date)
            last_purchase_date = date

    return predicted_purchase_dates

def get_quantity_features_vector(date, last_purchase_quantity, last_purchase_date, consolidated_historic_data, time_index):
    days_since_last_purchase = (date - last_purchase_date).days if last_purchase_date else np.nan

    return  [
            np.sin(2 * np.pi * date.day / 31),     # day
            np.cos(2 * np.pi * date.day / 31),
            np.sin(2 * np.pi * date.month / 12),   # month
            np.cos(2 * np.pi * date.month / 12),
            (date.weekday() == 0),                 # day of the week
            (date.weekday() == 1),
            (date.weekday() == 2),
            (date.weekday() == 3),
            (date.weekday() == 4),
            (date.weekday() == 5),
            (date.weekday() == 6),
            (get_season(date) == 'summer'),        # season
            (get_season(date) == 'fall'),
            (get_season(date) == 'winter'),
            (get_season(date) == 'spring'),
            last_purchase_quantity or np.nan,
            days_since_last_purchase,
            recent_quantity_sum(consolidated_historic_data, date, 7),
            recent_quantity_sum(consolidated_historic_data, date, 30),
            recent_quantity_sum(consolidated_historic_data, date, 90),         
            recent_purchases_ema_quantity(consolidated_historic_data, date, 7), 
            recent_purchases_ema_quantity(consolidated_historic_data, date, 30), 
            recent_purchases_ema_quantity(consolidated_historic_data, date, 90),   
            time_index,
        ]

def predict_next_purchase_quantities(historic_data: List[Tuple[datetime, float]], future_dates: List[datetime]) -> List[Tuple[datetime, float]]:
    if not historic_data or not future_dates:
        return
    
    consolidated_data: Dict[datetime, float] = {}
    for date, quantity in historic_data:
        date_only = date.date()
        if date_only in consolidated_data:
            consolidated_data[date_only] += quantity
        else:
            consolidated_data[date_only] = quantity
    consolidated_historic_data = sorted(consolidated_data.items())
    
    features = []
    labels = []
    last_purchase_quantity = None
    last_purchase_date = None
    time_index = 0
    for date, quantity in consolidated_historic_data:

        feature_vector = get_quantity_features_vector(date, last_purchase_quantity, last_purchase_date, consolidated_historic_data, time_index)

        time_index += (date - last_purchase_date).days if last_purchase_date else 0
        features.append(feature_vector)
        labels.append(quantity)
        last_purchase_quantity = quantity
        last_purchase_date = date
    
    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100)
    model.fit(features, labels)

    predictions = []
    last_purchase_date, last_purchase_quantity = consolidated_historic_data[-1]
    for date in future_dates:
        feature_vector = get_quantity_features_vector(date, last_purchase_quantity, last_purchase_date, consolidated_historic_data, time_index)

        time_index += (date - last_purchase_date).days if last_purchase_date else 0

        predicted_quantity = model.predict([feature_vector])[0]
        predictions.append(predicted_quantity)
        consolidated_historic_data.append((date, predicted_quantity))

        last_purchase_quantity = predicted_quantity
        last_purchase_date = date

    return list(zip(future_dates, predictions))

def recent_quantity_sum(data: List[Tuple[datetime, float]], target_date, days_window: int) -> float:
    total_quantity = 0
    for date, q in data:
        if date < target_date and date >= target_date - timedelta(days=days_window):
            total_quantity += q
    return total_quantity

def recent_purchases_ema_quantity(data: List[Tuple[datetime, float]], target_date: datetime, purchases_window: int) -> float:
    quantities = [q for date, q in data if date < target_date and q > 0]
    recent_quantities = quantities[-purchases_window:]
    if len(recent_quantities) < purchases_window:
        return np.nan
    return get_ema_quantity(recent_quantities)

def get_ema_quantity(quantities: List[float]) -> float:
    if not quantities:
        return np.nan
    
    alpha = 2 / (len(quantities) + 1)
    ema = quantities[0]
    for quantity in quantities[1:]:
        ema = (quantity * alpha) + (ema * (1 - alpha))
    
    return ema

def generate_purchase_data(start_date: datetime, end_date: datetime, noise_level: float = 2.0, trend_slope: float = 0.005) -> List[Tuple[datetime, float]]:
    current_data = []
    day = start_date
    total_days = (end_date - start_date).days

    # Seasonality factor with a sinusoidal pattern to simulate peaks in specific seasons
    seasonal_variation = 10 * np.sin(2 * np.pi * np.arange(total_days) / 365) + 30  # Peak at 30, low at 20

    day_count = 0  # Counter to apply the seasonal variation correctly
    while day <= end_date:
        # Calculate the linear trend increase for the current day
        trend_increase = trend_slope * day_count

        if day.weekday() == 0 and get_season(day.date()) == 'summer':  # Mondays during summer
            base_quantity = 30 + seasonal_variation[day_count] + trend_increase  # Higher quantity in summer
            noise = np.random.normal(0, noise_level)  # Add noise
            current_data.append((day, round(base_quantity + noise, 2)))
        
        elif day.weekday() == 3 and get_season(day.date()) != 'summer':  # Thursdays in non-summer seasons
            if random.random() < 0.5:
                base_quantity = 20 + seasonal_variation[day_count] + trend_increase  # Lower quantity in non-summer
                noise = np.random.normal(0, noise_level)  # Add noise
                current_data.append((day, round(base_quantity + noise, 2)))
        
        day += timedelta(days=1)
        day_count += 1  # Increment to follow the seasonal variation

    return current_data

start_date = datetime(2005, 10, 1)
end_date = datetime(2010, 12, 31)
current_data = generate_purchase_data(start_date, end_date)

# current_data = [
# [datetime(2024,10,17),1],
# [datetime(2024,10,8),1],
# [datetime(2024,10,1),1],
# [datetime(2024,9,14),1],
# [datetime(2024,9,9),1],
# [datetime(2024,9,3),1],
# [datetime(2024,8,28),1],
# [datetime(2024,8,14),1],
# [datetime(2024,7,29),1],
# [datetime(2024,7,22),1],
# [datetime(2024,7,8),1],
# [datetime(2024,6,16),1],
# ]

# current_data = [
# [datetime(2024,11,4),2],
# [datetime(2024,11,4),2],
# [datetime(2024,10,2),1.5],
# [datetime(2024,10,2),2],
# [datetime(2024,9,3),2],
# [datetime(2024,9,3),1],
# [datetime(2024,9,3),1.5],
# [datetime(2024,8,5),2],
# [datetime(2024,8,5),1.5],
# [datetime(2024,8,5),1.5],
# [datetime(2024,7,1),2],
# [datetime(2024,7,1),2],
# [datetime(2024,6,3),2],
# [datetime(2024,6,1),1.5],
# [datetime(2024,4,5),1],
# [datetime(2024,4,5),1],
# [datetime(2024,4,3),2],
# [datetime(2024,3,2),2],
# [datetime(2024,3,2),2],
# ]

# Prepare feature vectors for each date in the historical data
features = []
last_q = None
last_d = None

consolidated_data: Dict[datetime, float] = {}
for date, quantity in current_data:
    date_only = date.date()
    if date_only in consolidated_data:
        consolidated_data[date_only] += quantity
    else:
        consolidated_data[date_only] = quantity
consolidated_historic_data = sorted(consolidated_data.items())
for date, quantity in consolidated_historic_data:
    feature_vector = get_quantity_features_vector(date, last_q, last_d, consolidated_historic_data, time_index=0)
    feature_vector.append(quantity)
    features.append((date, *feature_vector))
    last_q = quantity
    last_d = date

# Convert features list to DataFrame
columns = [
    "date", "day_sin", "day_cos", "month_sin", "month_cos",
    "weekday_mon", "weekday_tue", "weekday_wed", "weekday_thu",
    "weekday_fri", "weekday_sat", "weekday_sun",
    "is_summer", "is_fall", "is_winter", "is_spring",
    "last_purchase_quantity", "days_since_last_purchase",
    "recent_sum_7", "recent_sum_30", "recent_sum_90",
    "ema_7", "ema_30", "ema_90", "time_index", "quantity"
]
df_features = pd.DataFrame(features, columns=columns)
df_features.set_index("date", inplace=True)

# Plotting each feature individually
for column in df_features.columns[-1:]:
    plt.figure(figsize=(10, 5))
    plt.plot(df_features.index, df_features[column], label=column)
    plt.title(f'{column} over Time')
    plt.xlabel('Date')
    plt.ylabel(column)
    plt.legend()
    plt.show()

predicted_dates = predict_next_purchase_dates(current_data, days_into_the_future=380)

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
    
future_purchases = predict_next_purchase_quantities(current_data, predicted_dates)

historic_dates, historic_quantities = zip(*consolidated_historic_data)
predicted_dates, predicted_quantities = zip(*future_purchases)

predicted_dates = (historic_dates[-1],) + predicted_dates
predicted_quantities = (historic_quantities[-1],) + predicted_quantities

# Plot historical data
plt.figure(figsize=(12, 6))
plt.plot(historic_dates, historic_quantities, label="Historical Data", marker="o", linestyle="-")

# Plot predicted data
plt.plot(predicted_dates, predicted_quantities, label="Predicted Data", marker="x", linestyle="--", color="orange")

# Labeling
plt.title("Purchase Quantity Trends")
plt.xlabel("Date")
plt.ylabel("Purchase Quantity")
plt.legend()
plt.grid(True)
plt.show()
