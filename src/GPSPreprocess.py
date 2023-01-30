import geopandas as gpd
import pandas as pd
import os

class GPSPreprocess:
    def __init__(self, data=None):
        data = data
        filteredData = self.filterData(data)
        smoothedData = self.smoothData(filteredData)
        self.processedData = smoothedData

# Return GeoDataFrame of processed data
    def getData(self):
        return self.processedData

# Remove all duplicate rows with the same latitudes and longitudes and converts DataFrame to GeoDataFrame
    def filterData(self, data):
        # Removes all rows in DataFrame with duplicate latitudes and longitudes
        data = data.drop_duplicates(subset=['latitude', 'longitude'], keep='first')

        # Converts DataFrame to GeoDataFrame and adds 'geometry' column which will be points based on the
        # latitude and longitude from the DataFrame
        filteredData = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data.longitude, data.latitude))

        # Reset index of GeoDataFrame
        filteredData.reset_index(drop=True, inplace=True)

        return filteredData

# Remove all rows where 'Speed_kmh' > 50.0
    def smoothData(self, data):
        # Remove all rows that have a value of greater than 50.0 for the column 'Speed_kmh'
        smoothedData = data.drop(data[data.Speed_kmh > 50.0].index)

        # Reset index of GeoDataFrame
        smoothedData.reset_index(drop=True, inplace=True)
        return smoothedData

