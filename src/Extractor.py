import geopandas as gpd
from math import cos, sin, radians, sqrt, asin

class Extractor:
    def __init__(self, episode_data=None):
        self.trip_segments = self.extract_trip_segments(episode_data)
        self.activity_locations = self.extract_activity_locations(episode_data)

    # Extracts data with modes that are either "Walk" or "Drive"
    def extract_trip_segments(self, episode_data):
        options = ['Walk', 'Drive']
        return episode_data[episode_data["MODES"].isin(options)]
    
    def distance(self, p1, p2):
        
        # convert from degrees to radian
        lon1 = radians(p1.x)
        lon2 = radians(p2.x)
        lat1 = radians(p1.y)
        lat2 = radians(p2.y)
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    
        c = 2 * asin(sqrt(a))
        
        # radius of earth in meters
        r = 6378137

        return c * r

    # Processes trip segments to make the distance between adjacent points >= 5m
    def relax_trip(self):
        start = 0
        dropped = []
        min_dist = 5
        for index,row in self.trip_segments.iterrows():
            point = row["geometry"] 
            if (not start):
                start = point
                continue
            # do not want to drop last row even if it violates the min distance
            if (index == self.trip_segments.shape[0]):
                break
            if (self.distance(start, point) < min_dist):
                dropped.append(index)
            else:
                start = point
        self.trip_segments.drop(dropped)

    def get_trip_segments(self):
        return self.trip_segments

    # Extracts data with modes that is "Stop"
    def extract_activity_locations(self, episode_data):
        return episode_data[episode_data["MODES"] == "Stop"]

    def get_activity_locations(self):
        return self.activity_locations
