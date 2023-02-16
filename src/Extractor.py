import geopandas as gpd
import pandas as pd
from math import cos, sin, radians, sqrt, asin


class Extractor:
    def __init__(self, episode_data, processed_data):
        self.fill_points(episode_data, processed_data)
        self.trip_segments = self.relax_trip(self.extract_trip_segments(episode_data))
        self.activity_locations = self.extract_activity_locations(episode_data)

    # Extracts data with modes that are either "Walk" or "Drive"
    def extract_trip_segments(self, episode_data):
        options = ['Walk', 'Drive']
        data = episode_data[episode_data["Modes"].isin(options)]
        return data.reset_index(drop=True, inplace=True)

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

    # add points between each detected mode with points from processed data
    def fill_points(self, episode_data, processed_data):
        length = len(episode_data.index) - 1
        add = gpd.GeoDataFrame()
        for index, row in episode_data.iterrows():
            mode = row["Modes"]
            record_id = row["RecordID"]
            serial_ids = []
            record_ids = []
            start_times = []
            modes = []
            geometry = []
            # fill points until next mode
            if (index != length):
                next_record_id = episode_data[index +
                                              1:index + 2]['RecordID'].iloc[0]
                filtered_data = processed_data.loc[(processed_data['RecordID'] > record_id) & (
                    processed_data['RecordID'] < next_record_id)]
                for index, row in filtered_data.iterrows():
                    serial_ids.append(row["SerialID"])
                    record_ids.append(row['RecordID'])
                    start_times.append(row["LocalTime"])
                    modes.append(mode)
                    geometry.append(row['geometry'])
                data = {'SerialID': serial_ids,
                        'RecordID': record_ids,
                        'TimeStart': start_times,
                        'Modes': modes,
                        'geometry': geometry}
                add = pd.concat([add, gpd.GeoDataFrame(data)],
                                ignore_index=True)
            # fill points until end
            else:
                filtered_data = processed_data.loc[processed_data['RecordID'] > record_id]
                for index, row in filtered_data.iterrows():
                    serial_ids.append(row["SerialID"])
                    record_ids.append(row['RecordID'])
                    start_times.append(row["LocalTime"])
                    modes.append(mode)
                    geometry.append(row['geometry'])
                data = {'SerialID': serial_ids,
                        'RecordID': record_ids,
                        'TimeStart': start_times,
                        'Modes': modes,
                        'geometry': geometry}
                episode_data = pd.concat(
                    [episode_data, add, gpd.GeoDataFrame(data)]).sort_values(by=['RecordID'])

        episode_data.reset_index(drop=True, inplace=True)

    # Processes trip segments to filter out points with distances <5m
    def relax_trip(self, data):
        start = 0
        dropped = []
        min_dist = 5
        for index, row in data.iterrows():
            point = row["geometry"]
            if (not start):
                start = point
                continue
            if (self.distance(start, point) < min_dist):
                dropped.append(index)
            else:
                start = point
        data = data.drop(dropped)
        return data.reset_index(drop=True, inplace=True)

    def get_trip_segments(self):
        return self.trip_segments

    # Extracts data with modes that is "Stop"
    def extract_activity_locations(self, episode_data):
        data = episode_data[episode_data["Modes"] == "Stop"]
        return data.reset_index(drop=True, inplace=True)
