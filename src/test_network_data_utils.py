import pytest
import geopandas as gpd
import osmnx as ox
import os

import network_data_utils as net_utils
#import src.Exceptions as Exceptions
#import network_data_utils as net_utils

test_data_path = os.getcwd().split("PyERT-BLACK")[0] + 'PyERT-BLACK/test/test_data'

@pytest.mark.parametrize(
    'test_trip_seg_path, correct_bounds', 
    [((test_data_path+'/test_network_utils_trip_seg_1/test_network_utils_trip_seg_1.shp'),
      [43.346958, 43.339123, -79.787413, -79.796938])]
)
def test_get_points_boundary(test_trip_seg_path,correct_bounds):
    test_trip_seg = gpd.read_file(test_trip_seg_path)
    output_bounds = net_utils.get_points_boundary(test_trip_seg)
    # Test if the predetermined bounds values are returned by 
    # get_points_boundary
    assert (output_bounds[0] == round(correct_bounds[0]+0.005, 6))
    assert (output_bounds[1] == round(correct_bounds[1]-0.005, 6))
    assert (output_bounds[2] == round(correct_bounds[2]+0.005, 6))
    assert (output_bounds[3] == round(correct_bounds[3]-0.005, 6))

@pytest.mark.parametrize(
    'test_pbf_path, test_mode, test_bounding_box', 
    [((test_data_path+'/test_network_utils.osm.pbf'),
      ('run'), [-79.81, 43.34, -79.79, 43.37]),
     ((test_data_path+'/test_network_utils.osm.pbf'),
      ('drive'), [-79.81, 43.34, -79.79, 43.37]),
     ((test_data_path+'/test_network_utils.osm.pbf'),
      ('walk'), [-79.81, 43.34, -79.79, 43.37]),
     ((test_data_path+'/test_network_utils.osm.pbf'),
      ('all'), [-79.81, 43.34, -79.79, 43.37])]
)
def test_extract_networkdata_pbf(test_pbf_path, test_mode, test_bounding_box):
    if test_mode not in ['drive', 'walk', 'all']:
        graph, nodes, edges, pbf_boundary = net_utils.extract_networkdata_pbf(test_pbf_path, 
                                                                              test_mode,
                                                                              test_bounding_box)
        # When input test_mode = run, extract_networkdata_pbf should return None
        assert graph == None
        assert nodes == None
        assert edges == None
        assert pbf_boundary == None
    else:
        graph, nodes, edges, pbf_boundary = net_utils.extract_networkdata_pbf(test_pbf_path, 
                                                                              test_mode,
                                                                              test_bounding_box)
        
        # Test if the indicies for edges and nodes are set as required
        assert edges.index.names == ['u', 'v', 'key']
        assert nodes.index.names == ['osmid']
        # Test if the graph, nodes and edges are all project to a projected CRS
        assert ox.projection.is_projected(graph.graph['crs'])
        assert ox.projection.is_projected(edges.crs)
        assert ox.projection.is_projected(nodes.crs)

        # Transfer the edges and nodes to universal geographic CRS 
        # (i.e. logitudes and latitudes)
        edges_geo = edges.to_crs(epsg=4326)
        nodes_geo = nodes.to_crs(epsg=4326)
        # Check if the edges' and nodes' longitude and latitude bounds
        # are within the sample input test_bounding_box
        assert edges_geo.total_bounds[0] >= test_bounding_box[0]
        assert edges_geo.total_bounds[1] >= test_bounding_box[1]
        assert edges_geo.total_bounds[2] <= test_bounding_box[2]
        assert edges_geo.total_bounds[3] <= test_bounding_box[3]

        assert nodes_geo.total_bounds[0] >= test_bounding_box[0]
        assert nodes_geo.total_bounds[1] >= test_bounding_box[1]
        assert nodes_geo.total_bounds[2] <= test_bounding_box[2]
        assert nodes_geo.total_bounds[3] <= test_bounding_box[3]
    
    return

@pytest.mark.parametrize(
    'test_mode, test_bounding_box', 
    [(('run'), [-79.81, 43.34, -79.79, 43.37]),
     (('drive'), [-79.81, 43.34, -79.79, 43.37]),
     (('walk'), [-79.81, 43.34, -79.79, 43.37]),
     (('all'), [-79.81, 43.34, -79.79, 43.37])]
)
def test_extract_networkdata_bbox(test_mode, test_bounding_box):
    if test_mode not in ['drive', 'walk', 'all']:
        graph, nodes, edges = net_utils.extract_networkdata_bbox(test_bounding_box[3],
                                                                 test_bounding_box[1], 
                                                                 test_bounding_box[2],
                                                                 test_bounding_box[0],test_mode)
        # When input test_mode = run, extract_networkdata_pbf should return None
        assert graph == None
        assert nodes == None
        assert edges == None

    else:
        graph, nodes, edges = net_utils.extract_networkdata_bbox(test_bounding_box[3],
                                                                 test_bounding_box[1], 
                                                                 test_bounding_box[2],
                                                                 test_bounding_box[0],test_mode)
        
        # Test if the graph, nodes and edges are all project to a projected CRS
        assert ox.projection.is_projected(graph.graph['crs'])
        assert ox.projection.is_projected(edges.crs)
        assert ox.projection.is_projected(edges.crs)

        # Transfer the edges and nodes to universal geographic CRS 
        # (i.e. logitudes and latitudes)
        edges_geo = edges.to_crs(epsg=4326)
        nodes_geo = nodes.to_crs(epsg=4326)
        # Check if the edges' and nodes' longitude and latitude bounds
        # are within the sample input test_bounding_box
        assert edges_geo.total_bounds[0] >= test_bounding_box[0]
        assert edges_geo.total_bounds[1] >= test_bounding_box[1]
        assert edges_geo.total_bounds[2] <= test_bounding_box[2]
        assert edges_geo.total_bounds[3] <= test_bounding_box[3]

        assert nodes_geo.total_bounds[0] >= test_bounding_box[0]
        assert nodes_geo.total_bounds[1] >= test_bounding_box[1]
        assert nodes_geo.total_bounds[2] <= test_bounding_box[2]
        assert nodes_geo.total_bounds[3] <= test_bounding_box[3]
    
    return

