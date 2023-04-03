import pytest
import geopandas as gpd
import pandas as pd
import osmnx as ox
import os
import sys
from src import route_solver as rs

#test_data_path = os.getcwd().split("PyERT-BLACK")[0] + 'PyERT-BLACK/test/test_data/sample-gps'
test_data_path = './test_data'
#print(test_data_path)

@pytest.mark.parametrize(
    'test_trip_seg_path, test_network_g_path', 
    [((test_data_path+'/test_rs_trip_seg/test_rs_trip_seg.shp'),
     (test_data_path+'/test_rs_network_g.osm'))]
)
def test_map_point(test_trip_seg_path, test_network_g_path):
    #print(test_trip_seg_path)
    #print(test_network_g_path)
    test_trip_seg = gpd.read_file(test_trip_seg_path)
    netowrk_g = ox.graph_from_xml(filepath=test_network_g_path, 
                                    bidirectional=False, simplify=False, retain_all=True)
    netowrk_g = ox.projection.project_graph(netowrk_g)
    network_n, network_e = ox.graph_to_gdfs(netowrk_g)

    matched_trip_seg = rs.map_point_to_network(test_trip_seg,netowrk_g, network_e)
    for i in range(matched_trip_seg.shape[0]):
        if (i == 0) or (89 <= i < matched_trip_seg.shape[0]):
            assert matched_trip_seg.iloc[i]['nearEdgeName'] == 'Pearl Drive'
        elif (1 <= i <= 6):
            assert matched_trip_seg.iloc[i]['nearEdgeName'] == 'Sherwood Street'
        elif (8 <= i <= 35):
            assert matched_trip_seg.iloc[i]['nearEdgeName'] == 'Astral Drive'
        elif (37 <= i <= 55):
            assert matched_trip_seg.iloc[i]['nearEdgeName'] == 'Brookfield Avenue'
        elif (57 <= i <= 81):
            assert matched_trip_seg.iloc[i]['nearEdgeName'] == 'Caldwell Road'
        elif (83 <= i <= 87):
            assert matched_trip_seg.iloc[i]['nearEdgeName'] == 'Atholea Drive'
        elif(i == 7):
            assert ((matched_trip_seg.iloc[i]['nearEdgeName'] == 'Sherwood Street') or
                    (matched_trip_seg.iloc[i]['nearEdgeName'] == 'Astral Drive'))
        elif(i == 36):
            assert ((matched_trip_seg.iloc[i]['nearEdgeName'] == 'Astral Drive') or
                    (matched_trip_seg.iloc[i]['nearEdgeName'] == 'Brookfield Avenue'))
        elif(i == 56):
            assert ((matched_trip_seg.iloc[i]['nearEdgeName'] == 'Brookfield Avenue') or
                    (matched_trip_seg.iloc[i]['nearEdgeName'] == 'Caldwell Road'))
        elif(i == 82):
            assert ((matched_trip_seg.iloc[i]['nearEdgeName'] == 'Caldwell Road') or
                    (matched_trip_seg.iloc[i]['nearEdgeName'] == 'Atholea Drive'))
        elif(i == 88):
            assert ((matched_trip_seg.iloc[i]['nearEdgeName'] == 'Atholea Drive') or
                    (matched_trip_seg.iloc[i]['nearEdgeName'] == 'Pearl Drive'))

@pytest.mark.parametrize(
    'test_trip_seg_path, test_network_g_path', 
    [((test_data_path+'/test_rs_trip_seg/test_rs_trip_seg.shp'),
     (test_data_path+'/test_rs_network_g.osm'))]
)
def test_detect_and_fill_gap(test_trip_seg_path, test_network_g_path):
    print(test_trip_seg_path)
    print(test_network_g_path)
    test_trip_seg = gpd.read_file(test_trip_seg_path)
    netowrk_g = ox.graph_from_xml(filepath=test_network_g_path, 
                                    bidirectional=False, simplify=False, retain_all=True)
    netowrk_g = ox.projection.project_graph(netowrk_g)
    network_n, network_e = ox.graph_to_gdfs(netowrk_g)

    matched_trip_seg = rs.map_point_to_network(test_trip_seg,netowrk_g, network_e)
    matched_trip_seg = matched_trip_seg.set_crs(epsg=network_e.crs.to_epsg())
    filled_gap_trip_seg, trip_seg_gaps = rs.detect_and_fill_gap(matched_trip_seg, netowrk_g, network_n, network_e)

    orig_points_rec_id = list(trip_seg_gaps['OrigPointRecordID'])

    assert ('15325215' in orig_points_rec_id)
    assert (('15325225' in orig_points_rec_id) or ('15325226' in orig_points_rec_id))
    assert (('15325264' in orig_points_rec_id) or ('15325265' in orig_points_rec_id))
    assert (('15325284' in orig_points_rec_id) or ('15325289' in orig_points_rec_id))
    assert (('15325314' in orig_points_rec_id) or ('15325315' in orig_points_rec_id))
    assert (('15325320' in orig_points_rec_id) or ('15325321' in orig_points_rec_id))