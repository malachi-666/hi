import math
import pandas as pd
import numpy as np

# Removed sklearn dependency as per latest scope adjustments
GAS_PRICE_PER_GALLON = 3.85
AVG_MPG = 20.0

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in miles between two points."""
    if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
        return 999.0
    R = 3958.8
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def calculate_fuel_surcharge(distance_miles):
    """Calculates dynamic fuel surcharge based on distance."""
    if distance_miles == 999.0:
        return 10.0 # Default fallback
    gallons_needed = (distance_miles * 2) / AVG_MPG # Round trip
    return round(gallons_needed * GAS_PRICE_PER_GALLON, 2)

def cluster_pickups(df):
    """
    Dummy clustering function since we removed sklearn.
    Just groups everything into one cluster for now.
    """
    if df.empty or 'lat' not in df.columns or df['lat'].isnull().all():
        df['pickup_cluster'] = -1
        return df

    df['pickup_cluster'] = 0
    return df
