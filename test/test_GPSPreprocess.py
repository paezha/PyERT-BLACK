import pytest
import geopandas as gpd
import pandas as pd
import os
import sys

from src import GPSPreprocess as gpsp

sample_gps_file_path = os.getcwd().split("PyERT-BLACK")[0] + 'PyERT-BLACK/quarto-example/data/sample-gps'

@pytest.mark.parametrize(
    'sample_gps', [(sample_gps_file_path+'/sample-gps-1.csv')]
)
def test_get_data(sample_gps):
    data = pd.read_csv(sample_gps)
    data_length = len(data)
    gps_data = gpsp.GPSPreprocess(data=data)
    processed_data = gps_data.get_data()
    processed_data_length = len(processed_data)
    point = gpd.points_from_xy(x=[processed_data['longitude'][0]], y=[processed_data['latitude'][0]])
    assert processed_data['latitude'][0] == data['latitude'][0]
    assert processed_data['longitude'][0] == data['longitude'][0]
    assert processed_data['geometry'][0] == point[0]
    assert 'geometry' not in data
    assert 'geometry' in processed_data
    assert data_length != processed_data_length

@pytest.mark.parametrize(
    'sample_gps', [(sample_gps_file_path+'/sample-gps-1.csv')]
)
def test_filter_data(sample_gps):
    data = pd.read_csv(filepath_or_buffer=sample_gps, nrows=4)
    data_length1 = len(data)
    gps_data = gpsp.GPSPreprocess(data=None)
    gps_data.data = data
    filtered_data1 = gps_data.filter_data(gps_data.data)
    filtered_data_length1 = len(filtered_data1)
    duplicate1 = filtered_data1.duplicated()

    gps_data.data = data.append(data[:1])
    gps_data.data.reset_index(drop=True, inplace=True)
    data_length2 = len(gps_data.data)
    duplicate2 = gps_data.data.duplicated()
    filtered_data2 = gps_data.filter_data(gps_data.data)
    filtered_data_length2 = len(filtered_data2)
    duplicate3 = filtered_data2.duplicated()

    assert data_length1 == filtered_data_length1
    for i in duplicate1:
        assert i == False
    assert data_length2 != filtered_data_length2
    assert duplicate2[4] == True
    for i in duplicate3:
        assert i == False

@pytest.mark.parametrize(
    'sample_gps', [(sample_gps_file_path+'/sample-gps-1.csv')]
)
def test_smooth_data(sample_gps):
    data = pd.read_csv(filepath_or_buffer=sample_gps, nrows=4)
    data_length = len(data)
    gps_data = gpsp.GPSPreprocess(data=None)
    gps_data.data = data
    smooth_data1 = gps_data.smoothdata(gps_data.data)
    smooth_data_length1 = len(smooth_data1)

    gps_data.data['Speed_kmh'][0] = 200.0
    gps_data.data['Speed_kmh'][1] = 180.0
    gps_data.data['Speed_kmh'][2] = 50.0
    gps_data.data['Speed_kmh'][3] = 180.000000000001

    smooth_data2 = gps_data.smooth_data(gps_data.data)
    smooth_data_length2 = len(smooth_data2)

    assert data_length == smooth_data_length1
    assert data_length != smooth_data_length2
    assert smooth_data_length2 == 2
    assert smooth_data2['Speed_kmh'][0] == 180.0
    assert smooth_data2['Speed_kmh'][1] == 50.0

    for i in smooth_data2['Speed_kmh']:
        assert i <= 180.0
