"""
Module Name: Activity Locations Identification
Source Name: activity_locations_identifaction.py
Creator: Hongzhao Tan (tanh10@mcmaster.ca)
Requirements: Python 3.8 or later
Date Created: Feb 12, 2023
Last Revised: Feb 12, 2023
Description: Appends LU and PAL for Activity Locations extracted by the Extractor module, if such information
             has been provided

Version History:
2023-02-12 (activity_locations_identification.py) Create identiy_LU, identify_PAL and create_AL_info functions

2023-02-13 (activity_locations_identification.py) Create comments explaining the logic of each function
"""

def identify_LU(AL_gdf, LU_gdf):
    """
    Returns a Geodataframe of Activity Locations with appended LU information corresponding to the Activity Locations

    Parameters:
    AL_gdf = GeoDataFrame of Activity Locations
    LU_gdf = GeoDataFrame of LU information
    """
    # Initialize lu_classification and lu_index columns
    LU_class_list = []
    LU_index_list = []
    # Iterate through the length of a GeoDataFrame of Activity Locations
    for i in range(len(AL_gdf)):
        # Get the geometry of row i for the Activity Locations
        AL_geo = AL_gdf.loc[i]['geometry']
        # Get the landuse class of the first row of the LU GeoDataFrame
        closest_LU_class = LU_gdf.iloc[0]['landuse']
        # Get the geometry of the first row of the LU GeoDataFrame
        closest_LU_geo = LU_gdf.iloc[0]['geometry']
        # Get the index of the first row of the LU GeoDataFrame
        closest_LU_index = list(LU_gdf.index)[0]
        # Calculate the closest distance between the geometry of the ith row
        # of the Activity Locations and the geometry of first row of the
        # LU GeoDataFrame
        closest_dist = closest_LU_geo.distance(AL_geo)
        # If the closest distance is smaller than the thershold 1e-8, append the
        # closest LU class and LU index into the arrays lu_classification and lu_index
        # arrays and continue the for loop to the next iteration
        if closest_dist < 1e-8:
            LU_class_list.append(closest_LU_class)
            LU_index_list.append(closest_LU_index)
            continue

        # If the distance was equal or greater than the threshold then iterate
        # through the second row till the length of the LU GeoDataFrame
        for j in range(1, len(LU_gdf)):
            # Get the landuse class of the jth row of the LU GeoDataFrame
            curr_LU_class = LU_gdf.iloc[j]['landuse']
            # Get the geometry of the jth row of the LU GeoDataFrame
            curr_LU_geo = LU_gdf.iloc[j]['geometry']
            # Get the index of the jth row of the LU GeoDataFrame
            curr_LU_index = list(LU_gdf.index)[j]
            # Calculate the current distance between the geometry of the ith row
            # of the Activity Locations and the geometry of jth row of the
            # LU GeoDataFrame
            curr_dist = curr_LU_geo.distance(AL_geo)
            # If the current distance is smaller than the closest distance,
            # set the closest distance to the current distance, the closest
            # LU class to the current LU class and closest LU index to the
            # current LU index. If the now closest distance is less than the
            # thershold of 1e-8 then break this for loop
            if curr_dist < closest_dist:
                closest_dist = curr_dist
                closest_LU_class = curr_LU_class
                closest_LU_geo = curr_LU_geo
                closest_LU_index = curr_LU_index
                if closest_dist < 1e-8:
                    break

        # At the end of the outer for loop, append the closest LU class to
        # the LU class list and the closest LU index to the LU index list
        LU_class_list.append(closest_LU_class)
        LU_index_list.append(closest_LU_index)
        print(closest_LU_class)
        print(closest_LU_index)

    # Copy the GeoDataFrame of Activity Locations and add columns
    # for the LU information and return the new GeoDataFrame
    AL_LU_gdf = AL_gdf.copy()
    AL_LU_gdf['lu_classification'] = LU_class_list
    AL_LU_gdf['lu_index'] = LU_index_list
    return AL_LU_gdf


