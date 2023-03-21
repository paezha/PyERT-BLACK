"""
Module Name: Network Data Utilities
Source Name: network_data_utils.py
Creator: Hongzhao Tan (tanh10@mcmaster.ca)
Requirements: Python 3.8 or later
Date Created: Mar 17, 2023
Last Revised: Mar 20, 2023
Description: Appends LU and PAL for Activity Locations extracted by the Extractor module,
             if such information has been provided

Version History:
2023-03-17 (network_data_utils.py) Create Network Data Utilities module and move 
    get_points_boundary, extract_networkdata_pbf, extract_networkdata_bbox extract_ludata_pbf, 
    extract_paldata_pbf, extract_ludata_bbox, extract_paldata_bbox, and get_trip_mode from 
    Main module to the Network Data Utilities module

2023-03-18 (network_data_utils.py) Updated extract_paldata_pbf and extract_paldata_bbox functions 
    to make them not filter out the rows in the dataframe for buildings' information with neither 
    address nor name and also extract amenities information

2023-03-19 (network_data_utils.py) Updated extract_networkdata_pbf, extract_ludata_pbf, and extract_paldata_pbf 
    functions with new optional input 'bbox' to make them be able to extract data from OSM PBF file 
    only within the input bounding box

2023-03-20 (network_data_utils.py) Updated extract_paldata_pbf function to remove rows in pal_info dataframe
    that are with duplicated indicies.
"""

import osmnx as ox
from pyrosm import OSM
import pandas as pd

from Exceptions import NetworkModeError


def get_points_boundary(points_gdf):
    """
    Returns the max and min x(longitude) and y(latitude) values
    within a Geodataframe that contains GPS points with longitude 
    and latitude values

    Parameters:
    points_gdf = GeoDataFrame that contains GPS points with longitude 
        and latitude values
    """
    max_x, max_y, min_x, min_y = -180, -180, 180, 180

    for point in points_gdf['geometry']:
        if point.x > max_x:
            max_x = point.x
        if point.x < min_x:
            min_x = point.x
        if point.y > max_y:
            max_y = point.y
        if point.y < min_y:
            min_y = point.y

    # Extend 0.005 degree out to make sure all network data 
    # needed can be extracted later in other function
    max_x = max_x + 0.005
    min_x = min_x - 0.005
    max_y = max_y + 0.005
    min_y = min_y - 0.005
    return (max_y, min_y, max_x, min_x)


def extract_networkdata_pbf(pbf_file_path, mode='drive', bbox=None):
    """
    Reuturns a Geodataframe that contains the data of transportation network 
    
    Parameter:
    pbf_file_path = file path of the OSM PBF file that the transportation network 
        data will be extracted from
    mode = Mode of the transportation network data to be extracted
    bbox = bounding box that specifies the max and min longitudes and latitudes
        the network data will be extracted from
    """
    try:
        if mode not in ['drive', 'walk', 'all']:
            raise NetworkModeError
        
        osm = OSM(pbf_file_path,bounding_box=bbox)

    except NetworkModeError:
        print("The input mode for required network data is not" 
              + "one of 'driving','walking' or 'all'")
        return None, None, None, None
    except ValueError as error:
        print(error)
        return None, None, None, None

    if mode == 'drive':
        nodes, edges = osm.get_network(nodes=True, network_type='driving')
    elif mode == 'walk':
        nodes, edges = osm.get_network(nodes=True, network_type='walking')
    elif mode == 'all':
        nodes, edges = osm.get_network(nodes=True, network_type='all')
    else:
        nodes, edges = osm.get_network(nodes=True, network_type='driving')
        
    # Columns for id, longitude and latitude need to be remaned to osmid, x and y respectively
    nodes['osmid'] = nodes['id']
    nodes['x'] = nodes['lon']
    nodes['y'] = nodes['lat']
    # Dropping the original columns for longitude and latitude
    nodes.drop(columns=['id', 'lon', 'lat'], inplace=True)
    nodes.set_index('osmid', inplace=True)
    pbf_boundary = get_points_boundary(nodes)

    # Column 'timestamp' needs to be renamed to 'key'
    edges['key'] = edges['timestamp']
    # Index for Edges need to be set to ['u','v','key'] multi-index
    edges.set_index(['u', 'v', 'key'], inplace=True)

    graph = ox.graph_from_gdfs(nodes, edges)
    graph_proj = ox.projection.project_graph(graph)
    nodes_proj, edges_proj = ox.graph_to_gdfs(graph_proj)
    return graph_proj, nodes_proj, edges_proj, pbf_boundary


