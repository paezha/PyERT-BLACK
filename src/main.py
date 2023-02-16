import pandas as pd
import geojsonio as gjsio
import os
from pyrosm import OSM
import osmnx as ox


import GPSPreprocess as gps_preprocess
import ModeDetection as mode_detect
import Extractor
import route_solver as rs
import variable_generator
import activity_locations_identification as al_identifier
from Exceptions import NetworkModeError

def get_points_boundary(points_gdf):
    maxX, maxY, minX, minY = -180, -180, 180, 180

    for point in points_gdf['geometry']:
        if point.x > maxX:
            maxX = point.x
        if point.x < minX:
            minX = point.x
        if point.y > maxY:
            maxY = point.y
        if point.y < minY:
            minY = point.y

    maxX = maxX + 0.005
    minX = minX - 0.005
    maxY = maxY + 0.005
    minY = minY - 0.005
    return (maxY, minY, maxX, minX)


def extract_networkdata_pbf(pbf_file_path, mode):
    try:
        if mode not in ['driving','walking','all']:
            raise NetworkModeError
        
        osm = OSM(pbf_file_path)
        
    except NetworkModeError:
        print("The input mode for required network data is not one of 'driving','walking' or 'all'")
        return None, None, None
    except ValueError as e:
        print(e)
        return None, None, None
    

    nodes, edges = osm.get_network(nodes=True, network_type=mode)
    
    # Columns for id, longitude and latitude need to be remaned to osmid, x and y respectively
    nodes['osmid'] = nodes['id']
    nodes['x'] = nodes['lon']
    nodes['y'] = nodes['lat']
    # Dropping the original columns for longitude and latitude 
    nodes.drop(columns=['id', 'lon', 'lat'], inplace = True)
    nodes.set_index('osmid', inplace=True)
    pbf_boundary = get_points_boundary(nodes)
    
    # Column 'timestamp' needs to be renamed to 'key'
    edges['key'] = edges['timestamp']
    # Index for Edges need to be set to ['u','v','key'] multi-index
    edges.set_index(['u','v','key'], inplace=True)
    
    graph = ox.graph_from_gdfs(nodes, edges)
    graph_proj = ox.projection.project_graph(graph)
    nodes_proj, edges_proj = ox.graph_to_gdfs(graph_proj)
    return graph_proj, nodes_proj, edges_proj, pbf_boundary

def extract_networkdata_bbox(max_lat, min_lat, max_lon, min_lon, mode):
    try:
        if mode not in ['drive','walk','all']:
            raise NetworkModeError
    except NetworkModeError:
        print("The input mode for required network data is not one of 'drive','walk' or 'all'")
        return None, None, None
    
    graph = ox.graph.graph_from_bbox(max_lat, min_lat, max_lon, min_lon, 
                                     network_type=mode, simplify=False, retain_all=True)
    graph_proj = ox.projection.project_graph(graph)
    nodes_proj, edges_proj = ox.graph_to_gdfs(graph_proj)
    
    return graph_proj, nodes_proj, edges_proj

def extract_ludata_pbf(pbf_file_path):
    try:
        osm = OSM(pbf_file_path)
    except ValueError as e:
        print(e)
        return None
    
    landuse_gdf = osm.get_landuse()
    landuse_gdf.set_index(['osm_type','id'], inplace=True)
    return landuse_gdf

def extract_paldata_pbf(pbf_file_path):
    try:
        osm = OSM(pbf_file_path)
    except ValueError as e:
        print(e)
        return None
    
    buildings = osm.get_buildings()
    filtered_buildings = buildings[((-buildings['addr:housenumber'].isnull()) & 
                                    (-buildings['addr:street'].isnull())) | 
                                   (-buildings['name'].isnull())]
    filtered_buildings.set_index(['osm_type','id'], inplace=True)
    return filtered_buildings

def extract_ludata_bbox(max_lat, min_lat, max_lon, min_lon):
    landuse_gdf = ox.geometries.geometries_from_bbox(max_lat, min_lat, max_lon, min_lon, tags ={ 'landuse':True})
    return landuse_gdf

def extract_paldata_bbox(max_lat, min_lat, max_lon, min_lon):
    pal_gdf = ox.geometries.geometries_from_bbox(max_lat, min_lat, max_lon, min_lon, tags ={ 'building':True})
    filtered_pal = pal_gdf[((-pal_gdf['addr:housenumber'].isnull()) &
                              (-pal_gdf['addr:street'].isnull())) | 
                             (-pal_gdf['name'].isnull())]
    return filtered_pal

