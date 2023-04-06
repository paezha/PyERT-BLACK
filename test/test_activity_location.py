import pytest
import geopandas as gpd
import pandas as pd
import os
import sys
from shapely.geometry import Point, Polygon

from src import activity_locations_identification as ali
#import activity_locations_identification as ali

test_data_path = os.getcwd().split("PyERT-BLACK")[0] + 'PyERT-BLACK/test/test_data'
pal_data_from_gpkg = gpd.read_file(test_data_path + "/test_al_info_data.gpkg", layer='potential_activity_locations')
lu_data_from_gpkg = gpd.read_file(test_data_path + "/test_al_info_data.gpkg", layer='landuse')
pal_data_from_gpkg.set_index(['element_type', 'osmid'], inplace=True)
lu_data_from_gpkg.set_index(['element_type', 'osmid'], inplace=True)
pal_data_from_gpkg = pal_data_from_gpkg.to_crs(epsg=32620)
lu_data_from_gpkg = lu_data_from_gpkg.to_crs(epsg=32620)
test_stop_seg_path = test_data_path + "/test_al_info_stop_seg/test_al_info_stop_seg.shp"
test_stop_seg = gpd.read_file(test_stop_seg_path)
test_stop_seg = test_stop_seg.to_crs(epsg=32620)

pal_gdf = pal_data_from_gpkg
lu_gdf = lu_data_from_gpkg
al_gdf = test_stop_seg

@pytest.mark.parametrize(
    'al_gdf, lu_gdf, pal_gdf', 
    [(al_gdf, lu_gdf, pal_gdf)]
)
def test_identify_lu(al_gdf, lu_gdf, pal_gdf):
    test_lu_gdf = ali.create_al_info(al_gdf, lu_gdf, pal_gdf, 100)
    for i in range(test_lu_gdf.shape[0]):
        # Test if the land use type for all the potential activity locations 
        # are 'residential'
        #print(test_lu_gdf.iloc[i]['lu_type'])
        assert test_lu_gdf.iloc[i]['lu_type'] == 'residential'
        # Test if the identified potential activity locations 
        # are all in the predetermined land-use area
        assert test_lu_gdf.iloc[i]['lu_index'] == ('relation', 13745200)

@pytest.mark.parametrize(
    'al_gdf, lu_gdf, pal_gdf', 
    [(al_gdf, lu_gdf, pal_gdf)]
)
def test_identify_pal(al_gdf, lu_gdf, pal_gdf):
    test_pal_gdf = ali.create_al_info(al_gdf, lu_gdf, pal_gdf, 100)
    # Test if the distance from each of the identified potential activity 
    # locations to its nearest point in the al_gdf is less than 100 (meters)
    for i in range(test_pal_gdf.shape[0]):
        polygon = test_pal_gdf.iloc[i]['geometry']
        point =  al_gdf.loc[0]['geometry']
        min_dist = point.distance(polygon)
        for point in list(al_gdf['geometry']):
            curr_dist = point.distance(polygon)
            if min_dist > curr_dist:
                min_dist = curr_dist
        #print(min_dist)
        assert min_dist < 100