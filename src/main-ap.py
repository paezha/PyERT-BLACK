import pandas as pd
import geojsonio as gjsio
import os
from pyrosm import OSM
import osmnx as ox
from datetime import datetime


import src.GPSPreprocess as gps_preprocess
import geopandas as gpd
import src.ModeDetection as mode_detect
import src.Extractor
import src.route_solver as rs
import src.variable_generator
import src.activity_locations_identification as al_identifier
from src.Exceptions import InvalidInputException, InvalidFilePathException, InvalidFileFormatException, \
    InvalidDataException, InvalidGPSDataException, NetworkModeError, OutofBoundException, NetworkBoundError
import webbrowser


def get_points_boundary(points_gdf):
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

    max_x = max_x + 0.005
    min_x = min_x - 0.005
    max_y = max_y + 0.005
    min_y = min_y - 0.005
    return (max_y, min_y, max_x, min_x)


def extract_networkdata_pbf(pbf_file_path, mode):
    try:
        if mode not in ['driving', 'walking', 'all']:
            raise NetworkModeError

        osm = OSM(pbf_file_path)

    except NetworkModeError:
        print("The input mode for required network data is not one of 'driving','walking' or 'all'")
        return None, None, None, None
    except ValueError as error:
        print(error)
        return None, None, None, None

    nodes, edges = osm.get_network(nodes=True, network_type=mode)

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


def extract_ludata_pbf(pbf_file_path):
    try:
        osm = OSM(pbf_file_path)
    except ValueError as error:
        print(error)
        return None

    landuse_gdf = osm.get_landuse()
    landuse_gdf.set_index(['osm_type', 'id'], inplace=True)
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
    filtered_buildings.set_index(['osm_type', 'id'], inplace=True)
    return filtered_buildings


def extract_ludata_bbox(max_lat, min_lat, max_lon, min_lon):
    landuse_gdf = ox.geometries.geometries_from_bbox(
        max_lat, min_lat, max_lon, min_lon, tags={'landuse': True})
    return landuse_gdf


