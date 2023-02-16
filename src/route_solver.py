"""
Module Name: Route Solver (module for map-matching and route generation algorithms)
Source Name: route_solver.py
Creator: Hongzhao Tan (tanh10@mcmaster.ca)
Requirements: Python 3.8 or later
Date Created: Jan 31, 2023
Last Revised: Feb 13, 2023
Description: Implements methods that are used to generate map-matched route 
or shortest path from GPS trajectory. A GPS trajectory consists of streams of points recorded 
by a GPS device that captures movement at a given period.

Version History:
2023-01-31 (RouteSolver.py)

2023-02-07 (RouteSolver.py) Update implementation of route_choice_gen 
and detect_and_fill_gap functions, to let the output of route_choice_gen 
include the IDs of edges in the network dataset that the route generated has passed through

2023-02-09 (RouteSolver.py) Separate the local function for finding the IDs of edges a filled gap 
has passed through out from the implementation of detect_and_fill_gap function as a new function 
filled_gap_edges

2023-02-12 (route_solver.py) change naming style to snake_case

2023-02-13 (route_solver.py) updated map_point_to_network function 
to identify if the last point of a trip trajectory is on an intersection 
point of two or more streets.

2023-02-13 (route_solver.py) Update comments & naming

2023-02-14 (route_solver.py) fix bugs and update comments & naming
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import osmnx as ox
from shapely.geometry import Point, LineString


def route_choice_gen(trip, network_graph, network_edges, network_nodes):
    """
    Returns a Geodataframe where each row contains a route 
    by matching GPS trip trajectories onto the transportation network

    Parameters: 
    trip = A Geodataframe that contains the data of GPS points in trip trajectories
    network_graph = A Directed Graph object that is projected and 
                    contains the data of the transportation network
    network_edges = A Geodataframe that contains the data of the edges 
                    in the Directed Graph network_graph
    network_nodes = A Geodataframe that contains the data of the nodes 
                    in the Directed Graph network_graph
    """

    network_epsg = network_graph.graph['crs'].to_epsg()
    # Find unique serial IDs extract trip segments with each unique serial ID
    unique_serials = list(trip['SerialID'].value_counts().index)
    # Initialize lists to contain generated routes
    routes = []
    # Initialize list of lists that contains IDs of edges each of the routes has on
    edges_route_passed = []
    for serial_id in unique_serials:
        # extract trip segments with each unique serial ID
        curr_serial_points = trip[trip['SerialID'] == serial_id]
        # Matching points to the network data
        points_on_net = map_point_to_network(
            curr_serial_points, network_graph, network_edges)
        # Because the matched points have not been projected to any CRS yet,
        # we need to first project them to the CRS of the network dataset
        points_on_net = points_on_net.set_crs(epsg=network_epsg)

        # Detecting gaps between the points and fill the gaps
        points_on_net, filled_gaps = detect_and_fill_gap(
            points_on_net, network_graph, network_nodes, network_edges)

        # Then project to the global geographic CRS with EPSG number 4326
        # for future visualizing the matched points
        point_on_net_geo_crs = points_on_net.to_crs(epsg=4326)
        # Same as the points, we need to set the CRS for the filled gaps
        filled_gaps = filled_gaps.set_crs(epsg=network_epsg)
        filled_gaps_geocrs = filled_gaps.to_crs(epsg=4326)

        # Connecting the matched points and the filled gaps
        # to generate full route for the trip segment
        routes.append(connect_points_and_filled_gaps(
            point_on_net_geo_crs, filled_gaps_geocrs))

        # Get all IDs of unique edges the route generated
        # for current trip segment has passed through
        tmp_edge_ids_set = set(
            point_on_net_geo_crs['nearEdgeID'].value_counts().index)
        for i in range(len(filled_gaps)):
            tmp_set = set(filled_gaps.loc[i]['EdgesGapPassed'])
            tmp_edge_ids_set = tmp_edge_ids_set.union(tmp_set)
        edges_route_passed.append(tmp_edge_ids_set)

    temp_df = pd.DataFrame({'SerialID': unique_serials,
                            'edgesRoutePassed': edges_route_passed,
                            'geometry': routes})
    routes_gdf = gpd.GeoDataFrame(temp_df, geometry='geometry')
    return routes_gdf


def map_point_to_network(points, network_pg, network_pe):
    """
    Returns a Geodataframe of points in a trip segment matched onto the transportation network

    Parameters: 
    points = A Geodataframe that contains the data of GPS points of a trip trajectory 
    network_pg = A Directed Graph object that is projected 
    and contains the data of the transportation network
    network_pe = A Geodataframe that contains the data of the edges in the Directed Graph network_pg
    """
    # Coordinates of points after matching
    point_on_net = []
    # The edge IDs of the edges that each of the matched points is on
    near_edges_id = []
    # The edge names of the edges that each of the matched points is on
    near_edges_name = []
    # Coordinates of the leg(a straight line segment in an edge)
    # that each of the matched points is on
    near_legs_geo = []

    # Project the sample GPS points to the same CRS as the network dataset
    network_epsg = network_pe.crs.to_epsg()
    points = points.to_crs(network_epsg)

    # Finding the nearest edge for every sample GPS point and take the edges' IDs
    for point in points['geometry']:
        near_edge = ox.distance.nearest_edges(
            network_pg, point.x, point.y, return_dist=True)
        # print(networkE.loc[near_edge[0]]['name'])
        near_edges_id.append(near_edge[0])
        # nearEdgesDist.append(near_edge[1])

    # For the each sample GPS point, find the nearest leg on its nearest edges,
    # and find the nearest point on the nearest leg to the sample GPS point
    for i, edge in enumerate(near_edges_id):
        if 1 <= i < (len(near_edges_id)-1):
            # If current GPS point is on a different street from the following 
            # and the following and former GPS points are on the same street
            # current GPS point could be crossing an interesction of two streets
            if ((network_pe.loc[near_edges_id[i-1]]['name'] == network_pe.loc[near_edges_id[i+1]]['name']) and
                    (network_pe.loc[near_edges_id[i]]['name'] != network_pe.loc[near_edges_id[i+1]]['name'])):
                near_edges_id[i] = near_edges_id[i-1]

        # if the last GPS point is on a different street from the second last GPS point,
        # check the distance between the edges they are on,
        # if the distance is not greater than 10 meters,
        # the last GPS point could be on a interesction of two streets
        if i == (len(near_edges_id)-1):
            if ((network_pe.loc[near_edges_id[i]]['name'] != network_pe.loc[near_edges_id[i-1]]['name']) and
                    (network_pe.loc[near_edges_id[i]]['geometry'].distance(network_pe.loc[near_edges_id[i-1]]['geometry']) <= 10)):
                near_edges_id[i] = near_edges_id[i-1]

        # Get the coordinates of the nearest edge of current GPS point
        near_edges_name.append(network_pe.loc[near_edges_id[i]]['name'])
        near_edge_geo = network_pe.loc[near_edges_id[i]]['geometry']
        near_edge_coord = list(near_edge_geo.coords)

        # find the nearest leg on the nearest edge of current GPS point
        near_leg = LineString([near_edge_coord[0], near_edge_coord[1]])
        near_leg_dist = near_leg.distance(points['geometry'][i])
        for i in range(1, len(near_edge_coord)-1):
            curr_leg = LineString([near_edge_coord[i], near_edge_coord[i+1]])
            curr_dist = curr_leg.distance(points['geometry'][i])
            if curr_dist < near_leg_dist:
                near_leg = curr_leg
        # find the nearest point on the nearest leg to the sample GPS point
        point_on_net.append(near_leg.interpolate(near_leg.project(list(points['geometry'])[i])))
        near_legs_geo.append(near_leg)

    # Create a dataframe for the points after matching
    temp_df = pd.DataFrame({'SerialID': list(points['SerialID']),
                            'RecordID': list(points['RecordID']),
                            'nearEdgeID': near_edges_id,
                            'nearEdgeName': near_edges_name,
                            'nearLeg': near_legs_geo,
                            'geometry': point_on_net})

    # Convert the dataframe into a geodataframe
    points_on_net_gdf = gpd.GeoDataFrame(temp_df, geometry='geometry')
    return points_on_net_gdf


def detect_and_fill_gap(points, network_pg, network_pn, network_pe):
    """
    Detects gaps from GPS points in trip trajectory 
    and returns a Geodataframe where each row contains a route 
    that is generated using shortest path algorithms and fills a detected gap

    Parameters: 
    points = A Geodataframe that contains the data of GPS points of a trip trajectory
    network_pg = A Directed Graph object that is projected 
    and contains the data of the transportation network
    network_pn = A Geodataframe that contains the data of the nodes in the Directed Graph network_pg
    """
    # The track IDs of the start points of the gaps
    gaps_orig_record_id = []
    # The episode IDs of the start points of the gaps
    gaps_orig_eps_id = []
    # The shortest routes that fill the gaps
    filled_gaps_line = []
    # The Edges on the network the filled gaps has passed
    edges_gaps_passed = []
    # For each pair of adjacent matched points, check if there is a gap between them
    # and fill the gap if found
    for i in range(1, len(points)):
        # Gap exists when the two adjacent points are not on the same edge in the network dataset
        # and the distance between them exceeds 50 meters.
        if (((points.loc[i-1]['nearEdgeID'] != points.loc[i]['nearEdgeID']) and
                (points.loc[i-1]['geometry'].distance(points.loc[i]['geometry'])) > 50) or
            (points.loc[i-1]['nearEdgeName'] != points.loc[i]['nearEdgeName'])):
            #print((points.loc[i-1]['RecordID'], points.loc[i]['RecordID']))
            # print(points.loc[i-1]['geometry'].distance(points.loc[i]['geometry']))
            # Get the track ID and episode ID of the start point of the gap
            gaps_orig_record_id.append(points.loc[i-1]['RecordID'])
            gaps_orig_eps_id.append(points.loc[i-1]['SerialID'])

            # Find the two nodes in the network dataset that are nearest to the start
            # and end points of the gap respectively
            start_node = ox.distance.nearest_nodes(
                network_pg, points.loc[i-1]['geometry'].x, points.loc[i-1]['geometry'].y)
            end_node = ox.distance.nearest_nodes(
                network_pg, points.loc[i]['geometry'].x, points.loc[i]['geometry'].y)
            # Find the shortest route between the two nodes found
            shortest_route = ox.distance.shortest_path(network_pg,
                                                       start_node,
                                                       end_node,
                                                       weight='length')
            # print(shortest_route)
            # Get the coordinates of the nodes on the shortest route
            shortest_route_geo = [(network_pn.loc[nodeID]['geometry'].x,
                                    network_pn.loc[nodeID]['geometry'].y)
                                    for nodeID in shortest_route]
            if len(shortest_route_geo) == 1:
                shortest_route_geo.insert(0,(points.loc[i-1]['geometry'].x,
                                                points.loc[i-1]['geometry'].y))
                shortest_route_geo.append((points.loc[i]['geometry'].x,points.loc[i]['geometry'].y))
            # print(shortest_route_geo)
            # Turning coordinates on shortest route to Point objects
            shortest_route_points = [Point(point_geo) for point_geo in shortest_route_geo]
            # Get the IDs of edges in the network that the filled gap has passed through
            # and add them into the list edges_gaps_passed
            shortest_route_edges = filled_gap_edges(points.loc[i-1]['SerialID'],
                                                    points.loc[i-1]['RecordID'],
                                                    shortest_route_points, network_pg, network_pe)
            edges_gaps_passed.append(shortest_route_edges)

            # Connect the coordinates of the nodes on the shortest route into one LineString
            filled_gaps_line.append(LineString(shortest_route_geo))

            # Check to see if the filled gap went over following points,
            # if yes, change the overlapped points' coordinates to the end of the filled gap
            # Loops from the current point until the first following point
            # that does not overlap with the filled gap
            for j in range(i, len(points)):
                # print(list(filled_gaps_line[-1].coords))
                # print(filled_gaps_line[-1].distance(points.loc[j]['geometry']))
                if filled_gaps_line[-1].distance(points.loc[j]['geometry']) < 1e-8:
                    points.at[j, 'geometry'] = Point(shortest_route_geo[-1])
                    # print((points.loc[j]['geometry'].x,points.loc[j]['geometry'].y))
                else:
                    break

    # Create a dataframe for the filled gaps
    temp_df = pd.DataFrame({'SerialID': gaps_orig_eps_id,
                            'OrigPointRecordID': gaps_orig_record_id,
                            'EdgesGapPassed': edges_gaps_passed,
                            'geometry': filled_gaps_line})
    # Convert the dataframe into a geodataframe
    filled_gaps_gdf = gpd.GeoDataFrame(temp_df, geometry='geometry')
    # Because the coordinates of some points in the input could be changed after filling the gaps,
    # we also need to return the points
    return points, filled_gaps_gdf

def filled_gap_edges(orig_point_serial_id, orig_point_record_id,
                        gap_route_points, network_pg, network_pe):
    """
    Returns a list which contains the IDs of edges in the network that the 
    route which fills the gap has passed through

    Parameters:
    orig_point_serial_id = The serial ID of the origin point of the gap
    orig_point_record_id = The record ID of the origin point of the gap
    filled_gap_route = The shortest route that was found to fill the gap detected
    network_pg = A Directed Graph object that is projected 
    and contains the data of the transportation network
    network_pn = A Geodataframe that contains the data of the nodes in the Directed Graph network_pg
    network_pe = A Geodataframe that contains the data of the edges in the Directed Graph network_pg
    """
    serial_id_list = []
    record_id_list = []
    for node in gap_route_points:
        serial_id_list.append(orig_point_serial_id)
        record_id_list.append(orig_point_record_id)

    gap_points_df = pd.DataFrame({'SerialID': serial_id_list,
                                  'RecordID': record_id_list,
                                  'geometry': gap_route_points})
    gap_points_gdf = gpd.GeoDataFrame(gap_points_df, geometry='geometry')
    network_epsg = network_pe.crs.to_epsg()
    gap_points_gdf = gap_points_gdf.set_crs(epsg=network_epsg)
    gap_points_on_net = map_point_to_network(gap_points_gdf, network_pg, network_pe)

    return list(gap_points_on_net['nearEdgeID'].value_counts().index)


def connect_points_and_filled_gaps(points, filled_gaps):
    """
    Returns a full route by connecting the input points and shortest routes 
    that were generated for filling gaps between GPS points.

    Parameters: 
    points = A Geodataframe that contains the data of GPS points of a trip trajectory
    filled_gaps = A Geodataframe that contains the data of filled detected gaps in a trip trajectory
    """
    # Coordinates of the points on the route
    route_points = []
    for i in range(len(points)):
        # Check if the 'SerialID','RecordID' combination of the current row
        # exists in the Geodataframe for filled gaps
        if np.any(np.all(points.loc[i][['SerialID', 'RecordID']].values == filled_gaps[['SerialID', 'OrigPointRecordID']].values,
                         axis=1)):
            # Find the row of Geodataframe for filled gaps,
            # and get the coordinates of the LineString on the row
            gap_row = filled_gaps[(filled_gaps['SerialID'] == points.loc[i]['SerialID']) &
                                  (filled_gaps['OrigPointRecordID'] == points.loc[i]['RecordID'])]
            # Add coordinates for the filled gap into route_points
            for coord in list(gap_row['geometry'].values[0].coords):
                # Make sure there is no consecutive duplicate points in the line
                # print(coord)
                if (len(route_points) > 0 and coord == route_points[-1]):
                    # print(route_points[-1])
                    continue
                route_points.append(coord)

        else:
            # if the point of the current row does not overlap on the last point
            # in route_points add its coordinates into route_points
            if (len(route_points) > 0 and
                    (points.loc[i]['geometry'].x, points.loc[i]['geometry'].y) != route_points[-1]):
                route_points.append(
                    (points.loc[i]['geometry'].x, points.loc[i]['geometry'].y))
            # if the point of the current row overlaps with the last point, ignore it
            else:
                continue

    # Generate a single LineString for the route
    route_line = LineString(route_points)

    return route_line
