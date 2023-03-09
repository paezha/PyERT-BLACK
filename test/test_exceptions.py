import pytest
import geopandas as gpd
import pandas as pd
import os
import sys

from src import Exceptions as e

sample_gps_file_path = os.getcwd().split("PyERT-BLACK")[0] + 'PyERT-BLACK/quarto-example/data/sample-gps'


def input_gps_data(file_path):
    gps_data_path = file_path
    if '.' in gps_data_path[-4:] and '.csv' != gps_data_path[-4:]:
        raise e.InvalidFileFormatException()


def check_file_path(file_path):
    if not os.path.isfile(file_path):
        raise e.InvalidFilePathException


def check_folder_exists(folder_path):
    if not os.path.isdir(folder_path.rsplit('/', 1)[0]):
        raise e.InvalidInputException()


def check_empty_values(data_path):
    data = pd.read_csv(data_path)
    if data.isnull().values.any():
        raise e.InvalidDataException

def check_geometry_points(data_path):
    data = pd.read_csv(data_path)
    gps_data = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data.longitude, data.latitude))
    if gps_data.is_empty[2]:
        raise e.InvalidGPSDataException


@pytest.mark.parametrize(
    'gps_data_path', [(sample_gps_file_path + '/sample-gps-1.gpx')]
)
def test_invalid_file_format(gps_data_path):
    with pytest.raises(e.InvalidFileFormatException):
        input_gps_data(gps_data_path)


@pytest.mark.parametrize(
    'file_path', [(sample_gps_file_path + '/filedoesnotexist.txt')]
)
def test_invalid_file_path(file_path):
    with pytest.raises(e.InvalidFilePathException):
        check_file_path(file_path)


@pytest.mark.parametrize(
    'folder_path', [(sample_gps_file_path + '/FolderDoesNotExist/FolderDoesNotExist')]
)
def test_invalid_input(folder_path):
    with pytest.raises(e.InvalidInputException):
        check_folder_exists(folder_path)


@pytest.mark.parametrize(
    'data_path', [(sample_gps_file_path + '/sample-gps-4.csv')]
)
def test_invalid_data(data_path):
    with pytest.raises(e.InvalidDataException):
        check_empty_values(data_path)


@pytest.mark.parametrize(
    'data_path', [(sample_gps_file_path + '/sample-gps-5.csv')]
)
def test_invalid_gps_data(data_path):
    with pytest.raises(e.InvalidGPSDataException):
        check_geometry_points(data_path)



