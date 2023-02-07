"""
Module Name: Route Solver (module for map-matching and route generation algorithms)
Source Name: RouteSolver.py
Creator: Hongzhao Tan (tanh10@mcmaster.ca)
Requirements: Python 3.8 or later
Date Created: Jan 31, 2023
Last Revised: Jan 31, 2023
Description: Implements methods that are used to generate map-matched route or shortest path from GPS trajectory. A GPS trajectory
             consists of streams of points recorded by a GPS device that captures movement at a given period.

Version History:
2023-01-31 (RouteSolver.py)

2023-02-07 (RouteSolver.py) Update implementation of RouteChoiceGen and detectAndFillGap functions, to let the output of RouteChoiceGen
include the IDs of edges in the network dataset that the route generated has passed through
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import osmnx as ox
from shapely.geometry import Point, LineString

def RouteChoiceGen(trip, networkGraph, networkEdges, networkNodes):
    """
    Returns a Geodataframe where each row contais a route 
    by matching GPS trip trajectories onto the transportation network

    Parameters: 
    trip = A Geodataframe that contains the data of GPS points in trip trajectories
    networkGraph = A Directed Graph object that is projected and contains the data of the transportation network
    networkEdges = A Geodataframe that contains the data of the edges in the Directed Graph networkGraph
    networkNodes = A Geodataframe that contains the data of the nodes in the Directed Graph networkGraph
    """
    # Check if the trip Geodataframe contains the required columns 
    # and the required columns are of the required data types
    for colName in ['RecordID','SerialID','geometry']:
        if colName not in list(trip.columns):
            raise Exception("Necessary column missing in the input trip dataframe")
    if str(trip['geometry'].dtypes) != 'geometry':
        raise Exception("geometry column of the input trip dataframe is not of 'geometry' data type")

    networkEPSG = networkGraph.graph['crs'].to_epsg()
    # Find unique serial IDs extract trip segments with each unique serial ID
    uniqueSerials = list(trip['SerialID'].value_counts().index)
    # Initialize lists to contain generated routes
    routes = []
    # Initialize list of lists that contains IDs of edges each of the routes has on
    edgesRoutePassed = []
    for serialID in uniqueSerials:
        # extract trip segments with each unique serial ID
        currSerialPoints = trip[trip['SerialID'] == serialID]
        # Matching points to the network data
        pointsOnNet = mapPointToNetwork(currSerialPoints, networkGraph, networkEdges)
        # Because the matched points have not been projected to any CRS yet, 
        # we need to first project them to the CRS of the network dataset 
        pointsOnNet = pointsOnNet.set_crs(epsg=networkEPSG)
        
        # Detecting gaps between the points and fill the gaps
        pointsOnNet, filledGaps = detectAndFillGap(pointsOnNet, networkGraph, networkNodes, networkEdges)

        # Then project to the global geographic CRS with EPSG number 4326 
        # for future visualizing the matched points
        pointOnNetGeoCRS=pointsOnNet.to_crs(epsg=4326)
        # Same as the points, we need to set the CRS for the filled gaps
        filledGaps = filledGaps.set_crs(epsg=networkEPSG)
        filledGapsGeoCRS=filledGaps.to_crs(epsg=4326)

        # Connecting the matched points and the filled gaps to generate full route for the trip segment
        routes.append(connectPointsAndFilledGaps(pointOnNetGeoCRS, filledGapsGeoCRS))

        # Get all IDs of unique edges the route generated for current trip segment has passed through
        tmpEdgeIDsSet = set(pointOnNetGeoCRS['nearEdgeID'].value_counts().index)
        for i in range(len(filledGaps)):
            tmpSet = set(filledGaps.loc[i]['EdgesGapPassed'])
            tmpEdgeIDsSet = tmpEdgeIDsSet.union(tmpSet)
        edgesRoutePassed.append(tmpEdgeIDsSet)

    tempDf = pd.DataFrame({'SerialID': uniqueSerials,
                           'edgesRoutePassed': edgesRoutePassed,
                           'geometry': routes})
    routesGdf = gpd.GeoDataFrame(tempDf, geometry='geometry')
    return routesGdf

def mapPointToNetwork(points, networkPG, networkPE):
    """
    Returns a Geodataframe of points in a trip segment matched onto the transportation network

    Parameters: 
    points = A Geodataframe that contains the data of GPS points of a trip trajectory 
    networkPG = A Directed Graph object that is projected and contains the data of the transportation network
    networkPE = A Geodataframe that contains the data of the edges in the Directed Graph networkPG
    """
    # Coordinates of points after matching
    pointOnNet = []
    # The edge IDs of the edges that each of the matched points is on
    nearEdgesID = []
    # The edge names of the edges that each of the matched points is on
    nearEdgesName = []
    # Coordinates of the leg(a straight line segment in an edge) that each of the matched points is on
    nearLegsGeo = []

    # Project the sample GPS points to the same CRS as the network dataset
    networkEPSG = networkPE.crs.to_epsg()
    points = points.to_crs(networkEPSG)

    # Finding the nearest edge for every sample GPS point and take the edges' IDs
    for point in points['geometry']:
        nearEdge = ox.distance.nearest_edges(networkPG, point.x, point.y, return_dist=True)
        #print(networkE.loc[nearEdge[0]]['name'])
        nearEdgesID.append(nearEdge[0])
        #nearEdgesDist.append(nearEdge[1])

    # For the each sample GPS point, find the nearest leg on its nearest edges, 
    # and find the nearest point on the nearest leg to the sample GPS point
    for i in range(len(nearEdgesID)):
        if (i >= 1) and (i < (len(nearEdgesID)-1)):
            # If current GPS point is on a different street from the following and the former GPS points
            # and the following and the former GPS points are on the same street
            # current GPS point could be crossing an interesction of two streets
            if ((networkPE.loc[nearEdgesID[i-1]]['name'] == networkPE.loc[nearEdgesID[i+1]]['name']) 
                and (networkPE.loc[nearEdgesID[i]]['name'] != networkPE.loc[nearEdgesID[i+1]]['name'])):
                nearEdgesID[i] = nearEdgesID[i-1]
        
        # Get the coordinates of the nearest edge of current GPS point 
        nearEdgesName.append(networkPE.loc[nearEdgesID[i]]['name'])
        nearEdgeGeo = networkPE.loc[nearEdgesID[i]]['geometry']
        nearEdgeCoord = list(nearEdgeGeo.coords)
        
        # find the nearest leg on the nearest edge of current GPS point
        nearLeg = LineString([nearEdgeCoord[0],nearEdgeCoord[1]])
        nearLegDist = nearLeg.distance(points['geometry'][i])
        for i in range(1, len(nearEdgeCoord)-1):
            currLeg = LineString([nearEdgeCoord[i],nearEdgeCoord[i+1]])
            currDist = currLeg.distance(points['geometry'][i])
            if currDist < nearLegDist:
                nearLeg = currLeg
        # find the nearest point on the nearest leg to the sample GPS point
        pointOnNet.append(nearLeg.interpolate(nearLeg.project(point)))
        nearLegsGeo.append(nearLeg)

    # Create a dataframe for the points after matching
    tempDf = pd.DataFrame({'SerialID': list(points['SerialID']),
                        'RecordID': list(points['RecordID']),
                        'nearEdgeID': nearEdgesID,
                        'nearEdgeName': nearEdgesName,
                        'nearLeg': nearLegsGeo,
                        'geometry': pointOnNet})

    # Convert the dataframe into a geodataframe
    pointsOnNetGdf = gpd.GeoDataFrame(tempDf, geometry='geometry')
    return pointsOnNetGdf

def detectAndFillGap(points, networkPG, networkPN, networkPE):
    """
    Detects gaps from GPS points in trip trajectory 
    and returns a Geodataframe where each row contains a route 
    that is generated using shortest path algorithms and fills a detected gap

    Parameters: 
    points = A Geodataframe that contains the data of GPS points of a trip trajectory
    networkPG = A Directed Graph object that is projected and contains the data of the transportation network
    networkPN = A Geodataframe that contains the data of the nodes in the Directed Graph networkPG
    """
    # The track IDs of the start points of the gaps
    gapsOrigRecordID = []
    # The episode IDs of the start points of the gaps
    gapsOrigEpsID = []
    # The shortest routes that fill the gaps
    filledGapsLine = []
    # The Edges on the network the filled gaps has passed
    edgesGapsPassed = []
    # For each pair of adjacent matched points, check if there is a gap between them and fill the gap if found
    for i in range(1,len(points)):
        # Gap exists when the two adjacent points are not on the same edge in the network dataset 
        # and the distance between them exceeds 50 meters.
        if ((points.loc[i-1]['nearEdgeID'] != points.loc[i]['nearEdgeID']) 
            and points.loc[i-1]['geometry'].distance(points.loc[i]['geometry']) > 50):
            #print((points.loc[i-1]['RecordID'], points.loc[i]['RecordID']))
            #print(points.loc[i-1]['geometry'].distance(points.loc[i]['geometry']))
            # Get the track ID and episode ID of the start point of the gap
            gapsOrigRecordID.append(points.loc[i-1]['RecordID'])
            gapsOrigEpsID.append(points.loc[i-1]['SerialID'])
            
            # Find the two nodes in the network dataset that are nearest to the start and end points of the gap respectively
            startNode = ox.distance.nearest_nodes(networkPG, points.loc[i-1]['geometry'].x,points.loc[i-1]['geometry'].y)
            endNode = ox.distance.nearest_nodes(networkPG, points.loc[i]['geometry'].x,points.loc[i]['geometry'].y)
            # Find the shortest route between the two nodes found
            shortestRoute = ox.distance.shortest_path(networkPG,
                                                      startNode,
                                                      endNode,
                                                      weight='length')
            #print(shortestRoute)
            # Get the coordinates of the nodes on the shortest route
            shortestRouteGeo = [(networkPN.loc[nodeID]['geometry'].x, networkPN.loc[nodeID]['geometry'].y) 
                                for nodeID in shortestRoute]
            #print(shortestRouteGeo)

            # Get the IDs of edges in the network that the filled gap has passed through
            epsIDList = []
            recordIDList = []
            for node in shortestRouteGeo:
                epsIDList.append(points.loc[i-1]['SerialID'])
                recordIDList.append(points.loc[i-1]['RecordID'])
                
            shortestRouteNodes = [networkPN.loc[nodeID]['geometry'] for nodeID in shortestRoute]
            gapPointsDf = pd.DataFrame({'SerialID': epsIDList,
                                        'RecordID': recordIDList,
                                        'geometry': shortestRouteNodes})
            gapPointsGdf = gpd.GeoDataFrame(gapPointsDf, geometry='geometry')
            networkEPSG = networkPE.crs.to_epsg()
            gapPointsGdf = gapPointsGdf.set_crs(epsg=networkEPSG)
            gapPointsOnNet = mapPointToNetwork(gapPointsGdf, networkPG, networkPE)
            edgesGapsPassed.append(list(gapPointsOnNet['nearEdgeID'].value_counts().index))
            
            # Connect the coordinates of the nodes on the shortest route into one LineString
            filledGapsLine.append(LineString(shortestRouteGeo))
            
            # Check to see if the filled gap went over following points, 
            # if yes, change the overlapped points' coordinates to the end of the filled gap
            # Loops from the current point until the first following point that does not overlap with the filled gap
            for j in range(i, len(points)):
                #print(list(filledGapsLine[-1].coords))
                #print(filledGapsLine[-1].distance(points.loc[j]['geometry']))
                if filledGapsLine[-1].distance(points.loc[j]['geometry']) < 1e-8:
                    points.at[j,'geometry'] = Point(shortestRouteGeo[-1])
                    #print((points.loc[j]['geometry'].x,points.loc[j]['geometry'].y))
                else:
                    break

    # Create a dataframe for the filled gaps 
    tempDf = pd.DataFrame({'SerialID': gapsOrigEpsID,
                           'OrigPointRecordID': gapsOrigRecordID,
                           'EdgesGapPassed': edgesGapsPassed,
                           'geometry': filledGapsLine})
    # Convert the dataframe into a geodataframe
    filledGapsGdf = gpd.GeoDataFrame(tempDf, geometry='geometry')
    # Because the coordinates of some points in the input could be changed after filling the gaps, 
    # we also need to return the points
    return points, filledGapsGdf

def connectPointsAndFilledGaps(points, filledGaps):
    """
    Returns a full route by connecting the input points and shortest routes 
    that were generated for filling gaps between GPS points.
    
    Parameters: 
    points = A Geodataframe that contains the data of GPS points of a trip trajectory
    filledGaps = A Geodataframe that contains the data of filled detected gaps in a trip trajectory
    """
    # Coordinates of the points on the route
    routePoints = []
    for i in range(len(points)):
        # Check if the 'SerialID','RecordID' combination of the current row exists in the Geodataframe for filled gaps
        if np.any(np.all(points.loc[i][['SerialID','RecordID']].values 
                        == filledGaps[['SerialID','OrigPointRecordID']].values, axis=1)):
            # Find the row of Geodataframe for filled gaps, and get the coordinates of the LineString on the row
            gapRow = filledGaps[(filledGaps['SerialID'] == points.loc[i]['SerialID']) 
                                        & (filledGaps['OrigPointRecordID'] == points.loc[i]['RecordID'])]
            # Add coordinates for the filled gap into routePoints
            for coord in list(gapRow['geometry'].values[0].coords):
                # Make sure there is no consecutive duplicate points in the line
                #print(coord)
                if (len(routePoints) > 0 and coord == routePoints[-1]):
                    #print(routePoints[-1])
                    continue
                routePoints.append(coord)    
                
        else:
            # if the point of the current row does not overlap on the last point in routePoints add its coordinates into routePoints
            if (len(routePoints) > 0 
                and (points.loc[i]['geometry'].x,points.loc[i]['geometry'].y) != routePoints[-1]):
                routePoints.append((points.loc[i]['geometry'].x,points.loc[i]['geometry'].y))
            # if the point of the current row overlaps with the last point, ignore it
            else:
                continue

    # Generate a single LineString for the route
    routeLine = LineString(routePoints)
    
    return routeLine