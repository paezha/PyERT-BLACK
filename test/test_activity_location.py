import pytest
import geopandas as gpd
import pandas as pd
import os
import sys
from shapely.geometry import Point, Polygon
from src import activity_locations_identification as ali



pal_data_from_gpkg = gpd.read_file("test_data/test_al_info_data.gpkg", layer='buildings')
lu_data_from_gpkg = gpd.read_file("test_data/test_al_info_data.gpkg", layer='landuse')
pal_data_from_gpkg.set_index(['element_type','osmid'], inplace=True)
lu_data_from_gpkg.set_index(['element_type','osmid'], inplace=True)
pal_data_from_gpkg = pal_data_from_gpkg.to_crs(epsg=32620)
lu_data_from_gpkg  = lu_data_from_gpkg.to_crs(epsg=32620)
test_stop_seg_path = "C:/University Grade4/4G06/gert_compiled_v4.3/map-matching_shared_v4.3/data/gps_trajectory/14640_20070403_17.shp"
test_stop_seg = gpd.read_file(test_stop_seg_path)
test_stop_seg = test_stop_seg.to_crs(epsg=32620)





@pytest.mark.parametrize(
    'al_gdf' = pal_data_from_gpkg
    'lu_gdf' = lu_data_from_gpkg
)
def test_identify_lu(al_gdf, lu_gdf):
    test_lu_gdf  = ali.identify_lu(al_gdf,lu_gdf)
    len_gdf = len(test_gdf)
    for i in len_gdf:
        assert test_gdf['lu_classification'][i] =
        assert test_gdf['lu_index'][i] =



@pytest.mark.parametrize(
    'al_gdf'= pal_data_from_gpkg
    'lu_gdf' = lu_data_from_gpkg
)

def test_identify_pal(al_gdf, lu_gdf):
    test_pal_gdf = ali.identify_pal(al_gdf, lu_gdf)
    len_gdf = len(test_gdf)
    for i in len_gdf:
        point = al_pal_gdf['building_index'][i]
        polygon = al_pal_gdf['building_geometry'][i]
        distance = point.distance(polygon)
        assert distance < 100