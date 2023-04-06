"""
Module Name: GPSPreprocess
Source Name: GPSPreprocess.py
Creator: Zabrain Ali (aliz8@mcmaster.ca)
Requirements: Python 3.8 or later
Date Created: Feb 12, 2023
Last Revised: Mar 18, 2023
Description: Preprocess raw GPS data to remove redundant and outliers GPS points

Version History:
2023-02-12 (GPSPreprocess.py) Create skeleton of class GPSPreprocess
2023-02-15 (GPSPreprocess.py) Create get_data, filter_data and smooth_data
"""
import geopandas as gpd
import pandas as pd
import os

class GPSPreprocess:
    def __init__(self, data=None):
        data = data
        filtered_data = self.filter_data(data)
        smoothed_data = self.smooth_data(filtered_data)
        self.processed_data = smoothed_data

# Return GeoDataFrame of processed data
    def get_data(self):
        return self.processed_data

# Remove all duplicate rows with the same latitudes and longitudes and converts DataFrame to GeoDataFrame
    def filter_data(self, data):
        if data is None:
            return None
        else:
            # Removes all rows in DataFrame with duplicate latitudes and longitudes
            data = data.drop_duplicates(subset=['latitude', 'longitude'], keep='first')

            # Converts DataFrame to GeoDataFrame and adds 'geometry' column which will be points based on the
            # latitude and longitude from the DataFrame
            filtered_data = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data.longitude, data.latitude))

            # Reset index of GeoDataFrame
            filtered_data.reset_index(drop=True, inplace=True)

            return filtered_data

# Remove all rows where 'Speed_kmh' > 180.0
    def smooth_data(self, data):
        if data is None:
            return None
        else:
            # Remove all rows that have a value of greater than 180.0 for the column 'Speed_kmh'
            smoothed_data = data.drop(data[data.Speed_kmh > 180.0].index)

            # Reset index of GeoDataFrame
            smoothed_data.reset_index(drop=True, inplace=True)
            return smoothed_data

