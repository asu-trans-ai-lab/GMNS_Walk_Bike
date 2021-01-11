import math
import datetime
import numpy as np
import pandas as pd

#read files
def readtxt(filename):
    Filepath = filename +'.txt'
    data = []
    with open(Filepath, 'r') as f:
        for line in f.readlines():
            data.append(line.split('\n')[0].split(','))
    df_data = pd.DataFrame(data[1:], columns=data[0])
    return df_data

#distance
def LLs2Dist(lon1, lat1, lon2, lat2): #WGS84 transfer coordinate system to distance(mile) #xy
    R = 6371
    dLat = (lat2 - lat1) * math.pi / 180.0
    dLon = (lon2 - lon1) * math.pi / 180.0

    a = math.sin(dLat / 2) * math.sin(dLat/2) + math.cos(lat1 * math.pi / 180.0) * math.cos(lat2 * math.pi / 180.0) * math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    dist = R * c * 0.621371
    return dist

#time
def convert_time_sequence(time_sequence): #change format: 13:22:00 --> 1322:00
    time = []
    for i in np.unique(time_sequence):
        i=i.replace(':', '', 1)
        time.append(i)
    return time

def time_convert(input_time): #time format in GTFS is not standard, need convert: 25:00:00 --> 01:00:00
    hour = int(input_time[:-5])
    hour = hour%24
    output_time = str(hour)+input_time[-5:]
    return output_time

def time_calculate(time1,time2): #calculate the time delta
    time_a = datetime.datetime.strptime(time1, '%H%M:%S')
    time_b = datetime.datetime.strptime(time2, '%H%M:%S')
    flag = (time_b<time_a)
    active_time = (time_b-time_a).total_seconds()/60 + 1440*flag #min
    return active_time

def time(time1,time2): 
    time_a = time_convert(time1)
    time_b = time_convert(time2)
    delta = time_calculate(time_a,time_b)
    return delta