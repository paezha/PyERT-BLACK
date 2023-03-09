import pytest
import geopandas as gpd
import pandas as pd
import os
from shapely.geometry import Point
import sys


from src import ModeDetection as md

sample_gps_file_path = os.getcwd().split(
    "PyERT-BLACK")[0] + 'PyERT-BLACK/quarto-example/data/sample-gps'


def test_distance():
    p1 = Point(1, 1)
    p2 = Point(2, 2)
    ModeDetection = md.ModeDetection(processed_data=None)
    dist1 = ModeDetection.distance(p1, p2)
    dist2 = ModeDetection.distance(p1, p1)
    assert round(dist1) == 157402
    assert dist2 == 0
