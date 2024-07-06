# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 17:35:22 2024

@author: louise
"""

import requests
import pandas as pd
import numpy as np
import io
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
#import time

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

    # Reset index starting from 1
    uk_locations.reset_index(drop=True, inplace=True)
    
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
    ukweather = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_station = {executor.submit(get_isd_data, station, year): station for station in stations}
        for future in tqdm(as_completed(future_to_station), total=len(stations), desc="Fetching data"):
            station = future_to_station[future]
            try:
                uk_weather_2023 = future.result()
                if uk_weather_2023 is not None:
                    ukweather.append(uk_weather_2023)
            except Exception as exc:
                print(f'{station} generated an exception: {exc}')
    
    return pd.concat(ukweather, ignore_index=True) if ukweather else None

# Assuming uk_locations is your DataFrame and it has a column named 'station_code'
# If the column name is different, replace 'station_code' with the actual column name
stations = uk_locations['station_code'].tolist()

test_locations = uk_locations.head(3) 

test_stations = test_locations['station_code'].tolist()

year = 2023

uk_weather_2023 = get_data_for_stations(stations, year)
if uk_weather_2023 is not None:
    print(uk_weather_2023.head())
    print(f"Total records: {len(uk_weather_2023)}")
    print(f"Unique stations: {uk_weather_2023['STATION'].nunique()}")
    print(f"Date range: {uk_weather_2023['DATE'].min()} to {uk_weather_2023['DATE'].max()}")
    print(f"Months covered: {sorted(uk_weather_2023['DATE'].dt.month.unique())}")

    uk_weather_2023 = uk_weather_2023.loc[:,['STATION','DATE','LATITUDE','LONGITUDE',
                    'NAME','WND','CIG','VIS','TMP','DEW','SLP']] 
    
    uk_weather_2023_processed = uk_weather_2023 
    
    
    uk_weather_2023_processed[['wd', 'wdstatus', 'windtype', 'ws', 'wsstatus']] = uk_weather_2023_processed['WND'].str.split(',', expand=True).apply(pd.to_numeric, errors='coerce')
   
    
    uk_weather_2023_processed[['ceil_hgt', 'chstatus', 'notused', 'notused2']] = uk_weather_2023_processed['CIG'].str.split(',', expand=True).apply(pd.to_numeric, errors='coerce')
     
    uk_weather_2023_processed[['vis', 'visstatus', 'notused3', 'notused4']] = uk_weather_2023_processed['VIS'].str.split(',', expand=True).apply(pd.to_numeric, errors='coerce')
    
    uk_weather_2023_processed[['tmp', 'tmpstatus']] = uk_weather_2023_processed['TMP'].str.split(',', expand=True).apply(pd.to_numeric, errors='coerce')
    
    uk_weather_2023_processed[['dewpt', 'dewptstatus']] = uk_weather_2023_processed['DEW'].str.split(',', expand=True).apply(pd.to_numeric, errors='coerce')
    
    
    uk_weather_2023_processed[['pres', 'presstatus']] = uk_weather_2023_processed['SLP'].str.split(',', expand=True).apply(pd.to_numeric, errors='coerce')
   
   
    
    uk_weather_2023_processed = uk_weather_2023_processed.loc[:,['STATION','DATE','LATITUDE','LONGITUDE',
                    'wd','wdstatus','ws','wsstatus','ceil_hgt','chstatus','vis','visstatus','tmp','tmpstatus','dewpt', 'dewptstatus', 'pres','presstatus']]  
     
          
    
    uk_weather_2023_processed.loc[~uk_weather_2023_processed['wdstatus'].isin([1, 5]), 'wd'] = pd.NA
    
    uk_weather_2023_processed.loc[~uk_weather_2023_processed['wsstatus'].isin([1, 5]), 'ws'] = pd.NA
    
    uk_weather_2023_processed.loc[~uk_weather_2023_processed['chstatus'].isin([1, 5]), 'ceil_hgt'] = pd.NA
    
    uk_weather_2023_processed.loc[~uk_weather_2023_processed['visstatus'].isin([1, 5]), 'vis'] = pd.NA
    
    uk_weather_2023_processed.loc[~uk_weather_2023_processed['tmpstatus'].isin([1, 5]), 'tmp'] = pd.NA
    
    uk_weather_2023_processed.loc[~uk_weather_2023_processed['dewptstatus'].isin([1, 5]), 'dewpt'] = pd.NA
    
    uk_weather_2023_processed.loc[~uk_weather_2023_processed['presstatus'].isin([1, 5]), 'pres'] = pd.NA
    
      
    uk_weather_2023_processed = uk_weather_2023_processed.loc[:,['STATION','DATE','LATITUDE','LONGITUDE',
                    'wd','ws','tmp','vis','pres','dewpt','ceil_hgt']] 
  
    # Optional: Save to CSV
    # data.to_csv(f"weather_data_{year}.csv", index=False)
 



