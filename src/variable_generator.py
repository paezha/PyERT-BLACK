"""
Module Name: RCA Variables Generator (module for generating route choice analysis variables)
Source Name: variable_generator.py
Creator: Mengtong Shi (shim17@mcmaster.ca)
Requirements: Python 3.8 or later
Date Created: Feb 01, 2023
Last Revised: Feb 15, 2023
Description: Implements methods that are used to generate route choice analysis variables from
             the given route choice

Version History:
2023-02-01 (variable_generator.py)

2023-02-10 (variable_generator.py) Changed naming style to snake_case

2023-02-11 (variable_generator.py) Edited comments

2023-02-12 (variable_generator.py) Updated var_gen

2023-02-13 (variable_generator.py) Updated var_gen & comments

2023-02-14 (variable_generator.py) Updated var_gen

2023-02-14 (variable_generator.py) Updated var_gen to output number of left and right turns

2023-02-15 (variable_generator.py) Updated var_gen
"""

import math
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point


def var_gen(route, network_edges):
    """
    Returns a GeoDataframe that contains route choice analysis
    variables generated for the route choice

    Parameters:
    route = A GeoDataframe that represents a route choice
    network_edges = A Geodataframe that contains the data of
                    the edges in the Directed Graph
    """
    # Project the route to the same CRS as the network dataset
    network_epsg = network_edges.crs.to_epsg()
    route_gdf_proj = route.to_crs(epsg=network_epsg)
    # Find geometry extract route segments with each geometry
    rca = list(route['geometry'])
    # Find serial IDs extract route segments with each serial ID
    serial_id = list(route['SerialID'].value_counts().index)

    # The distance of the route
    distance = []
    # The number of left turns
    num_lt = []
    # The number of right turns
    num_rt = []
    # The number of roads
    num_r = []
    # The longest street name
    street_name = []
    # The longest street name length
    length = []
    for i in range(len(route_gdf_proj)):
        curr_route_coord = list(route_gdf_proj.loc[i]['geometry'].coords)

        # Get the length of the input route in meters
        route_dist_length = route_gdf_proj.loc[i]['geometry'].length
        distance.append(route_dist_length)
        edges_route_passed = list(route_gdf_proj.loc[i]['edgesRoutePassed'])
        # print("Length of matched Route Choice is: " +
        #       str(round(route_dist_length, 2)) + " meters")

        # Count the number of turns
        num_of_t = count_turns(
            network_edges, edges_route_passed, curr_route_coord)
        # print(num_of_turns)

        num_lt.append(num_of_t['left'])
        num_rt.append(num_of_t['right'])

        # Get information about the longest leg
        longest_leg_info = longest_leg(
            network_edges, edges_route_passed, curr_route_coord)
        # print(longest_leg_info)
        street_name.append(longest_leg_info['legStreet'])
        length.append(longest_leg_info['legLength'])
        num_r.append(longest_leg_info['numOfStreets'])

    temp_df = pd.DataFrame({'SerialID': serial_id,
                            'distanceMeter:': distance,
                            'numOfLturns:': num_lt,
                            'numOfRturns:': num_rt,
                            'numOfRoads': num_r,
                            'streetLongestLeg': street_name,
                            'lengthLongestLeg': length,
                            'geometry': rca})
    rca_gdf = gpd.GeoDataFrame(temp_df, geometry='geometry')

    return rca_gdf


def find_nearest_street(network_pe, edges_route_passed, coord):
    """
    Returns a string which is the name of the nearest street to a point

    Parameters:
    network_pe = A Geodataframe that contains the data of the edges in the Directed Graph
    edges_route_passed = A list of the edges passed by the route
    coord = A pair of coordinates for the point
    """
    point_on_route = Point(coord[0], coord[1])
    nearest_dist = network_pe.loc[edges_route_passed[0]
                                  ]['geometry'].distance(point_on_route)
    nearest_street = network_pe.loc[edges_route_passed[0]]['name']
    for edge_id in edges_route_passed[1:]:
        edge_geo = network_pe.loc[edge_id]['geometry']
        curr_dist = edge_geo.distance(point_on_route)
        # print(network_pe.loc[edge_id]['name'])
        # print(curr_dist)
        if curr_dist < nearest_dist:
            nearest_dist = curr_dist
            nearest_street = network_pe.loc[edge_id]['name']

    return nearest_street


