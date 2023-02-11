"""
Module Name: RCA Variables Generator (module for generating data for route choice modeling)
Source Name: variable_generator.py
Creator: Mengtong Shi (shim17@mcmaster.ca)
Requirements: Python 3.8 or later
Date Created: Feb 05, 2023
Last Revised: Feb 10, 2023
Description: 

Version History:
2023-02-05 (variable_generator.py)

2023-02-10 (variable_generator.py)
"""

import math
from shapely.geometry import Point, LineString
import RouteSolver as rs


def var_gen():
    return


def find_nearest_street(networkPE, edgesRoutePassed, Coord):
    point_on_route = Point(Coord[0], Coord[1])
    nearest_dist = networkPE.loc[edgesRoutePassed[0]
                                 ]['geometry'].distance(point_on_route)
    nearest_street = networkPE.loc[edgesRoutePassed[0]]['name']
    for edge_id in edgesRoutePassed[1:]:
        edge_geo = networkPE.loc[edge_id]['geometry']
        curr_dist = edge_geo.distance(point_on_route)
        # print(networkPE.loc[edge_id]['name'])
        # print(curr_dist)
        if curr_dist < nearest_dist:
            nearest_dist = curr_dist
            nearest_street = networkPE.loc[edge_id]['name']

    return nearest_street


def count_turns(networkPE, edgesRoutePassed, routeCoord):
    num_left_turn = 0
    num_right_turn = 0
    for j in range(1, len(routeCoord)-1):
        line_segment1 = (routeCoord[j], routeCoord[j-1])
        line_segment2 = (routeCoord[j], routeCoord[j+1])
        # print(straightLine1)
        # print(straightLine2)

        # Using Dot Product to determine the angle between two line segments
        # Convert to vector form
        vector1 = ((line_segment1[0][0]-line_segment1[1][0]),
                   (line_segment1[0][1]-line_segment1[1][1]))
        vector2 = ((line_segment2[0][0]-line_segment2[1][0]),
                   (line_segment2[0][1]-line_segment2[1][1]))
        # Calculate dot product
        dot_prod = vector1[0]*vector2[0] + vector1[1]*vector2[1]
        # Calculate magnitudes of two line segments
        magnitude1 = (vector1[0]*vector1[0] + vector1[1]*vector1[1])**0.5
        magnitude2 = (vector2[0]*vector2[0] + vector2[1]*vector2[1])**0.5
        # Calculate cosine value
        cos_val = dot_prod/(magnitude1*magnitude2)
        # Calculate angle in radians then convert to degrees
        angle_rad = math.acos(cos_val)
        angle_deg = math.degrees(angle_rad) % 360

        if angle_deg > 180:
            angle_deg = 360-angle_deg

        # If an angle greater than 30 degrees is found,
        # Check if the two line segments of the angle are going from one street to another.
        if abs(180-angle_deg) > 30:
            print(angle_deg)
            start_street = find_nearest_street(
                networkPE, edgesRoutePassed, routeCoord[j-1])
            print(start_street)
            end_street = find_nearest_street(
                networkPE, edgesRoutePassed, routeCoord[j+1])
            print(end_street)
            # If the two line segments of the angle are going from one street to another
            # Meaning a Turn is found. Then use cross product to determine the direction of the turn(Left/Right)
            if (start_street != end_street):
                pointDiffA = (routeCoord[j+1][0] - routeCoord[j-1]
                              [0], routeCoord[j+1][1] - routeCoord[j-1][1])
                pointDiffB = (
                    routeCoord[j][0] - routeCoord[j-1][0], routeCoord[j][1] - routeCoord[j-1][1])
                crossProd = pointDiffA[0] * pointDiffB[1] - \
                    pointDiffB[0] * pointDiffA[1]
                if crossProd < 0:
                    print('Left Turn')
                    num_left_turn += 1
                elif crossProd > 0:
                    print('Right Turn')
                    num_right_turn += 1
            # print()

    return {'left': num_left_turn, 'right': num_right_turn, 'total': (num_left_turn+num_right_turn)}


def longest_leg(networkPE, edgesRoutePassed, routeCoord):
    leg_len_dict = {}
    curr_street = find_nearest_street(
        networkPE, edgesRoutePassed, routeCoord[0])
    lastPoint = routeCoord[0]
    leg_len_dict[curr_street] = 0
    for i in range(1, len(routeCoord)):
        lineSegLen = Point(routeCoord[i-1]).distance(Point(routeCoord[i]))
        leg_len_dict[curr_street] += lineSegLen
        point_street = find_nearest_street(
            networkPE, edgesRoutePassed, routeCoord[i])

        if curr_street != point_street:
            if point_street not in leg_len_dict:
                leg_len_dict[point_street] = 0
            # else:
            #    leg_len_dict[point_street] += lineSegLen

            curr_street = point_street
    print(leg_len_dict)

    longLegStreet = curr_street
    longLegLen = leg_len_dict[curr_street]
    for street in leg_len_dict:
        currLegLen = leg_len_dict[street]
        if longLegLen < currLegLen:
            longLegStreet = street
            longLegLen = currLegLen

    return {'legStreet': longLegStreet, 'legLength': longLegLen}