def identify_PAL(AL_gdf, PAL_gdf):
    """
    Returns a Geodataframe of Activity Locations with appended PAL information corresponding to the Activity Locations

    Parameters:
    AL_gdf = GeoDataFrame of Activity Locations
    PAL_gdf = GeoDataFrame of PAL information
    """
    # Initialize house_number, street_name, city, province
    # name_of_building, building_geometry and building_index
    PAL_house_num_list = []
    PAL_street_name_list = []
    PAL_city_list = []
    PAL_province_list = []
    PAL_name_list = []
    PAL_geo_list = []
    PAL_index_list = []
    # Iterate through the length of a GeoDataFrame Activity Locations
    for i in range(len(AL_gdf)):
        # Get the geometry of row i for the Activity Locations
        AL_geo = AL_gdf.loc[i]['geometry']
        # Get the house number of the first row of the PAL GeoDataFrame
        closest_PAL_house_num = PAL_gdf.iloc[0]['addr:housenumber']
        # Get the street of the first row of the PAL GeoDataFrame
        closest_PAL_street_name = PAL_gdf.iloc[0]['addr:street']
        # Get the city of the first row of the PAL GeoDataFrame
        closest_PAL_city = PAL_gdf.iloc[0]['addr:city']
        # Get the province of the first row of the PAL GeoDataFrame
        closest_PAL_province = PAL_gdf.iloc[0]['addr:province']
        # Get the name of the first row of the PAL GeoDataFrame
        closest_PAL_name = PAL_gdf.iloc[0]['name']
        # Get the geometry of the first row of the PAL GeoDataFrame
        closest_PAL_geo = PAL_gdf.iloc[0]['geometry']
        # Get the index of the first row of the PAL GeoDataFrame
        closest_PAL_index = list(PAL_gdf.index)[0]

        closest_dist = closest_PAL_geo.distance(AL_geo)
        # If the closest distance is smaller than the thershold 1e-8, append the
        # closest PAL house number, street name, city, province, name, geometry
        # and list to their respective list and continue the for loop to the next
        # iteration
        if closest_dist < 1e-8:
            PAL_house_num_list.append(closest_PAL_house_num)
            PAL_street_name_list.append(closest_PAL_street_name)
            PAL_city_list.append(closest_PAL_city)
            PAL_province_list.append(closest_PAL_province)
            PAL_name_list.append(closest_PAL_name)
            PAL_geo_list.append(closest_PAL_geo)
            PAL_index_list.append(closest_PAL_index)
            continue

        # If the distance was equal or greater than the threshold then iterate
        # through the second row till the length of the PAL GeoDataFrame
        for j in range(1, len(PAL_gdf)):
            # Get the geometry of the jth row of the PAL GeoDataFrame
            curr_PAL_geo = PAL_gdf.iloc[j]['geometry']
            # Calculate the current distance between the geometry of the ith row
            # of the Activity Locations and the geometry of jth row of the
            # PAL GeoDataFrame
            curr_dist = curr_PAL_geo.distance(AL_geo)
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
                closest_PAL_house_num = PAL_gdf.iloc[j]['addr:housenumber']
                closest_PAL_street_name = PAL_gdf.iloc[j]['addr:street']
                closest_PAL_city = PAL_gdf.iloc[j]['addr:city']
                closest_PAL_province = PAL_gdf.iloc[j]['addr:province']
                closest_PAL_name = PAL_gdf.iloc[j]['name']
                closest_PAL_geo = curr_PAL_geo
                closest_PAL_index = list(PAL_gdf.index)[j]
                if closest_dist < 1e-8:
                    break

        # At the end of the outer for loop, append the closest PAL house
        # number, up till the closest PAL index, to their respective lists
        PAL_house_num_list.append(closest_PAL_house_num)
        PAL_street_name_list.append(closest_PAL_street_name)
        PAL_city_list.append(closest_PAL_city)
        PAL_province_list.append(closest_PAL_province)
        PAL_name_list.append(closest_PAL_name)
        PAL_geo_list.append(closest_PAL_geo)
        PAL_index_list.append(closest_PAL_index)
        print(closest_dist)
        print(closest_PAL_house_num)
        print(closest_PAL_street_name)
        print(closest_PAL_city)
        print(closest_PAL_province)
        print(closest_PAL_name)
        print(closest_PAL_index)
        print()

    # Copy the GeoDataFrame of Activity Locations and add columns
    # for the PAL information and return the new GeoDataFrame
    AL_PAL_gdf = AL_gdf.copy()
    AL_PAL_gdf['house_number'] = PAL_house_num_list
    AL_PAL_gdf['street_name'] = PAL_street_name_list
    AL_PAL_gdf['city'] = PAL_city_list
    AL_PAL_gdf['province'] = PAL_province_list
    AL_PAL_gdf['name_of_building'] = PAL_name_list
    AL_PAL_gdf['building_geometry'] = PAL_geo_list
    AL_PAL_gdf['building_index'] = PAL_index_list
    return AL_PAL_gdf

def create_AL_info(AL_LU_gdf,AL_PAL_gdf):
    """
    Returns a Geodataframe of Activity Locations with appended LU and PAL information corresponding to the Activity Locations

    Parameters:
    AL_LU_gdf = GeoDataFrame of Activity Locations with LU information
    AL_PAL_gdf = GeoDataFrame of Activity Locations with PAL information
    """
    # Copy the GeoDataFrame of Activity Locations and PAL information
    joined_gdf = AL_PAL_gdf.copy()
    # Join the LU information to the copied GeoDataFrame
    joined_gdf['lu_classification'] = AL_LU_gdf['lu_classification']
    joined_gdf['lu_index'] = AL_LU_gdf['lu_index']
    #joined_gdf = AL_PAL_gdf.merge(AL_LU_gdf,how='inner')
    # Return the joined GeoDataFrame with LU and PAL information
    return joined_gdf