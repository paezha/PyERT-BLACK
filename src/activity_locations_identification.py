"""
Module Name: Activity Locations Identification
Source Name: activity_locations_identification.py
Creator: Hongzhao Tan (tanh10@mcmaster.ca)
Requirements: Python 3.8 or later
Date Created: Feb 12, 2023
Last Revised: Mar 18, 2023
Description: Appends LU and PAL for Activity Locations extracted by the Extractor module,
             if such information has been provided

Version History:
2023-02-12 (activity_locations_identification.py) Create identify_lu, identify_pal and create_al_info functions

2023-02-13 (activity_locations_identification.py) Create comments explaining the logic of each function

2023-02-15 (activity_locations_identification.py) Update format & naming

2023-03-18 (activity_locations_identification.py) Update all functions to find activity locations info from a
    radius around the stop segments instead of finding from the nearest building/amenity
"""
import pandas as pd
import geopandas as gpd

# values for building type for unclassified buildings 
unclassified_values = ['yes','Yes','building','Building','general','mixed','yesq','undefined','unknown']

def identify_lu(al_pal_gdf, lu_gdf):
    """
    Returns a Geodataframe of Activity Locations with appended LU information corresponding to the Activity Locations

    Parameters:
    al_pal_gdf = GeoDataFrame of Activity Locations with PAL information added
    lu_gdf = GeoDataFrame of LU information
    """
    # Initialize lu_classification and lu_index columns
    lu_class_list = []
    lu_index_list = []
    # Iterate through the length of a GeoDataFrame of Potential Activity Locations
    for i in range(len(al_pal_gdf)):
        # Get the geometry of row i for the Potential Activity Locations
        pal_geo = al_pal_gdf.loc[i]['geometry']
        # Get the landuse class of the first row of the LU GeoDataFrame
        closest_lu_class = lu_gdf.iloc[0]['landuse']
        # Get the geometry of the first row of the LU GeoDataFrame
        closest_lu_geo = lu_gdf.iloc[0]['geometry']
        # Get the index of the first row of the LU GeoDataFrame
        closest_lu_index = list(lu_gdf.index)[0]
        # Calculate the closest distance between the geometry of the ith row
        # of the Potential Activity Locations and the geometry of first row of the
        # LU GeoDataFrame
        closest_dist = closest_lu_geo.distance(pal_geo)
        # If the closest distance is smaller than the threshold 1e-8, append the
        # closest LU class and LU index into the arrays lu_classification and lu_index
        # arrays and continue the for loop to the next iteration
        if closest_dist < 1e-8:
            lu_class_list.append(closest_lu_class)
            lu_index_list.append(closest_lu_index)
            continue

        # If the distance was equal or greater than the threshold then iterate
        # through the second row till the length of the LU GeoDataFrame
        for j in range(1, len(lu_gdf)):
            # Get the landuse class of the jth row of the LU GeoDataFrame
            curr_lu_class = lu_gdf.iloc[j]['landuse']
            # Get the geometry of the jth row of the LU GeoDataFrame
            curr_lu_geo = lu_gdf.iloc[j]['geometry']
            # Get the index of the jth row of the LU GeoDataFrame
            curr_lu_index = list(lu_gdf.index)[j]
            # Calculate the current distance between the geometry of the ith row
            # of the Potential Activity Locations and the geometry of jth row of the
            # LU GeoDataFrame
            curr_dist = curr_lu_geo.distance(pal_geo)
            # If the current distance is smaller than the closest distance,
            # set the closest distance to the current distance, the closest
            # LU class to the current LU class and closest LU index to the
            # current LU index. If the now closest distance is less than the
            # threshold of 1e-8 then break this for loop
            if curr_dist < closest_dist:
                closest_dist = curr_dist
                closest_lu_class = curr_lu_class
                closest_lu_geo = curr_lu_geo
                closest_lu_index = curr_lu_index
                if closest_dist < 1e-8:
                    break

        # At the end of the outer for loop, append the closest LU class to
        # the LU class list and the closest LU index to the LU index list
        lu_class_list.append(closest_lu_class)
        lu_index_list.append(closest_lu_index)
        # print(closest_lu_class)
        # print(closest_lu_index)

    # Copy the GeoDataFrame of Potential Activity Locations and add columns
    # for the LU information and return the new GeoDataFrame
    pal_lu_gdf = al_pal_gdf.copy()
    pal_lu_gdf['lu_type'] = lu_class_list
    pal_lu_gdf['lu_index'] = lu_index_list
    return pal_lu_gdf


