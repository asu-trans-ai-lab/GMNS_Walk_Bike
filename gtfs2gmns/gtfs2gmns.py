'''Read Transit Files
required gtfs data : stop.txt, route.txt, trip.txt, stop_times.txt
'''
import os
import math
import datetime
import numpy as np
import pandas as pd
from python import readtxt, LLs2Dist, convert_time_sequence, time_convert, time_calculate, time

'''read files'''
os.getcwd()
os.chdir('data')

df_stops = readtxt('stops')
df_routes = readtxt('routes')
df_trips = readtxt('trips')
df_stoptimes = readtxt('stop_times')


'''build node.csv'''
node_csv = pd.DataFrame()

node_csv['name'] = df_stops['stop_id']
node_csv['x_coord'] = df_stops['stop_lon']
node_csv['y_coord'] = df_stops['stop_lat']
node_csv['node_type'] = None
node_csv['ctrl_type'] = None
node_csv['zone_id'] = None
node_csv['geometry'] = "POINT (" + df_stops['stop_lon'] + " " + df_stops['stop_lat'] +")"
node_csv.index.name = 'node_id'
node_csv.index += 100001 #index from 0

node_csv.to_csv('node.csv')
print('node.csv done') 


'''build link.csv'''
node_csv = pd.read_csv('node.csv')
node_csv = node_csv.rename(columns={'name':'stop_id'})

combined_route = df_trips.merge(df_routes,on='route_id',how='left')
combined_stop = df_stoptimes.merge(node_csv,on='stop_id',how='left' )
combined_trip = combined_stop.merge(df_trips,on='trip_id',how='left')

dataList_route = {}
gp = combined_route.groupby('trip_id')
for key, form in gp:
    dataList_route[key] = {
        'route_id': form['route_id'].values[0],
        'route_id_short_name': form['route_long_name'].values[0]
        }


dataList_trip = {}
gp = combined_trip.groupby('trip_id')

for key, form in gp:
    temp = form['arrival_time']
    temp = convert_time_sequence(temp)
    dataList_trip[key] = {
        'route_id': form['route_id'].values[0],
        'from_node_id': form['node_id'].values[0],
        'to_node_id': form['node_id'].values[-1],
        'node_sequence': form['node_id'].tolist(),
        'time_sequence': temp
        }
# print('datalist done')


link_list = []
link_csv = pd.DataFrame()

node_x = node_csv['x_coord'].tolist()
node_y = node_csv['y_coord'].tolist()
node_id_list = node_csv['node_id'].tolist()

for key in dataList_trip.keys(): 
    # print(key)    
    active_node_sequence_size = len(dataList_trip[key]['node_sequence'])\
        
    for i in range(active_node_sequence_size-1):
        
        route_index = dataList_trip[key]['route_id']
        active_from_node_id = dataList_trip[key]['node_sequence'][i]
        active_to_node_id = dataList_trip[key]['node_sequence'][i+1]
        active_from_node_idx = node_id_list.index(active_from_node_id)
        active_to_node_idx = node_id_list.index(active_to_node_id)
        
        from_node_id_x = node_x[active_from_node_idx] ###
        from_node_id_y = node_y[active_from_node_idx]
        to_node_id_x = node_x[active_to_node_idx]
        to_node_id_y = node_y[active_to_node_idx]
        
        active_distance = LLs2Dist(from_node_id_x,from_node_id_y,to_node_id_x,to_node_id_y)
        active_geometry = 'LINESTRING (' + str(from_node_id_x)+' '+str(from_node_id_y)+', '+str(to_node_id_x)+' '+str(to_node_id_y)+')'
        
        link_list.append([route_index,active_from_node_id,active_to_node_id,active_distance,active_geometry])

link_csv = pd.DataFrame(link_list, columns=['name','from_node_id','to_node_id','length','geometry']).drop_duplicates()    

link_csv['facility_type'] = None
link_csv['link_type'] = 1
link_csv['dir_flag'] = 1
link_csv['lanes'] = 1
link_csv['free_speed'] = 65
link_csv['capacity'] = 1900
link_csv['main_node_id'] = None
link_csv['movement_str'] = None
link_csv['NEMA_phase_number'] = None    
    
link_csv.index.name = 'link_id'
link_csv.index += 0
link_csv.to_csv('link.csv')   
print('link.csv done') 
 

'''build agent.csv'''
agent_csv = pd.DataFrame()
length_temp = np.array(link_csv['length'])
from_node_temp = np.array(link_csv['from_node_id'])
to_node_temp = np.array(link_csv['to_node_id'])

for key in dataList_trip.keys(): #key:string
    active_length_list = []
    # key = str(13878908)
    # print(key)
    flag = 1

    active_node_sequence_size = len(dataList_trip[key]['node_sequence'])
    for i in range(active_node_sequence_size-1):
        active_from_node_id = dataList_trip[key]['node_sequence'][i]
        active_to_node_id = dataList_trip[key]['node_sequence'][i+1]
        temp1 = np.array(from_node_temp == active_from_node_id)
        temp2 = np.array(to_node_temp == active_to_node_id)
        temp = temp1 & temp2
        if not any(temp2):
            flag = 0
            break
        
        active_length = length_temp[temp2]
        active_length = active_length[0]
        active_length_list.append(active_length)
          
    if flag == 1:
        active_length = sum(active_length_list) 
        active_time_sequence = dataList_trip[key]['time_sequence']
        active_time_first_temp = dataList_trip[key]['time_sequence'][0]
        active_time_last_temp = dataList_trip[key]['time_sequence'][-1]
        active_time=time(active_time_first_temp, active_time_last_temp)

        node_sequence_str = list(map(str, dataList_trip[key]['node_sequence']))
        node_sequence_temp = ';'.join(node_sequence_str)+';'
        
        time_sequence_temp = ';'.join(active_time_sequence)+';'
        
        agent_csv = agent_csv.append([{'agent_type':'transit', 'trip_id':key, 'route_id':dataList_trip[key]['route_id'],
                                'route_id_short_name':dataList_route[key]['route_id_short_name'],
                                'from_node_id':dataList_trip[key]['from_node_id'], 'to_node_id':dataList_trip[key]['to_node_id'],
                                'travel_time':active_time, 'distance':active_length,
                                'node_sequence':node_sequence_temp,
                                'time_sequence':time_sequence_temp}],ignore_index=True)

agent_csv.index.name = 'agent_id'
agent_csv.index += 0
agent_csv.to_csv('agent.csv')
print('agent.csv done')