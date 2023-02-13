"""
Module Name: Activity Locations Identification
Source Name: activity_locations_identifaction.py
Creator: Hongzhao Tan (tanh10@mcmaster.ca)
Requirements: Python 3.8 or later
Date Created: Feb 12, 2023
Last Revised: Feb 12, 2023
Description:

Version History:
2023-02-12
"""

def identify_LU(AL_gdf, LU_gdf):
    LU_class_list = []
    LU_index_list = []
    for i in range(len(AL_gdf)):
        AL_geo = AL_gdf.loc[i]['geometry']
        closest_LU_class = LU_gdf.iloc[0]['landuse']
        closest_LU_geo = LU_gdf.iloc[0]['geometry']
        closest_LU_index = list(LU_gdf.index)[0]
        closest_dist = closest_LU_geo.distance(AL_geo)
        if closest_dist < 1e-8:
            LU_class_list.append(closest_LU_class)
            LU_index_list.append(closest_LU_index)
            continue

        for j in range(1, len(LU_gdf)):
            curr_LU_class = LU_gdf.iloc[j]['landuse']
            curr_LU_geo = LU_gdf.iloc[j]['geometry']
            curr_LU_index = list(LU_gdf.index)[j]
            curr_dist = curr_LU_geo.distance(AL_geo)
            if curr_dist < closest_dist:
                closest_dist = curr_dist
                closest_LU_class = curr_LU_class
                closest_LU_geo = curr_LU_geo
                closest_LU_index = curr_LU_index
                if closest_dist < 1e-8:
                    break

        LU_class_list.append(closest_LU_class)
        LU_index_list.append(closest_LU_index)
        print(closest_LU_class)
        print(closest_LU_index)

    AL_LU_gdf = AL_gdf.copy()
    AL_LU_gdf['lu_classification'] = LU_class_list
    AL_LU_gdf['lu_index'] = LU_index_list
    return AL_LU_gdf


def identify_PAL(AL_gdf, PAL_gdf):
    PAL_house_num_list = []
    PAL_street_name_list = []
    PAL_city_list = []
    PAL_province_list = []
    PAL_name_list = []
    PAL_geo_list = []
    PAL_index_list = []
    for i in range(len(AL_gdf)):
        AL_geo = AL_gdf.loc[i]['geometry']
        closest_PAL_house_num = PAL_gdf.iloc[0]['addr:housenumber']
        closest_PAL_street_name = PAL_gdf.iloc[0]['addr:street']
        closest_PAL_city = PAL_gdf.iloc[0]['addr:city']
        closest_PAL_province = PAL_gdf.iloc[0]['addr:province']
        closest_PAL_name = PAL_gdf.iloc[0]['name']
        closest_PAL_geo = PAL_gdf.iloc[0]['geometry']
        closest_PAL_index = list(PAL_gdf.index)[0]
        closest_dist = closest_PAL_geo.distance(AL_geo)
        if closest_dist < 1e-8:
            PAL_house_num_list.append(closest_PAL_house_num)
            PAL_street_name_list.append(closest_PAL_street_name)
            PAL_city_list.append(closest_PAL_city)
            PAL_province_list.append(closest_PAL_province)
            PAL_name_list.append(closest_PAL_name)
            PAL_geo_list.append(closest_PAL_geo)
            PAL_index_list.append(closest_PAL_index)
            continue

        for j in range(1, len(PAL_gdf)):
            curr_PAL_geo = PAL_gdf.iloc[j]['geometry']
            curr_dist = curr_PAL_geo.distance(AL_geo)

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
    joined_gdf = AL_PAL_gdf.copy()
    joined_gdf['lu_classification'] = AL_LU_gdf['lu_classification']
    joined_gdf['lu_index'] = AL_LU_gdf['lu_index']
    #joined_gdf = AL_PAL_gdf.merge(AL_LU_gdf,how='inner')
    return joined_gdf