def get_trip_mode(trip_data):
    trip_modes = list(trip_data['Modes'].value_counts().index)
    
    if ('Walk' in trip_modes) and ('Drive' not in trip_modes):
        return 'walk'
    elif ('Walk' not in trip_modes) and ('Drive' in trip_modes):
        return 'drive'
    elif ('Walk' in trip_modes) and ('Drive' in trip_modes):
        return 'all'
    else:
        return 'no mode found'

def main():
    gps_data_path = 'C:/University Grade4/4G06/PyERT-BLACK/quarto-example/data/sample-gps/sample-gps-1.csv' #input("Enter file path to GPS data: ")
    # Check if file type and path are valid, raise exception if not
    network_pbf_path = ''#input("Enter file path to OSM network data(optional): ")
    # Check if file type and path are valid (empty input is fine), raise exception if not
    output_dir_path = 'C:/Users/jimta/Undergraduate/4G06_test/main_test' #input("Enter file path to the output folder: ")
    # Check if the path is to a folder, raise exception if not
    
    # Preprocess GPS data
    print('Preprocessing input GPS data...')
    gps_data_df = pd.read_csv(gps_data_path)
    preprocessor = gps_preprocess.GPSPreprocess(gps_data_df)
    gps_data_df = preprocessor.get_data()
    # Check if there is any valid data left, if not, print message to tell the user and return
    
    # Detect modes of GPS data
    print('Detecting modes of GPS data...')
    mode_detector = mode_detect.ModeDetection(gps_data_df)
    eps_data_gdf = mode_detector.get_episode_data()
    print(eps_data_gdf)
    # Extract trip and stop segments
    print('Extracting trip and stop segments...')
    extractor = Extractor.Extractor(eps_data_gdf, gps_data_df)
    trip_gdf = extractor.get_trip_segments()
    aloc_gdf = extractor.get_activity_locations()
    print(trip_gdf.head(100))
    print(aloc_gdf.head(100))
    trip_mode = get_trip_mode(trip_gdf)
    trip_bound = get_points_boundary(trip_gdf)
    
    
    if (network_pbf_path == '') or (network_pbf_path == None):
        network_G, network_N, network_E = extract_networkdata_bbox(trip_bound[0], trip_bound[1],
                                                                   trip_bound[2], trip_bound[3],
                                                                   trip_mode)
        landuse_info = extract_ludata_bbox(trip_bound[0], trip_bound[1],
                                           trip_bound[2], trip_bound[3])
        pal_info = extract_paldata_bbox(trip_bound[0], trip_bound[1],
                                        trip_bound[2], trip_bound[3])
    else:
        network_G, network_N, network_E, network_bound = extract_networkdata_pbf(network_pbf_path, trip_mode)
        # Check if the trip segment is out of the boundary of the extracted network
        if ((network_bound[0] < trip_bound[0]) or
            (network_bound[1] > trip_bound[1]) or
            (network_bound[2] < trip_bound[2]) or
            (network_bound[3] > trip_bound[3])):
            # raise exception OutOfBound
            return
        
        landuse_info = extract_ludata_pbf(network_pbf_path)
        pal_info = extract_paldata_pbf(network_pbf_path)
    
    if len(trip_gdf) >= 2:
        print('Generating route choices for trip segments...')
        routes_gdf = rs.route_choice_gen(trip_gdf, network_G, network_E, network_N)
        routes_gdf = routes_gdf.set_crs(epsg = 4326)
        print(routes_gdf)
        rca_var_gdf = variable_generator.var_gen(routes_gdf)
        print(rca_var_gdf)
        # Generating shp file and csv files into output folder
        routes_gdf.to_file(filename=output_dir_path+'/route_choice', driver = 'ESRI Shapefile')
        rca_var_gdf.drop(columns=['geometry']).to_csv(filename=output_dir_path+'/rca_var.csv')
        viz_json = gjsio.make_url(routes_gdf[['SerialID','geometry']].to_json())
        print('Routes for trip segments generated, visualize the route by clicking HERE')
        print(viz_json)
    else:
        print('No trip segment has been found, hence no route choice can be generated')
    
    if len(aloc_gdf) >= 1:
        print("Adding activity locations' information...")
        aloc_lu_gdf = al_identifier.identify_lu(aloc_gdf,landuse_info)
        aloc_pal_gdf = al_identifier.identify_PAL(aloc_gdf,pal_info)
        aloc_info = al_identifier.create_al_info(aloc_lu_gdf, aloc_pal_gdf)
        print(aloc_info)
        aloc_info.to_file(filename=output_dir_path+'/activity_locations', driver = 'ESRI Shapefile')
    else:
        print("No stop segment has been found, hence no activity locations' information can be added")
    
    print('Matching Done!')
    return