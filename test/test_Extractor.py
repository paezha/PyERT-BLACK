import pytest
import geopandas as gpd
import pandas as pd
import os
import sys

from src import GPSPreprocess as gpsp
from src import Extractor as ex
from src import ModeDetection as md

sample_gps_file_path = os.getcwd().split("PyERT-BLACK")[0] + 'PyERT-BLACK/quarto-example/data/sample-gps/'
expected_output_file_path = os.getcwd().split("PyERT-BLACK")[0] + 'PyERT-BLACK/test/test_data/test_extractor/'

@pytest.mark.parametrize(
    'sample_gps', [(sample_gps_file_path+'sample-gps-1.csv')]
)
@pytest.mark.parametrize(
    'expected_file_path', [(expected_output_file_path+'filled_expected.csv')]
)
def test_fill_points(sample_gps, expected_file_path):
    data = pd.read_csv(sample_gps)
    gps_data = gpsp.GPSPreprocess(data=data)
    processed_data = gps_data.get_data()
    ModeData = md.ModeDetection(processed_data=processed_data)
    episode_data = ModeData.get_episode_data()
    ExtractedData = ex.Extractor(episode_data=episode_data, processed_data=processed_data)
    filled = ExtractedData.fill_points(episode_data, processed_data)
    filled.to_csv(expected_output_file_path+'filled_out.csv', index=False)
    df = pd.read_csv(filepath_or_buffer=expected_file_path)
    filled_df = pd.read_csv(filepath_or_buffer=expected_output_file_path+'filled_out.csv')
    assert filled_df.equals(df) == True

@pytest.mark.parametrize(
    'sample_gps', [(sample_gps_file_path+'sample-gps-1.csv')]
)
@pytest.mark.parametrize(
    'expected_file_path', [(expected_output_file_path+'trip_expected.csv')]
)
def test_extract_trip_segments(sample_gps, expected_file_path):
    data = pd.read_csv(sample_gps)
    gps_data = gpsp.GPSPreprocess(data=data)
    processed_data = gps_data.get_data()
    ModeData = md.ModeDetection(processed_data=processed_data)
    episode_data = ModeData.get_episode_data()
    ExtractedData = ex.Extractor(episode_data=episode_data, processed_data=processed_data)
    trip = ExtractedData.get_trip_segments()
    trip.to_csv(expected_output_file_path+'trip_out.csv', index=False)
    df = pd.read_csv(filepath_or_buffer=expected_file_path)
    trip_df = pd.read_csv(filepath_or_buffer=expected_output_file_path+'trip_out.csv')
    assert trip_df.equals(df) == True

@pytest.mark.parametrize(
    'sample_gps', [(sample_gps_file_path+'sample-gps-1.csv')]
)
@pytest.mark.parametrize(
    'expected_file_path', [(expected_output_file_path+'stop_expected.csv')]
)
def test_extract_stop_segments(sample_gps, expected_file_path):
    data = pd.read_csv(sample_gps)
    gps_data = gpsp.GPSPreprocess(data=data)
    processed_data = gps_data.get_data()
    ModeData = md.ModeDetection(processed_data=processed_data)
    episode_data = ModeData.get_episode_data()
    ExtractedData = ex.Extractor(episode_data=episode_data, processed_data=processed_data)
    stop = ExtractedData.get_activity_locations()
    stop.to_csv(expected_output_file_path+'stop_out.csv', index=False)
    df = pd.read_csv(filepath_or_buffer=expected_file_path)
    stop_df = pd.read_csv(filepath_or_buffer=expected_output_file_path+'stop_out.csv')
    assert stop_df.equals(df) == True
   