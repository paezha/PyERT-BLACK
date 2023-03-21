"""
Module Name: PyERT-BLACK Main Module
Source Name: main.py
Creator: All PyERT-BLACK project team members
Requirements: Python 3.8 or later
Date Created: Feb 15, 2023
Last Revised: Mar 20, 2023
Description: Main module of PyERT-BLACK that contains the main function

Version History:
2023-02-15 (main.py) Create get_points_boundary, extract_networkdata_pbf, extract_networkdata_bbox 
    extract_ludata_pbf, extract_paldata_pbf, extract_ludata_bbox, extract_paldata_bbox, get_trip_mode 
    and main functions

2023-03-17 (main.py) Move get_points_boundary, extract_networkdata_pbf, extract_networkdata_bbox 
    extract_ludata_pbf, extract_paldata_pbf, extract_ludata_bbox, extract_paldata_bbox, 
    and get_trip_mode to a separate module Network Data Utilities

2023-03-17 (main.py) Update code for adding activity locations' information due to changes made in
    Activity Locations Identification moule

2023-03-18 (main.py) Update code for visualizing routes generated and activity locations' information 
    to let the program print excepion message and keep progressing when visualization failed instead of 
    crashing

2023-03-19 (main.py) Update code for extracting network, potential activity locations and landuse data 
    from OSM PBF file due to changes made in Network Data Utilities module
"""

import pandas as pd
import geojsonio as gjsio
import os
from pyrosm import OSM
import osmnx as ox
from datetime import datetime


import GPSPreprocess as gps_preprocess
import geopandas as gpd
import ModeDetection as mode_detect
import Extractor
import route_solver as rs
import variable_generator
import activity_locations_identification as al_identifier
from network_data_utils import get_points_boundary, extract_networkdata_pbf, extract_networkdata_bbox, \
    extract_ludata_pbf, extract_paldata_pbf, extract_ludata_bbox, extract_paldata_bbox, get_trip_mode
from Exceptions import InvalidInputException, InvalidFilePathException, InvalidFileFormatException, \
    InvalidDataException, InvalidGPSDataException, OutofBoundException, NetworkBoundError
