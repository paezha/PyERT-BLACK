import geopandas as gpd
from math import cos, sin, radians, sqrt, asin, floor
import re
import datetime


class ModeDetection:
    def __init__(self, processed_data=None):
        self.episode_data = self.detect_modes(processed_data)

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

    # gets seconds travelled at each minute segment and acceleration
    def calc_time_acc(self, data):
        seconds = []
        acc = []
        zeros = []
        marker = []
        segment_time = 0
        last_index = len(data.index) - 1
        for index, row in data.iterrows():
            curr_min = row["LocalTime"][-2:]
            # since no time can be determined on stops, approximation is made
            if (index == 0):
                start_min = curr_min
            # if no zeros in segment, no need to do anything
            elif (curr_min != start_min):
                if (zeros):
                    avg_stop_time = (max(59.99, segment_time) -
                                     segment_time) / len(zeros)
                    for i in zeros:
                        seconds[i] = avg_stop_time
                        next_speed = data[i + 1:i +
                                          2]['Speed_kmh'].iloc[0] * 5 / 18
                        if (avg_stop_time != 0):
                            acc[i] = next_speed / avg_stop_time

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
        stage_points = {}
        pattern = '(\\d+)\\/(\\d+)\\/(\\d+)\\s(\\d+):(\\d+)'
        prev_time = 0
        episode_len = 0
        temp_episode_len = 0
        start_index = 0
        ep_id = 0
        valid_stop = False
        last_car_index = -1
        last = len(processed_data.index) - 1

        [seconds, acc] = self.calc_time_acc(processed_data)

        for index, row in processed_data.iterrows():
            speed = float(row['Speed_kmh'])
            if (speed <= 10.008):
                new_mode = 'walk/stop'
                if (speed > 0.36):
                    valid_stop = False
            elif (speed > 10.008):
                new_mode = 'car'

            pattern = '(\\d+)\\/(\\d+)\\/(\\d+)\\s(\\d+):(\\d\\d)'
            match = re.search(pattern, row['LocalTime'])
            # inaccuracies in distance and speed can cause impossible times
            second = min(floor(seconds[index]), 59)
            microseconds = floor((seconds[index] - second) * 10**6)
            cur_time = datetime.datetime(
                year=int(
                    match.groups()[2]), month=int(
                    match.groups()[0]), day=int(
                    match.groups()[1]), hour=int(
                    match.groups()[3]), minute=int(
                    match.groups()[4]), microsecond=microseconds, second=second)
            if index == 0:
                cur_mode = new_mode
                prev_time = cur_time
            time_difference = (cur_time - prev_time).total_seconds()
            prev_time = cur_time
            episode_len += time_difference

            if (time_difference > 120):
                ep_id += 1
                stage_points[ep_id] = {}
                stage_points[ep_id]['start'] = start_index
                stage_points[ep_id]['end'] = index
                if cur_mode == 'walk/stop' and valid_stop:
                    stage_points[ep_id]['mode'] = 'stop'
                elif cur_mode == 'walk/stop' and valid_stop == False:
                    stage_points[ep_id]['mode'] = 'walk'
                else:
                    stage_points[ep_id]['mode'] = 'car'

                episode_len = 0
                start_index = index + 1
                cur_mode = new_mode
            elif (index == last):
                if (cur_mode == 'car' and episode_len > 120):
                    ep_id += 1
                    stage_points[ep_id] = {}
                    stage_points[ep_id]['start'] = start_index
                    stage_points[ep_id]['end'] = index
                    stage_points[ep_id]['mode'] = 'car'
                elif (cur_mode == 'walk/stop' and episode_len > 60 and valid_stop == False):
                    ep_id += 1
                    stage_points[ep_id] = {}
                    stage_points[ep_id]['start'] = start_index
                    stage_points[ep_id]['end'] = index
                    stage_points[ep_id]['mode'] = 'walk'
                elif (cur_mode == 'walk/stop' and episode_len > 60 and valid_stop):
                    ep_id += 1
                    stage_points[ep_id] = {}
                    stage_points[ep_id]['start'] = start_index
                    stage_points[ep_id]['end'] = index
                    stage_points[ep_id]['mode'] = 'stop'
            else:
                if (new_mode != cur_mode):
                    # currently, no invalid car episodes
                    if (new_mode == 'walk/stop') and cur_mode == 'car':
                        if (last_car_index < 0):
                            last_car_index = index - 1
                            temp_episode_len = 0

                        temp_episode_len += time_difference
                        #print('temp_episode_len: ' + str(temp_episode_len))
                        if (temp_episode_len > 60):
                            ep_id += 1
                            stage_points[ep_id] = {}
                            stage_points[ep_id]['start'] = start_index
                            stage_points[ep_id]['end'] = last_car_index
                            stage_points[ep_id]['mode'] = 'car'
                            start_index = last_car_index + 1
                            last_car_index = -1
                            episode_len = temp_episode_len
                            cur_mode = new_mode
                    elif new_mode == "car" and (cur_mode == 'walk/stop'):
                        if ((episode_len > 60 and valid_stop)):  # valid stop
                            #print(f'valid episode ep_len: {episode_len} cur_mode: {cur_mode} new_mode: {new_mode}')
                            ep_id += 1
                            stage_points[ep_id] = {}
                            stage_points[ep_id]['start'] = start_index
                            stage_points[ep_id]['end'] = index - 1
                            stage_points[ep_id]['mode'] = 'stop'
                        elif ((episode_len > 60 and not valid_stop)):  # invalid stop, valid walk
                            #print(f'valid episode ep_len: {episode_len} cur_mode: {cur_mode} new_mode: {new_mode}')
                            ep_id += 1
                            stage_points[ep_id] = {}
                            stage_points[ep_id]['start'] = start_index
                            stage_points[ep_id]['end'] = index - 1
                            stage_points[ep_id]['mode'] = 'walk'
                        else:
                            #print(f'invalid episode')
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
                        valid_stop = True
                else:
                    if temp_episode_len > 0:
                        last_car_index = -1
                        temp_episode_len = 0

        serial_ids = []
        record_ids = []
        start_times = []
        modes = []
        geometry = []

        invalid_first_stage = False

        for key in stage_points:
            print(
                f"key: {key} start: {stage_points[key]['start']} end: {stage_points[key]['end']} mode: {stage_points[key]['mode']}")
            if stage_points[key]['mode'] == 'invalid':
                invalid_first_stage = True
                target = processed_data.iloc[stage_points[key]['start']]
            else:
                if (not invalid_first_stage):
                    target = processed_data.iloc[stage_points[key]['start']]
                serial_ids.append(target.SerialID)
                record_ids.append(target.RecordID)
                start_times.append(target.LocalTime)
                modes.append(stage_points[key]['mode'])
                geometry.append(target.geometry)

        data = {'EPISODEID': serial_ids,
                'RECORDID': record_ids,
                'TIMESTART': start_times,
                'MODES': modes,
                'geometry': geometry}

        return gpd.GeoDataFrame(data)

    def get_episode_data(self):
        return self.episode_data