def count_turns(network_pe, edges_route_passed, route_coord):
    """
    Returns a dictionary that contains the number of left turns,
    right turns and total turns of the input route

    Parameters:
    network_pe = A Geodataframe that contains the data of the edges in the Directed Graph
    edges_route_passed = A list of the edges passed by the route
    route_coord = A list of coordinates for the points on the route
    """
    num_left_turn = 0
    num_right_turn = 0
    for j in range(1, len(route_coord) - 1):
        line_segment1 = (route_coord[j], route_coord[j - 1])
        line_segment2 = (route_coord[j], route_coord[j + 1])

        # Using Dot Product to determine the angle between two line segments
        # Convert to vector form
        vector1 = ((line_segment1[0][0] - line_segment1[1][0]),
                   (line_segment1[0][1] - line_segment1[1][1]))
        vector2 = ((line_segment2[0][0] - line_segment2[1][0]),
                   (line_segment2[0][1] - line_segment2[1][1]))
        # Calculate dot product
        dot_prod = vector1[0] * vector2[0] + vector1[1] * vector2[1]
        # Calculate magnitudes of two line segments
        magnitude1 = (vector1[0] * vector1[0] + vector1[1] * vector1[1]) ** 0.5
        magnitude2 = (vector2[0] * vector2[0] + vector2[1] * vector2[1]) ** 0.5
        # Calculate cosine value
        cos_val = dot_prod / (magnitude1 * magnitude2)
        # set cos_val to 1 or -1 if cos_val is not in the [-1,1] value range
        if cos_val > 1:
            cos_val = 1
        elif cos_val < -1:
            cos_val = -1
        # Calculate angle in radians then convert to degrees
        angle_rad = math.acos(cos_val)
        angle_deg = math.degrees(angle_rad) % 360

        if angle_deg > 180:
            angle_deg = 360 - angle_deg

        # If an angle greater than 30 degrees is found,
        # Check if the two line segments of the angle are going from one street to another.
        if abs(180 - angle_deg) > 30:
            # print(angle_deg)
            start_street = find_nearest_street(
                network_pe, edges_route_passed, route_coord[j - 1])
            # print(start_street)
            end_street = find_nearest_street(
                network_pe, edges_route_passed, route_coord[j + 1])
            # print(end_street)
            # If the two line segments of the angle are going from one street to another
            # Meaning a Turn is found. Then use cross product
            # to determine the direction of the turn(Left/Right)
            if start_street != end_street:
                point_diff1 = (route_coord[j + 1][0] - route_coord[j - 1]
                               [0], route_coord[j + 1][1] - route_coord[j - 1][1])
                point_diff2 = (
                    route_coord[j][0] - route_coord[j - 1][0], route_coord[j][1] - route_coord[j - 1][1])
                cross_prod = point_diff1[0] * point_diff2[1] - \
                    point_diff2[0] * point_diff1[1]
                if cross_prod < 0:
                    # print('Left Turn')
                    num_left_turn += 1
                elif cross_prod > 0:
                    # print('Right Turn')
                    num_right_turn += 1

    return {'left': num_left_turn, 'right': num_right_turn, 'total': (num_left_turn + num_right_turn)}


def longest_leg(network_pe, edges_route_passed, route_coord):
    """
    Returns a dictionary that contains information about the longest
    leg in the route

    Parameters:
    network_pe = A Geodataframe that contains the data of the edges in the Directed Graph
    edges_route_passed = A list of the edges passed by the route
    route_coord = A list of coordinates for the points on the route
    """
    leg_len_dict = {}
    curr_street = find_nearest_street(
        network_pe, edges_route_passed, route_coord[0])
    # lastPoint = route_coord[0]
    leg_len_dict[curr_street] = 0
    for i in range(1, len(route_coord)):
        line_seg_len = Point(
            route_coord[i - 1]).distance(Point(route_coord[i]))
        leg_len_dict[curr_street] += line_seg_len
        point_street = find_nearest_street(
            network_pe, edges_route_passed, route_coord[i])

        if curr_street != point_street:
            if point_street not in leg_len_dict:
                leg_len_dict[point_street] = 0
            # else:
            #    leg_len_dict[point_street] += line_seg_len

            curr_street = point_street
    # print(leg_len_dict)

    long_leg_street = curr_street
    long_leg_len = leg_len_dict[curr_street]
    street_count = 0
    for street in leg_len_dict:
        curr_leg_len = leg_len_dict[street]
        if long_leg_len < curr_leg_len:
            long_leg_street = street
            long_leg_len = curr_leg_len
        street_count += 1

    return {'legStreet': long_leg_street, 'legLength': long_leg_len, 'numOfStreets': street_count}
