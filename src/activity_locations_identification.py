"""
Module Name: Activity Locations Identification
Source Name: activity_locations_identification.py
Creator: Hongzhao Tan (tanh10@mcmaster.ca)
Requirements: Python 3.8 or later
Date Created: Feb 12, 2023
Last Revised: Feb 12, 2023
Description: Appends LU and PAL for Activity Locations extracted by the Extractor module,
             if such information has been provided

Version History:
2023-02-12 (activity_locations_identification.py) Create identify_lu, identify_PAL and create_al_info functions

2023-02-13 (activity_locations_identification.py) Create comments explaining the logic of each function

2023-02-13 (activity_locations_identification.py) Update format & naming
"""


def identify_lu(al_gdf, lu_gdf):
    """
    Returns a Geodataframe of Activity Locations with appended LU information corresponding to the Activity Locations

    Parameters:
    al_gdf = GeoDataFrame of Activity Locations
    lu_gdf = GeoDataFrame of LU information
    """
    # Initialize lu_classification and lu_index columns
    lu_class_list = []
    lu_index_list = []
    # Iterate through the length of a GeoDataFrame of Activity Locations
    for i in range(len(al_gdf)):
        # Get the geometry of row i for the Activity Locations
        al_geo = al_gdf.loc[i]['geometry']
        # Get the landuse class of the first row of the LU GeoDataFrame
        closest_lu_class = lu_gdf.iloc[0]['landuse']
        # Get the geometry of the first row of the LU GeoDataFrame
        closest_lu_geo = lu_gdf.iloc[0]['geometry']
        # Get the index of the first row of the LU GeoDataFrame
        closest_lu_index = list(lu_gdf.index)[0]
        # Calculate the closest distance between the geometry of the ith row
        # of the Activity Locations and the geometry of first row of the
        # LU GeoDataFrame
        closest_dist = closest_lu_geo.distance(al_geo)
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
            # of the Activity Locations and the geometry of jth row of the
            # LU GeoDataFrame
            curr_dist = curr_lu_geo.distance(al_geo)
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

    # Copy the GeoDataFrame of Activity Locations and add columns
    # for the LU information and return the new GeoDataFrame
    al_lu_gdf = al_gdf.copy()
    al_lu_gdf['lu_classification'] = lu_class_list
    al_lu_gdf['lu_index'] = lu_index_list
    return al_lu_gdf


