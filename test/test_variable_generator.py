import pytest
import geopandas as gpd
import osmnx as ox
from src import variable_generator as vg
from src import route_solver as rs

test_data_path = './test_data'

@pytest.mark.parametrize(
    'test_trip_seg_path, test_network_g_path', 
    [((test_data_path+'/test_rs_trip_seg/test_rs_trip_seg.shp'),
     (test_data_path+'/test_rs_network_g.osm'))]
)
def test_var_gen(test_trip_seg_path, test_network_g_path):

    # Generate a route for testing
    test_trip_seg = gpd.read_file(test_trip_seg_path)
    network_g = ox.graph_from_xml(filepath=test_network_g_path, bidirectional=False, simplify=False, retain_all=True)
    network_g = ox.projection.project_graph(network_g)
    network_n, network_e = ox.graph_to_gdfs(network_g)
    trip_route = rs.route_choice_gen(test_trip_seg,network_g, network_e, network_n)
    trip_route = trip_route.set_crs(epsg=network_e.crs.to_epsg())

    # Test the variable generator function
    test_rca = vg.var_gen(trip_route,network_e)

    # Test if the distance is within the range
    assert test_rca.iloc[0]['distanceMeter'] > 0
    assert test_rca.iloc[0]['distanceMeter'] < 1

    # Test if the number of left turns is correct
    assert test_rca.iloc[0]['numOfLturns'] == 0

    # Test if the number of right turns is correct
    assert test_rca.iloc[0]['numOfRturns'] == 0

    # Test if the number of roads is correct
    assert test_rca.iloc[0]['numOfRoads'] == 1

    # Test if the street name is correct
    assert test_rca.iloc[0]['streetLongestLeg'] == 'Atholea Drive'

    # Test if the length of the longest leg is within the range
    assert test_rca.iloc[0]['lengthLongestLeg'] > 0
    assert test_rca.iloc[0]['lengthLongestLeg'] < 1