def identify_pal(al_gdf, pal_gdf, radius):
    """
    Returns a Geodataframe of Activity Locations with appended PAL information corresponding to the Activity Locations

    Parameters:
    al_gdf = GeoDataFrame of Activity Locations
    pal_gdf = GeoDataFrame of PAL information
    radius = the range of distance from Activity Locations that PAL information will be collected from
    """
    # Initialize house_number, street_name, building_tyep
    # amenity_type, city, province, name_of_building/name_of_amenity
    # building_geometry and building_index
    pal_house_num_list = []
    pal_street_name_list = []
    pal_building_type_list = []
    pal_amenity_type_list = []
    pal_city_list = []
    #pal_province_list = []
    pal_name_list = []
    pal_geo_list = []
    pal_index_list = []
    pal_serial_list = []
    # Iterate through the length of a GeoDataFrame Activity Locations
    for i in range(len(al_gdf)):
        # Get the geometry and SerialID of row i for the Activity Locations
        al_geo = al_gdf.loc[i]['geometry']
        al_serial_id = al_gdf.loc[i]['SerialID']
        
        # Get the indexes of all buildings and amenities in the PAL GeoDataFrame
        # that are within the radius for the Activity Locations
        pal_in_radius = pal_gdf[pal_gdf['geometry'].distance(al_geo) < radius]
        pal_in_radius_index = pal_in_radius.index.to_list()
        
        # for each building or amenity, check if its index has been  
        # recorded in pal_index_list, if not, add its info into the lists for 
        # house_number, street_name, building_tyep
        # amenity_type, city, province, name_of_building/name_of_amenity
        # building_geometry and building_index
        for index in pal_in_radius_index:
            if index in pal_index_list:
                continue
            
            pal_house_num_list.append(pal_in_radius.loc[index]['addr:housenumber'])
            pal_street_name_list.append(pal_in_radius.loc[index]['addr:street'])
            
            building_value = pal_in_radius.loc[index]['building']
            if pd.isnull(building_value):
                pal_building_type_list.append('Not a building')
            elif building_value in unclassified_values:
                pal_building_type_list.append('unclassified')
            else:
                pal_building_type_list.append(building_value)
            
            amenity_value = pal_in_radius.loc[index]['amenity']
            if pd.isnull(amenity_value):
                pal_amenity_type_list.append('Not an amenity')
            else:
                pal_amenity_type_list.append(amenity_value)
                
            pal_city_list.append(pal_in_radius.loc[index]['addr:city'])
            #pal_province_list.append(pal_in_radius.loc[index]['addr:province'])
            pal_name_list.append(pal_in_radius.loc[index]['name'])
            pal_geo_list.append(pal_in_radius.loc[index]['geometry'])
            pal_index_list.append(index)
            pal_serial_list.append(al_serial_id)            
            
        # Create a dataframe for the points after matching
        temp_df = pd.DataFrame({'SerialID': pal_serial_list,
                                'pal_index': pal_index_list,
                                'house_num': pal_house_num_list,
                                'street': pal_street_name_list,
                                'city': pal_city_list,
                                #'province': pal_province_list,
                                'name': pal_name_list,
                                'building': pal_building_type_list,
                                'amenity': pal_amenity_type_list,
                                'geometry': pal_geo_list})

        # Convert the dataframe into a geodataframe
        al_pal_gdf = gpd.GeoDataFrame(temp_df, geometry='geometry', crs=al_gdf.crs)
        # Set crs for al_pal_gdf
        #al_pal_gdf.set_crs(epsg=)
    return al_pal_gdf


def create_al_info(al_gdf, lu_gdf, pal_gdf, pal_info_radius):
    """
    Returns a Geodataframe of Activity Locations with appended LU and PAL information corresponding to the Activity Locations

    Parameters:
    al_gdf = GeoDataFrame of Activity Locations
    pal_gdf = GeoDataFrame of PAL information
    lu_gdf = GeoDataFrame of LU information
    pal_info_radius = the range of distance from Activity Locations that PAL information 
                      will be collected from
    """
    # Identifiy the PAL(buildings and amenities) information
    # around the Activity Locations within the range of the input radius
    al_pal_gdf = identify_pal(al_gdf, pal_gdf, pal_info_radius)
    
    # Identify the landuse of the PAL(buildings and amenities)
    # that are found around the Activity Locations
    al_info_gdf = identify_lu(al_pal_gdf,lu_gdf)
    return al_info_gdf