def identify_PAL(al_gdf, pal_gdf):
    """
    Returns a Geodataframe of Activity Locations with appended PAL information corresponding to the Activity Locations

    Parameters:
    al_gdf = GeoDataFrame of Activity Locations
    pal_gdf = GeoDataFrame of PAL information
    """
    # Initialize house_number, street_name, city, province
    # name_of_building, building_geometry and building_index
    pal_house_num_list = []
    pal_street_name_list = []
    pal_city_list = []
    pal_province_list = []
    pal_name_list = []
    pal_geo_list = []
    pal_index_list = []
    # Iterate through the length of a GeoDataFrame Activity Locations
    for i in range(len(al_gdf)):
        # Get the geometry of row i for the Activity Locations
        AL_geo = al_gdf.loc[i]['geometry']
        # Get the house number of the first row of the PAL GeoDataFrame
        closest_pal_house_num = pal_gdf.iloc[0]['addr:housenumber']
        # Get the street of the first row of the PAL GeoDataFrame
        closest_pal_street_name = pal_gdf.iloc[0]['addr:street']
        # Get the city of the first row of the PAL GeoDataFrame
        closest_pal_city = pal_gdf.iloc[0]['addr:city']
        # Get the province of the first row of the PAL GeoDataFrame
        closest_pal_province = pal_gdf.iloc[0]['addr:province']
        # Get the name of the first row of the PAL GeoDataFrame
        closest_pal_name = pal_gdf.iloc[0]['name']
        # Get the geometry of the first row of the PAL GeoDataFrame
        closest_pal_geo = pal_gdf.iloc[0]['geometry']
        # Get the index of the first row of the PAL GeoDataFrame
        closest_pal_index = list(pal_gdf.index)[0]

        closest_dist = closest_pal_geo.distance(AL_geo)
        # If the closest distance is smaller than the threshold 1e-8, append the
        # closest PAL house number, street name, city, province, name, geometry
        # and list to their respective list and continue the for loop to the next
        # iteration
        if closest_dist < 1e-8:
            pal_house_num_list.append(closest_pal_house_num)
            pal_street_name_list.append(closest_pal_street_name)
            pal_city_list.append(closest_pal_city)
            pal_province_list.append(closest_pal_province)
            pal_name_list.append(closest_pal_name)
            pal_geo_list.append(closest_pal_geo)
            pal_index_list.append(closest_pal_index)
            continue

        # If the distance was equal or greater than the threshold then iterate
        # through the second row till the length of the PAL GeoDataFrame
        for j in range(1, len(pal_gdf)):
            # Get the geometry of the jth row of the PAL GeoDataFrame
            curr_pal_geo = pal_gdf.iloc[j]['geometry']
            # Calculate the current distance between the geometry of the ith row
            # of the Activity Locations and the geometry of jth row of the
            # PAL GeoDataFrame
            curr_dist = curr_pal_geo.distance(AL_geo)
            # If the current distance is smaller than the closest distance,
            # set the closest distance to the current distance, the closest PAL
            # house number to the jth rows house number, closest street name
            # to the jth rows street, closest city to the jth rows city, the
            # closest province to the jth province, closest name to the jth
            # name, closest geometry to the jth geometry and closest index to
            # the jth index. If the now closest distance is less than the threshold
            # of 1e-8 then break the loop
            if curr_dist < closest_dist:
                closest_dist = curr_dist
                closest_pal_house_num = pal_gdf.iloc[j]['addr:housenumber']
                closest_pal_street_name = pal_gdf.iloc[j]['addr:street']
                closest_pal_city = pal_gdf.iloc[j]['addr:city']
                closest_pal_province = pal_gdf.iloc[j]['addr:province']
                closest_pal_name = pal_gdf.iloc[j]['name']
                closest_pal_geo = curr_pal_geo
                closest_pal_index = list(pal_gdf.index)[j]
                if closest_dist < 1e-8:
                    break

        # At the end of the outer for loop, append the closest PAL house
        # number, up till the closest PAL index, to their respective lists
        pal_house_num_list.append(closest_pal_house_num)
        pal_street_name_list.append(closest_pal_street_name)
        pal_city_list.append(closest_pal_city)
        pal_province_list.append(closest_pal_province)
        pal_name_list.append(closest_pal_name)
        pal_geo_list.append(closest_pal_geo)
        pal_index_list.append(closest_pal_index)
        # print(closest_dist)
        # print(closest_pal_house_num)
        # print(closest_pal_street_name)
        # print(closest_pal_city)
        # print(closest_pal_province)
        # print(closest_pal_name)
        # print(closest_pal_index)
        # print()

    # Copy the GeoDataFrame of Activity Locations and add columns
    # for the PAL information and return the new GeoDataFrame
    al_pal_gdf = al_gdf.copy()
    al_pal_gdf['house_number'] = pal_house_num_list
    al_pal_gdf['street_name'] = pal_street_name_list
    al_pal_gdf['city'] = pal_city_list
    al_pal_gdf['province'] = pal_province_list
    al_pal_gdf['name_of_building'] = pal_name_list
    al_pal_gdf['building_geometry'] = pal_geo_list
    al_pal_gdf['building_index'] = pal_index_list
    return al_pal_gdf


def create_al_info(al_lu_gdf, al_pal_gdf):
    """
    Returns a Geodataframe of Activity Locations with appended LU and PAL information corresponding to the Activity Locations

    Parameters:
    al_lu_gdf = GeoDataFrame of Activity Locations with LU information
    al_pal_gdf = GeoDataFrame of Activity Locations with PAL information
    """
    # Copy the GeoDataFrame of Activity Locations and PAL information
    joined_gdf = al_pal_gdf.copy()
    # Join the LU information to the copied GeoDataFrame
    joined_gdf['lu_classification'] = al_lu_gdf['lu_classification']
    joined_gdf['lu_index'] = al_lu_gdf['lu_index']
    # joined_gdf = al_pal_gdf.merge(al_lu_gdf,how='inner')
    # Return the joined GeoDataFrame with LU and PAL information
    return joined_gdf