import webbrowser

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
    
    aloc_pal_info_radius = input("Enter the radius in meters that activity location information "
                                 + "will be collected from(optional, default 100 meters): ")
    try:
        if aloc_pal_info_radius == '' or aloc_pal_info_radius == None:
            aloc_pal_info_radius = 100
        else:
            aloc_pal_info_radius = float(aloc_pal_info_radius)
    except ValueError:
        print("Invalid input for radius, please enter a real number.\n")
        return None
    
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
    aloc_bound = get_points_boundary(aloc_gdf)
    if (network_pbf_path == '') or (network_pbf_path is None):
        print('Extracting transportation network data...')
        network_g, network_n, network_e = extract_networkdata_bbox(trip_bound[0], trip_bound[1],
                                                                   trip_bound[2], trip_bound[3],
                                                                   trip_mode)
        #if (network_g == None):
        #    return
        print('Extracting landuse data...')
        landuse_info = extract_ludata_bbox(aloc_bound[0], aloc_bound[1],
                                           aloc_bound[2], aloc_bound[3])
        print('Extracting potential activity locations data...')
        pal_info = extract_paldata_bbox(aloc_bound[0], aloc_bound[1],
                                        aloc_bound[2], aloc_bound[3])
    else:
        print('Extracting transportation network data...')
        network_g, network_n, network_e, network_bound = extract_networkdata_pbf(
            network_pbf_path, trip_mode, bbox=[trip_bound[3], trip_bound[1], 
                                               trip_bound[2], trip_bound[0]])
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
        landuse_info = extract_ludata_pbf(
            network_pbf_path,bbox=[aloc_bound[3], aloc_bound[1], 
                                   aloc_bound[2], aloc_bound[0]])
        print('Extracting potential activity locations data...')
        pal_info = extract_paldata_pbf(
            network_pbf_path,bbox=[aloc_bound[3], aloc_bound[1], 
                                   aloc_bound[2], aloc_bound[0]])
    
    if len(trip_gdf) >= 2 and (network_g != None):
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
        try:
            viz_json = gjsio.make_url(
                routes_gdf[['SerialID', 'geometry']].to_json())
        except Exception as e:
            print("Unable to generate url to visualize generated routes due to exception: \n" + str(e))

        routes_url = viz_json
        
        try:
            webbrowser.open(routes_url, new=0, autoraise=True)
        except Exception as e:
            print("Unable to visualize generated route due to exception: \n" + str(e))
    else:
        print('No trip segment has been found, hence no route choice can be generated')
    
    if len(aloc_gdf) >= 1:
        print("Adding activity locations' information...")
        network_epsg = network_e.crs.to_epsg()
        aloc_gdf = aloc_gdf.set_crs(epsg=4326)
        #aloc_points_url = gjsio.make_url(
        #    aloc_gdf.to_json())
        #webbrowser.open(aloc_points_url, new=0, autoraise=True)
        aloc_gdf = aloc_gdf.to_crs(epsg=network_epsg)
        landuse_info = landuse_info.to_crs(network_epsg)
        pal_info = pal_info.to_crs(network_epsg)

        aloc_info = al_identifier.create_al_info(aloc_gdf, landuse_info, pal_info, 
                                                 aloc_pal_info_radius)

        aloc_info_geo_crs = aloc_info.to_crs(epsg=4326)
        polygon_pal_info = aloc_info_geo_crs.loc[(aloc_info_geo_crs.geometry.geom_type=='Polygon')]
        polygon_pal_info = polygon_pal_info.reset_index(drop=True)
        point_pal_info = aloc_info_geo_crs.loc[(aloc_info_geo_crs.geometry.geom_type=='Point')]
        point_pal_info = point_pal_info.reset_index(drop=True)
        polygon_pal_to_save = polygon_pal_info.drop(
            columns=['pal_index', 'lu_index'])
        point_pal_to_save = point_pal_info.drop(
            columns=['pal_index', 'lu_index'])
        
        #dropped_geo_gdf = gpd.GeoDataFrame(
        #    dropped_geo_gdf, geometry='building_geometry')
        #dropped_geo_gdf = dropped_geo_gdf.set_crs(epsg=network_epsg)
        #dropped_geo_gdf = dropped_geo_gdf.to_crs(epsg=4326)
        if not polygon_pal_to_save.empty:
            polygon_pal_to_save.to_file(
                filename=output_dir_path + '/activity_locations_polygon_info', driver='ESRI Shapefile')
        if not point_pal_to_save.empty:
            point_pal_to_save.to_file(
                filename=output_dir_path + '/activity_locations_point_info', driver='ESRI Shapefile')
    
        #building_info_df = aloc_info[['SerialID', 'building_geometry']]
        #building_info = gpd.GeoDataFrame(
        #    building_info_df, geometry='building_geometry')
        #building_info = building_info.set_crs(epsg=network_epsg)
        #building_info = building_info.to_crs(epsg=4326)
        aloc_info_geo_crs.drop(columns=['geometry']).to_csv(
            output_dir_path+'/aloc_var.csv')
        
        try:
            viz_aloc_json = gjsio.make_url(
                aloc_info_geo_crs.to_json())
        except Exception as e:
            print("Unable to generate url to visualize generated routes due to exception: \n" + str(e))
        # print(viz_aloc_json)
        aloc_url = viz_aloc_json
        
        try:
            webbrowser.open(aloc_url, new=0, autoraise=True)
        except Exception as e:
            print("Unable to visualize the activity locations' info due to exception: \n" + str(e))
        
    else:
        print("No stop segment has been found, hence no activity locations' information can be added")
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)
    print('Matching Done!')

    return

if __name__ == '__main__':
    main()
