import pytest
import geopandas as gpd
import pandas as pd
import os
import sys
from shapely.geometry import Point, Polygon
import activity_locations_identification as ali

pal_data_from_gpkg = gpd.read_file("test_data/test_al_info_data.gpkg", layer='buildings')
lu_data_from_gpkg = gpd.read_file("test_data/test_al_info_data.gpkg", layer='landuse')
pal_data_from_gpkg.set_index(['element_type', 'osmid'], inplace=True)
lu_data_from_gpkg.set_index(['element_type', 'osmid'], inplace=True)
pal_data_from_gpkg = pal_data_from_gpkg.to_crs(epsg=32620)
lu_data_from_gpkg = lu_data_from_gpkg.to_crs(epsg=32620)
test_stop_seg_path = "C:/Users/Clyde/PyERT-BLACK/src/test_data/test_al_info_stop_seg/test_al_info_stop_seg.shp"
test_stop_seg = gpd.read_file(test_stop_seg_path)
test_stop_seg = test_stop_seg.to_crs(epsg=32620)

pal_gdf = pal_data_from_gpkg
lu_gdf = lu_data_from_gpkg
al_gdf = test_stop_seg


def test_identify_lu():
    test_lu_gdf = ali.identify_lu(al_gdf, lu_gdf)

    for i in range(test_lu_gdf.shape[0]):
        assert test_lu_gdf.iloc[i]['lu_classification'] == 'residential'
        assert test_lu_gdf.iloc[i]['lu_index'] == ('relation', 13745200)


def test_identify_pal():
    test_pal_gdf = ali.identify_pal(al_gdf, pal_gdf)

    for i in range(test_pal_gdf.shape[0]):
        point = al_gdf.iloc[i]['geometry']

        polygon = test_pal_gdf.iloc[i]['building_geometry']
        distance = point.distance(polygon)
        assert distance < 100