@pytest.mark.parametrize(
    'test_pbf_path, test_bounding_box', 
    [((test_data_path+'/test_network_utils.osm.pbf'),
      [-79.81, 43.34, -79.79, 43.37])]
)
def test_extract_ludata_pbf(test_pbf_path, test_bounding_box):
    lu_gdf = net_utils.extract_ludata_pbf(test_pbf_path, test_bounding_box)
    # Test if the index for lu_gdf is set as required
    assert lu_gdf.index.names == ['osm_type', 'id']
    # Check if the longitude and latitude bounds of lu_gdf
    # is within the sample input test_bounding_box
    assert lu_gdf.total_bounds[0] >= test_bounding_box[0]
    assert lu_gdf.total_bounds[1] >= test_bounding_box[1]
    assert lu_gdf.total_bounds[2] <= test_bounding_box[2]
    assert lu_gdf.total_bounds[3] <= test_bounding_box[3]
    
    return

@pytest.mark.parametrize(
    'test_pbf_path, test_bounding_box', 
    [((test_data_path+'/test_network_utils.osm.pbf'),
      [-79.81, 43.34, -79.79, 43.37])]
)
def test_extract_paldata_pbf(test_pbf_path, test_bounding_box):
    pal_gdf = net_utils.extract_paldata_pbf(test_pbf_path, test_bounding_box)
    # Test if the index for lu_gdf is set as required
    assert pal_gdf.index.names == ['osm_type', 'id']
    # Check if the longitude and latitude bounds of pal_gdf
    # is within the sample input test_bounding_box
    assert pal_gdf.total_bounds[0] >= test_bounding_box[0]
    assert pal_gdf.total_bounds[1] >= test_bounding_box[1]
    assert pal_gdf.total_bounds[2] <= test_bounding_box[2]
    assert pal_gdf.total_bounds[3] <= test_bounding_box[3]
    
    return


@pytest.mark.parametrize(
    'test_bounding_box', 
    [([-79.81, 43.34, -79.79, 43.37])]
)
def test_extract_ludata_bbox(test_bounding_box):
    lu_gdf = net_utils.extract_ludata_bbox(test_bounding_box[3],
                                           test_bounding_box[1], 
                                           test_bounding_box[2],
                                           test_bounding_box[0])
    # Check if the longitude and latitude bounds of lu_gdf
    # is within the sample input test_bounding_box
    assert lu_gdf.total_bounds[0] >= test_bounding_box[0]-0.05
    assert lu_gdf.total_bounds[1] >= test_bounding_box[1]-0.05
    assert lu_gdf.total_bounds[2] <= test_bounding_box[2]+0.05
    assert lu_gdf.total_bounds[3] <= test_bounding_box[3]+0.05
    return

@pytest.mark.parametrize(
    'test_bounding_box', 
    [([-79.81, 43.34, -79.79, 43.37])]
)
def test_extract_paldata_bbox(test_bounding_box):
    pal_gdf = net_utils.extract_paldata_bbox(test_bounding_box[3],
                                             test_bounding_box[1], 
                                             test_bounding_box[2],
                                             test_bounding_box[0])
    # Check if the longitude and latitude bounds of pal_gdf
    # is within the sample input test_bounding_box
    assert pal_gdf.total_bounds[0] >= test_bounding_box[0]-0.05
    assert pal_gdf.total_bounds[1] >= test_bounding_box[1]-0.05
    assert pal_gdf.total_bounds[2] <= test_bounding_box[2]+0.05
    assert pal_gdf.total_bounds[3] <= test_bounding_box[3]+0.05
    return

@pytest.mark.parametrize(
    'test_trip_seg_path, correct_mode', 
    [((test_data_path+'/test_network_utils_trip_seg_1/test_network_utils_trip_seg_1.shp'),
      'all'),
     ((test_data_path+'/test_network_utils_trip_seg_2/test_network_utils_trip_seg_2.shp'),
      'drive')]
)
def test_get_trip_mode(test_trip_seg_path, correct_mode):
    test_trip_seg = gpd.read_file(test_trip_seg_path)
    output_mode = net_utils.get_trip_mode(test_trip_seg)
    # Test if the trip mode output for the sample trip segments 
    # match the predetermined modes
    assert output_mode == correct_mode
    return
