# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 17:35:22 2024

@author: louise
"""

import requests
import pandas as pd
import io
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# URL to the ISD history CSV file
url = "https://www1.ncdc.noaa.gov/pub/data/noaa/isd-history.csv"

try:
    # Download the CSV file
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for bad response status
    
    # Load CSV data into a pandas DataFrame
    all_locations = pd.read_csv(BytesIO(response.content))
    
    # Filter data for UK locations with end dates after 01-01-2024
    start_date_threshold = pd.to_datetime('2014-01-01')
    end_date_threshold = pd.to_datetime('2024-06-01')
    
    # Convert BEGIN and END columns to datetime format
    all_locations['BEGIN'] = all_locations['BEGIN'].astype(str)
    all_locations['END'] = all_locations['END'].astype(str)
    all_locations.loc[:, 'BEGIN'] = pd.to_datetime(all_locations['BEGIN'], format='%Y%m%d')
    all_locations.loc[:, 'END'] = pd.to_datetime(all_locations['END'], format='%Y%m%d')   
    
        
    uk_locations = all_locations[(all_locations['CTRY'] == 'UK') & 
                             (all_locations['END'] > end_date_threshold) & 
                             (all_locations['BEGIN'] < start_date_threshold)]
   
    uk_locations = uk_locations.copy(deep=True)

    # Create the new column on the copy
    uk_locations['station_code'] = uk_locations['USAF'].astype(str) + uk_locations['WBAN'].astype(str).str.zfill(5)

    # Use the copy for further operations
    stations = uk_locations['station_code'].tolist()

except requests.exceptions.RequestException as e:
    print(f"Error downloading data: {e}")
    

def get_isd_data(station, year):
    base_url = f"https://www.ncei.noaa.gov/data/global-hourly/access/{year}/"
    file_name = f"{station}"
    
    url = f"{base_url}{file_name}.csv"
    response = requests.get(url)
    
    if response.status_code == 200:
        weather = pd.read_csv(io.StringIO(response.text), low_memory=False)
        weather['DATE'] = pd.to_datetime(weather['DATE'])
        weather['STATION'] = station  # Add station ID to the dataframe
        return weather
    else:
        print(f"Failed to retrieve data for station {station}: {response.status_code}")
        return None

def get_data_for_stations(stations, year):
    uk_weather_2023 = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_station = {executor.submit(get_isd_data, station, year): station for station in stations}
        for future in tqdm(as_completed(future_to_station), total=len(stations), desc="Fetching data"):
            station = future_to_station[future]
            try:
                data = future.result()
                if data is not None:
                    uk_weather_2023.append(data)
            except Exception as exc:
                print(f'{station} generated an exception: {exc}')
    
    return pd.concat(uk_weather_2023, ignore_index=True) if uk_weather_2023 else None

# Assuming uk_locations is your DataFrame and it has a column named 'station_code'
# If the column name is different, replace 'station_code' with the actual column name
stations = uk_locations['station_code'].tolist()

test_locations = uk_locations.head(3) 

test_stations = test_locations['station_code'].tolist()

year = 2023

data = get_data_for_stations(stations, year)
if data is not None:
    print(data.head())
    print(f"Total records: {len(data)}")
    print(f"Unique stations: {data['STATION'].nunique()}")
    print(f"Date range: {data['DATE'].min()} to {data['DATE'].max()}")
    print(f"Months covered: {sorted(data['DATE'].dt.month.unique())}")
    
    # Optional: Save to CSV
    # data.to_csv(f"weather_data_{year}.csv", index=False)

# Optional: Merge the weather data with uk_locations if needed
# merged_data = pd.merge(data, uk_locations, left_on='STATION', right_on='station_code', how='left')
