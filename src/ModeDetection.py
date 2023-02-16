import geopandas as gpd
from math import cos, sin, radians, sqrt, asin, floor
import re
import datetime


class ModeDetection:
    def __init__(self, processed_data=None):
        self.episode_data = self.detect_modes(processed_data)

    def distance(self, p1, p2):
        """
        Gets distance between two points in meters
        Parameters:
        p1: Point object with longitude, latitude
        p2: Point object with longitude, latitude
        """

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

    def calc_time_acc(self, data):
        """
        Gets seconds travelled at each minute segment and acceleration
        Parameters:
        data: A Geodataframe that contains the filtered and smoothed data of GPS points
        """
        seconds = []
        acc = []
        zeros = []
        marker = []
        segment_time = 0
        last_index = len(data.index) - 1
        for index, row in data.iterrows():
            curr_min = row["LocalTime"][-2:]
            # since no time can be determined on Stops, approximation is made
            if (index == 0):
                start_min = curr_min
            # if no zeros in segment, no need to do anything
            elif (curr_min != start_min):
                if (zeros):
                    avg_Stop_time = (max(59.99, segment_time) -
                                     segment_time) / len(zeros)
                    for i in zeros:
                        seconds[i] = avg_Stop_time
                        next_speed = data[i + 1:i +
                                          2]['Speed_kmh'].iloc[0] * 5 / 18
                        if (avg_Stop_time != 0):
                            acc[i] = next_speed / avg_Stop_time

                start_min = curr_min
                segment_time = 0
                zeros = []
                marker.append(index)

            cur_speed = row['Speed_kmh'] * 5 / 18
            if (cur_speed == 0):
                seconds.append(0)
                acc.append(0)
                zeros.append(index)
                continue
            cur = row['geometry']
            next = data[index + 1:index + 2]['geometry']
            time = self.distance(cur, next) / (cur_speed)
            seconds.append(time)
            segment_time = segment_time + time
            if (index == last_index):
                acc.append(0)
            else:
                next_speed = data[index + 1:index +
                                  2]['Speed_kmh'].iloc[0] * 5 / 18
                acc.append(abs(cur_speed - next_speed) / time)

        # summing consecutive seconds in each minute segment
        sum = 0
        mark = marker.pop(0)
        for i in range(len(seconds)):
            if (i == mark):
                sum = 0
                if (marker):
                    mark = marker.pop(0)
            sum += seconds[i]
            seconds[i] = sum

        return [seconds, acc]

    def detect_modes(self, processed_data):
        """
        Returns a Geodataframe where each row contains a trip segment, with a labelled mode
        Parameters:
        processed_data= A Geodataframe that contains the filtered and smoothed data of GPS points
        """

        # initialize variables for main loop
        stage_points = {}
        prev_time = 0
        episode_len = 0
        episode_lens = []
        temp_episode_len = 0
        temp_stop_episode_len = 0
        start_index = 0
        ep_id = 0
        last_drive_index = -1
        valid_stop = True
        last_walk_index = -1
        last = len(processed_data.index) - 1

        # gets seconds travelled between each minute of the data
        [seconds, acc] = self.calc_time_acc(processed_data)

        # iterate over geodataframe
        for index, row in processed_data.iterrows():

            # determine mode based on speed thresholds
            speed = float(row['Speed_kmh'])
            if (0.36 <= speed <= 10.008):
                new_mode = 'Walk'
            elif (speed < 0.36):
                new_mode = 'Stop'
            elif (speed > 10.008):
                new_mode = 'Drive'

            # get time difference between two points and calculate length of each stage
            pattern = '(\d+)\/(\d+)\/(\d+)\s(\d+):(\d\d)'
            match = re.search(pattern, row['LocalTime'])
            # inaccuracies in distance and speed can cause impossible times
            second = min(floor(seconds[index]), 59)
            microseconds = min(floor((seconds[index] - second)*10**6), 999999)
            cur_time = datetime.datetime(second=second, microsecond=microseconds, year=int(match.groups()[2]), month=int(
                match.groups()[0]), day=int(match.groups()[1]), hour=int(match.groups()[3]), minute=int(match.groups()[4]))
            if index == 0:
                cur_mode = new_mode
                prev_time = cur_time
            time_difference = (cur_time - prev_time).total_seconds()
            prev_time = cur_time
            episode_len += time_difference
            episode_lens.append(episode_len)

            # if there is a gap between two points, create one or two episodes
            # First episode: create if points before gap are a valid episode
            # Second episode: create stop episode from gap
            if (time_difference >= 120):
                if (len(episode_lens) > 2 and ((cur_mode == 'Drive' and episode_lens[index-2] >= 120) or (cur_mode == 'Walk' and episode_lens[index-2] >= 60) or (cur_mode == 'Stop' and episode_lens[index-2] >= 120))):
                    ep_id += 1
                    stage_points[ep_id] = {}
                    stage_points[ep_id]['start'] = start_index
                    stage_points[ep_id]['end'] = index-2
                    stage_points[ep_id]['mode'] = cur_mode
                else:
                    if ep_id != 0:
                        stage_points[ep_id]['end'] = index-2

                ep_id += 1
                stage_points[ep_id] = {}
                stage_points[ep_id]['start'] = index - 1
                stage_points[ep_id]['end'] = index
                stage_points[ep_id]['mode'] = 'Stop'

                episode_len = 0
                start_index = index + 1
                cur_mode = 'Stop'

            # if last index, create episode if valid
            elif (index == last):
                if ((cur_mode == 'Drive' and episode_len >= 120) or (cur_mode == 'Walk' and episode_len >= 60) or (cur_mode == 'Stop' and episode_len >= 120)):
                    ep_id += 1
                    stage_points[ep_id] = {}
                    stage_points[ep_id]['start'] = start_index
                    stage_points[ep_id]['end'] = index
                    stage_points[ep_id]['mode'] = cur_mode
            else:
                # if the mode of travel is detected as switched, potentially create a new episode
                if (new_mode != cur_mode):
                    # If driving and a new mode of walk/stop is detected, don't switch the mode immediately. keep track of how long this potential
                    # walk/stop episode is until the episode is valid, then create a new driving episode and switch mode
                    if (new_mode != 'Drive' and cur_mode == 'Drive'):
                        if (last_drive_index < 0):
                            last_drive_index = index - 1
                            temp_episode_len = 0

                        if (speed >= 0.36):
                            valid_stop = False

                        temp_episode_len += time_difference
                        if ((not valid_stop and temp_episode_len >= 120) or (valid_stop and temp_episode_len >= 60)):
                            ep_id += 1
                            stage_points[ep_id] = {}
                            stage_points[ep_id]['start'] = start_index
                            stage_points[ep_id]['end'] = last_drive_index
                            stage_points[ep_id]['mode'] = 'Drive'
                            start_index = last_drive_index + 1
                            last_drive_index = -1
                            episode_len = temp_episode_len
                            cur_mode = new_mode
                            valid_stop = True

                    # If walking and a new mode of drive is detected, don't switch the mode immediately. keep track of how long this potential
                    # stop episode is until the episode is valid, then create a new walking episode and switch mode
                    elif (new_mode == 'Stop' and cur_mode == 'Walk'):
                        if (last_walk_index < 0):
                            last_walk_index = index - 1
                            temp_stop_episode_len = 0

                        temp_stop_episode_len += time_difference
                        if (temp_stop_episode_len >= 120):
                            ep_id += 1
                            stage_points[ep_id] = {}
                            stage_points[ep_id]['start'] = start_index
                            stage_points[ep_id]['end'] = last_walk_index
                            stage_points[ep_id]['mode'] = 'Walk'
                            start_index = last_walk_index + 1
                            last_walk_index = -1
                            episode_len = temp_stop_episode_len
                            cur_mode = new_mode

                    # If walking or stopping and a new mode detected, switch modes, and check if the current walking/stopping episode is valid
                    elif ((new_mode != 'Walk' and cur_mode == 'Walk') or (new_mode != 'Stop' and cur_mode == 'Stop')):
                        if ((cur_mode == 'Walk' and episode_len >= 60) or (cur_mode == 'Stop' and episode_len >= 120)):
                            ep_id += 1
                            stage_points[ep_id] = {}
                            stage_points[ep_id]['start'] = start_index
                            stage_points[ep_id]['end'] = index - 1
                            stage_points[ep_id]['mode'] = cur_mode
                        else:
                            if (ep_id == 0):
                                stage_points[ep_id] = {}
                                stage_points[ep_id]['start'] = start_index
                                stage_points[ep_id]['end'] = index - 1
                                stage_points[ep_id]['mode'] = 'invalid'
                            if (ep_id != 0):
                                stage_points[ep_id]['end'] = index - 1

                        start_index = index
                        episode_len = 0
                        cur_mode = new_mode
                else:
                    # Reset variables if driving and a temporary walking/stopping episode was detected, but it was invalid
                    if temp_episode_len > 0:
                        last_drive_index = -1
                        temp_episode_len = 0
                        valid_stop = True
                    # Reset variables if walking and a temporary stopping episode was detected, but it was invalid
                    if temp_stop_episode_len > 0:
                        last_walk_index = -1
                        temp_stop_episode_len = 0

        serial_ids = []
        record_ids = []
        start_times = []
        modes = []
        geometry = []

        invalid_first_stage = False

        # add rows extracted from loop into gdf
        # if first episode is an invalid episode, add it to the second episode
        for value in stage_points.values():
            if value['mode'] == 'invalid':
                invalid_first_stage = True
                target = processed_data.iloc[value['start']]
            else:
                if (not invalid_first_stage):
                    target = processed_data.iloc[value['start']]
                else:
                    invalid_first_stage = False
                serial_ids.append(target.SerialID)
                record_ids.append(target.RecordID)
                start_times.append(target.LocalTime)
                modes.append(value['mode'])
                geometry.append(target.geometry)

        data = {'SerialID': serial_ids,
                'RecordID': record_ids,
                'TimeStart': start_times,
                'Modes': modes,
                'geometry': geometry}

        return gpd.GeoDataFrame(data)

    def get_episode_data(self):
        """
        Getter method for episode data from detect_modes
        """

        return self.episode_data
