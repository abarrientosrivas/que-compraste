import xgboost as xgb
import numpy as np
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