def extract_networkdata_bbox(max_lat, min_lat, max_lon, min_lon, mode):
    """
    Reuturns a Geodataframe that contains the data of transportation network extracted
    with OSMnx
    
    Parameter:
    max_lat = Max latitude of the bounding box the data will be extracted within
    min_lat = Min latitude of the bounding box the data will be extracted within
    max_lon = Max longitude of the bounding box the data will be extracted within
    min_lon = Min longitude of the bounding box the data will be extracted within
    mode = Mode of the transportation network data to be extracted
    """
    try:
        if mode not in ['drive', 'walk', 'all']:
            raise NetworkModeError
    except NetworkModeError:
        print(
            "The input mode for required network data is not one of 'drive','walk' or 'all'")
        return None, None, None

    graph = ox.graph.graph_from_bbox(max_lat, min_lat, max_lon, min_lon,
                                     network_type=mode, simplify=False, retain_all=True)
    graph_proj = ox.projection.project_graph(graph)
    nodes_proj, edges_proj = ox.graph_to_gdfs(graph_proj)

    return graph_proj, nodes_proj, edges_proj

# revision 1 change
def extract_ludata_pbf(pbf_file_path, bbox=None):
    """
    
    Reuturns a Geodataframe that contains the data of landuse
    
    Parameter:
    pbf_file_path = file path of the OSM PBF file that the landuse data will
        be extracted from
    bbox = bounding box that specifies the max and min longitudes and latitudes
        the buildings' and amenities' data will be extracted from
    
    """
    try:
        osm = OSM(pbf_file_path, bounding_box=bbox)
    except ValueError as error:
        print(error)
        return None

    landuse_gdf = osm.get_landuse()
    landuse_gdf.set_index(['osm_type', 'id'], inplace=True)
    return landuse_gdf

# revision 1 change
def extract_paldata_pbf(pbf_file_path, bbox=None):
    """
    Reuturns a Geodataframe that contains the data of buildings and amenities
    
    Parameter:
    pbf_file_path = file path of the OSM PBF file that the buildings' and amenities'  
        data will be extracted from
    bbox = bounding box that specifies the max and min longitudes and latitudes
        the buildings' and amenities' data will be extracted from
    """
    try:
        osm = OSM(pbf_file_path, bounding_box=bbox)
    except ValueError as e:
        print(e)
        return None

    buildings = osm.get_buildings()
    amenities = osm.get_pois(custom_filter={'amenity': True})
    
    buildings.set_index(['osm_type', 'id'], inplace=True)
    amenities.set_index(['osm_type', 'id'], inplace=True)

    pal_info = pd.concat([buildings, amenities])
    pal_info = pal_info[~pal_info.index.duplicated(keep='first')]
    pal_info.sort_index(inplace=True)
    #filtered_buildings = buildings[((-buildings['addr:housenumber'].isnull()) &
    #                                (-buildings['addr:street'].isnull())) |
    #                               (-buildings['name'].isnull())]
    #filtered_buildings.set_index(['osm_type', 'id'], inplace=True)

    return pal_info


def extract_ludata_bbox(max_lat, min_lat, max_lon, min_lon):
    """
    Reuturns a Geodataframe that contains the data of landuse extracted
    with OSMnx
    
    Parameter:
    max_lat = Max latitude of the bounding box the data will be extracted within
    min_lat = Min latitude of the bounding box the data will be extracted within
    max_lon = Max longitude of the bounding box the data will be extracted within
    min_lon = Min longitude of the bounding box the data will be extracted within
    """
    landuse_gdf = ox.geometries.geometries_from_bbox(
        max_lat, min_lat, max_lon, min_lon, tags={'landuse': True})
    return landuse_gdf

# revision 1 change
def extract_paldata_bbox(max_lat, min_lat, max_lon, min_lon):
    """
    Reuturns a Geodataframe that contains the data of buildings and amenities 
    extracted with OSMnx
    
    Parameter:
    max_lat = Max latitude of the bounding box the data will be extracted within
    min_lat = Min latitude of the bounding box the data will be extracted within
    max_lon = Max longitude of the bounding box the data will be extracted within
    min_lon = Min longitude of the bounding box the data will be extracted within
    """
    pal_gdf = ox.geometries.geometries_from_bbox(
        max_lat, min_lat, max_lon, min_lon, tags={'building': True, 'amenity': True})
    #filtered_pal = pal_gdf[((-pal_gdf['addr:housenumber'].isnull()) &
    #                        (-pal_gdf['addr:street'].isnull())) |
    #                       (-pal_gdf['name'].isnull())]
    #return filtered_pal
    filtered_pal = pal_gdf.loc[(pal_gdf.geometry.geom_type=='Polygon') |(pal_gdf.geometry.geom_type=='Point')]
    return filtered_pal

def get_trip_mode(trip_data):
    """
    Returns the trip mode of a trip segment

    trip_data = a Geodataframe that contains the data of a trip segment(s)
    """
    trip_modes = list(trip_data['Modes'].value_counts().index)

    if ('Walk' in trip_modes) and ('Drive' not in trip_modes):
        return 'walk'
    elif ('Walk' not in trip_modes) and ('Drive' in trip_modes):
        return 'drive'
    elif ('Walk' in trip_modes) and ('Drive' in trip_modes):
        return 'all'
    else:
        return 'no mode found'