def extract_paldata_bbox(max_lat, min_lat, max_lon, min_lon):
    pal_gdf = ox.geometries.geometries_from_bbox(
        max_lat, min_lat, max_lon, min_lon, tags={'building': True})
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
    gps_data_path = input("Enter file path to GPS data: ")
    # gps_data_path = '/Users/jasperleung/Documents/GitHub/PyERT-BLACK/quarto-example/data/sample-gps/sample-gps-1.csv'
    # Check if file type and path are valid, raise exception if not
    try:
        if '.' in gps_data_path[-4:] and '.csv' != gps_data_path[-4:]:
            raise InvalidFileFormatException()
    except InvalidFileFormatException:
        print(gps_data_path + ': File format is not .csv\n')
        return None

    try:
        if not os.path.isfile(gps_data_path):
            raise InvalidFilePathException()
    except InvalidFilePathException:
        print(gps_data_path + ': GPS data path does not exist\n')
        return None
    network_pbf_path = input("Enter file path to OSM network data(optional): ")
    # network_pbf_path = ''
    # Check if file type and path are valid (empty input is fine), raise exception if not
    if network_pbf_path:
        try:
            if '.' in network_pbf_path[-4:] and '.pbf' != network_pbf_path[-4:]:
                raise InvalidFileFormatException()
        except InvalidFileFormatException:
            print(network_pbf_path + ': File is not .pbf\n')
            return None
        try:
            if not os.path.isfile(network_pbf_path):
                raise InvalidFilePathException()
        except InvalidFilePathException:
            print(network_pbf_path + ": Network pbf path does not exist\n")
            return None

    output_dir_path = input("Enter file path to the output folder: ")
    # output_dir_path = '/Users/jasperleung/Documents'
    # Check if the path is to a folder, raise exception if not
    try:
        if not os.path.isdir(output_dir_path.rsplit('/', 1)[0]):
            raise InvalidInputException()
    except InvalidInputException:
        print(output_dir_path.rsplit('/', 1)[0] + ": is not a folder\n")
        return None

    num_points_str = input(
        "(Optional) Enter the number of points from the dataset to process. ")
    if num_points_str.isdigit():
        num_points = int(num_points_str)
        if num_points < 100:
            print("num_points too low. set to 100.")
            num_points = 100
    else:
        num_points = None

    # Preprocess GPS data
    print('Preprocessing input GPS data...')
    gps_data_df = pd.read_csv(gps_data_path)
    # Check if there is any valid data missing
    try:
        cols = ['RecordID', 'SerialID', 'LocalTime', 'latitude',
                'longitude', 'Fix_Status', 'DOP', 'Speed_kmh', 'Limit_kmh']
        if not gps_data_df.columns.isin(cols).all():
            raise InvalidDataException()
    except InvalidDataException:
        print('Data does not have correct columns\nData needs to have the following columns: ' + cols + '\n')
        return None
    preprocessor = gps_preprocess.GPSPreprocess(gps_data_df)
    gps_data_df = preprocessor.get_data()
    # Check if geometry column is missing
    try:
        if 'geometry' not in gps_data_df:
            raise InvalidGPSDataException()
    except InvalidGPSDataException:
        print('GPS Data does not have a geometry column\n')
        return None
    # Detect modes of GPS data
    print('Detecting modes of GPS data...')
    mode_detector = mode_detect.ModeDetection(gps_data_df)
    eps_data_gdf = mode_detector.get_episode_data()
    # print(eps_data_gdf)
    # Extract trip and stop segments
    print('Extracting trip and stop segments...')
    extractor = Extractor.Extractor(eps_data_gdf, gps_data_df)
    trip_gdf = extractor.get_trip_segments()
    if num_points is None:
        trip_gdf = trip_gdf.set_crs(epsg=4326)
    else:
        trip_gdf = trip_gdf.loc[:num_points].set_crs(epsg=4326)

    aloc_gdf = extractor.get_activity_locations()

    # print(trip_gdf.head(100))
    # print(aloc_gdf.head(100))
    trip_mode = get_trip_mode(trip_gdf)
    trip_bound = get_points_boundary(trip_gdf)
    if (network_pbf_path == '') or (network_pbf_path is None):
        print('Extracting transportation network data...')
        network_g, network_n, network_e = extract_networkdata_bbox(trip_bound[0], trip_bound[1],
                                                                   trip_bound[2], trip_bound[3],
                                                                   trip_mode)
        print('Extracting landuse data...')
        landuse_info = extract_ludata_bbox(trip_bound[0], trip_bound[1],
                                           trip_bound[2], trip_bound[3])
        print('Extracting potential activity locations data...')
        pal_info = extract_paldata_bbox(trip_bound[0], trip_bound[1],
                                        trip_bound[2], trip_bound[3])
    else:
        print('Extracting transportation network data...')
        network_g, network_n, network_e, network_bound = extract_networkdata_pbf(
            network_pbf_path, trip_mode)
        try:
            if network_bound is not None:
                # Check if the trip segment is out of the boundary of the extracted network
                try:
                    if (network_bound[0] < trip_bound[0]) or \
                            (network_bound[1] > trip_bound[1]) or \
                            (network_bound[2] < trip_bound[2]) or \
                            (network_bound[3] > trip_bound[3]):
                        raise OutofBoundException()
                except OutofBoundException:
                    print(
                        "Trip Segment is out of the boundary of the extracted network\n")
                    return None
            else:
                raise NetworkBoundError()
        except NetworkBoundError:
            print("Network bound is None\n")
            return None
        print('Extracting landuse data...')
        landuse_info = extract_ludata_pbf(network_pbf_path)
        print('Extracting potential activity locations data...')
        pal_info = extract_paldata_pbf(network_pbf_path)
    if len(trip_gdf) >= 2:
        print('Generating route choices for trip segments...')
        routes_gdf = rs.route_choice_gen(
            trip_gdf, network_g, network_e, network_n)
        routes_gdf = routes_gdf.set_crs(epsg=4326)
        # print(routes_gdf)
        rca_var_gdf = variable_generator.var_gen(routes_gdf, network_e)
        # print(rca_var_gdf)
        # Generating shp file and csv files into output folder
        routes_gdf[['SerialID', 'geometry']].to_file(filename=output_dir_path +
                                                     '/route_choice', driver='ESRI Shapefile')
        # routes_gdf[['SerialID', 'geometry']].to_file(filename='route_choice.shp')
        rca_var_gdf.drop(columns=['geometry']).to_csv(
            output_dir_path+'/rca_var.csv')
        viz_json = gjsio.make_url(
            routes_gdf[['SerialID', 'geometry']].to_json())
        # print('Routes for trip segments generated, visualize the route by clicking HERE')
        # print(viz_json)
        routes_url = viz_json
        webbrowser.open(routes_url, new=0, autoraise=True)
    else:
        print('No trip segment has been found, hence no route choice can be generated')
    if len(aloc_gdf) >= 1:
        print("Adding activity locations' information...")
        network_epsg = network_e.crs.to_epsg()
        aloc_gdf = aloc_gdf.set_crs(epsg=4326)
        aloc_gdf = aloc_gdf.to_crs(epsg=network_epsg)
        landuse_info = landuse_info.to_crs(network_epsg)
        pal_info = pal_info.to_crs(network_epsg)
        aloc_lu_gdf = al_identifier.identify_lu(aloc_gdf, landuse_info)
        aloc_pal_gdf = al_identifier.identify_pal(aloc_gdf, pal_info)
        aloc_info = al_identifier.create_al_info(aloc_lu_gdf, aloc_pal_gdf)

        dropped_geo_gdf = aloc_info.drop(
            columns=['geometry', 'building_index', 'lu_index'])
        dropped_geo_gdf = gpd.GeoDataFrame(
            dropped_geo_gdf, geometry='building_geometry')
        dropped_geo_gdf = dropped_geo_gdf.set_crs(epsg=network_epsg)
        dropped_geo_gdf = dropped_geo_gdf.to_crs(epsg=4326)
        dropped_geo_gdf.to_file(
            filename=output_dir_path + '/activity_locations_info', driver='ESRI Shapefile')

        building_info_df = aloc_info[['SerialID', 'building_geometry']]
        building_info = gpd.GeoDataFrame(
            building_info_df, geometry='building_geometry')
        building_info = building_info.set_crs(epsg=network_epsg)
        building_info = building_info.to_crs(epsg=4326)
        aloc_info.drop(columns=['geometry']).to_csv(
            output_dir_path+'/aloc_var.csv')
        viz_aloc_json = gjsio.make_url(
            building_info.to_json())
        # print(viz_aloc_json)
        aloc_url = viz_aloc_json
        webbrowser.open(aloc_url, new=0, autoraise=True)
    else:
        print("No stop segment has been found, hence no activity locations' information can be added")
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)
    print('Matching Done!')

    return


main()