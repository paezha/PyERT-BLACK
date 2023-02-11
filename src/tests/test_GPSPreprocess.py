import pytest
import geopandas as gpd
import pandas as pd
import os
import sys

import GPSPreprocess as gpsp

sample_gps_file_path = os.getcwd().split("PyERT-BLACK")[0] + 'PyERT-BLACK/quarto-example/data/sample-gps'

@pytest.mark.parametrize(
    'sample_gps', [(sample_gps_file_path+'/sample-gps-1.csv')]
)
def test_getData(sample_gps):
    Data = pd.read_csv(sample_gps)
    DataLength = len(Data)
    GPSData = gpsp.GPSPreprocess(data=Data)
    ProcessedData = GPSData.getData()
    ProcessedDataLength = len(ProcessedData)
    point = gpd.points_from_xy(x=[ProcessedData['longitude'][0]], y=[ProcessedData['latitude'][0]])
    assert ProcessedData['latitude'][0] == Data['latitude'][0]
    assert ProcessedData['longitude'][0] == Data['longitude'][0]
    assert ProcessedData['geometry'][0] == point[0]
    assert 'geometry' not in Data
    assert 'geometry' in ProcessedData
    assert DataLength != ProcessedDataLength

@pytest.mark.parametrize(
    'sample_gps', [(sample_gps_file_path+'/sample-gps-1.csv')]
)
def test_filterData(sample_gps):
    Data = pd.read_csv(filepath_or_buffer=sample_gps, nrows=4)
    Data1Length = len(Data)
    GPSData = gpsp.GPSPreprocess(data=None)
    GPSData.data = Data
    FilteredData1 = GPSData.filterData(GPSData.data)
    FilteredData1Length = len(FilteredData1)
    Duplicate1 = FilteredData1.duplicated()

    GPSData.data = Data.append(Data[:1])
    GPSData.data.reset_index(drop=True, inplace=True)
    Data2Length = len(GPSData.data)
    Duplicate2 = GPSData.data.duplicated()
    FilteredData2 = GPSData.filterData(GPSData.data)
    FilteredData2Length = len(FilteredData2)
    Duplicate3 = FilteredData2.duplicated()

    assert Data1Length == FilteredData1Length
    for i in Duplicate1:
        assert i == False
    assert Data2Length != FilteredData2Length
    assert Duplicate2[4] == True
    for i in Duplicate3:
        assert i == False