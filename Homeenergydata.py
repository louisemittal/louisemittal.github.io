# -*- coding: utf-8 -*-
"""
Created on Thu Jun 27 12:09:57 2024

@author: louise
"""

import pandas as pd

# Load the data (assuming CSV files, adjust as needed)
Elecreadings = pd.read_excel('C:/Users/louis/OneDrive/Data investigations/home_energy_use/Home energy use.xlsx', sheet_name='Elecreadings')
Gasreadings = pd.read_excel('C:/Users/louis/OneDrive/Data investigations/home_energy_use/Home energy use.xlsx', sheet_name='Gasreadings')
met = pd.read_csv('C:/Users/louis/OneDrive/Data investigations/home_energy_use/metdata.csv', parse_dates=['date'], date_format='mixed')


# Ensure the timestamp columns are in datetime format
met['date'] = pd.to_datetime(met['date'], format='%d/%m/%Y %H:%M')
print(met.dtypes)

Elecreadings['Date'] = pd.to_datetime(Elecreadings['Date'])

# Initialize an empty list to store the results
mean_temps = []

# Loop through meter readings to calculate mean temperature between readings
for i in range(len(Elecreadings) - 1):
    end_date = Elecreadings['Date'].iloc[i]
    start_date = Elecreadings['Date'].iloc[i + 1]
    
    # Subset temperature data between the meter reading dates
    temp_subset = met[(met['date'] >= start_date) & (met['date'] < end_date)]
    
    # Calculate the mean temperature
    mean_temp = temp_subset['air_temp'].mean()
    
    # Store the result with the corresponding meter reading dates
    mean_temps.append({
        'start_date': start_date, 
        'end_date': end_date, 
        'mean_temperature': mean_temp
    })

# Convert the list of results to a DataFrame
mean_temps_df = pd.DataFrame(mean_temps)

# Print the result
print(mean_temps_df)

Elecwithtemp = pd.merge(Elecreadings, mean_temps_df, left_on='Date', right_on='end_date',  how='left')
Gaswithtemp = pd.merge(Gasreadings, mean_temps_df, left_on='Date', right_on='end_date',  how='left')

Elecwithtemp['InsulationPresent'] = Elecwithtemp['Date'] > '23/09/2023 00:00'
Gaswithtemp['InsulationPresent'] = Gaswithtemp['Date'] > '23/09/2023 00:00'

Elecwithtemp.to_csv('Elecwithtemp.csv', index=False)
Gaswithtemp.to_csv('Gaswithtemp.csv', index=False)
