# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 05:20:00 2022

@author: Administrator
"""

import requests
import json
import pandas as pd 
import math
import csv
from math import pow
import numpy as np
import matplotlib.pyplot as plot

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# =============================================================================

# Login controller functions

#Get the token to access vMM information  -- via API
def authentication(username,password,aosip):
    url_login = "https://" + aosip + ":4343/v1/api/login"
    payload_login = 'username=' + username + '&password=' + password
    headers = {'Content-Type': 'application/json'}
    get_uidaruba = requests.post(url_login, data=payload_login, headers=headers, verify=False)

    if get_uidaruba.status_code != 200:
        print('Status:', get_uidaruba.status_code, 'Headers:', get_uidaruba.headers,'Error Response:', get_uidaruba.reason)
        uidaruba = "error"

    else:
        uidaruba = get_uidaruba.json()["_global_result"]['UIDARUBA']
        return uidaruba

#show command
def show_command(aosip,uidaruba,command):
    url_login = 'https://' + aosip + ':4343/v1/configuration/showcommand?command='+command+'&UIDARUBA=' + uidaruba
    aoscookie = dict(SESSION = uidaruba)
    AOS_response = requests.get(url_login, cookies=aoscookie, verify=False)
    
    if AOS_response.status_code != 200:
        print('Status:', AOS_response.status_code, 'Headers:', AOS_response.headers,'Error Response:', AOS_response.reason)
        AOS_response = 'error'

    else:
        AOS_response = AOS_response.json()
        
    return AOS_response

# =============================================================================

# Username & password & API

username='apiUser'
password='x564#kdHrtNb563abcde'
vMM_aosip='140.118.151.248'

# =============================================================================

# Login & get data

ap_iy = ['AP01','AP03','AP05','AP07']
print(ap_iy)
df = {} 

#Get the token to access vMM information  -- via API
token = authentication(username,password,vMM_aosip)

for ap in ap_iy:
    command = 'show+ap+monitor+ap-list+ap-name+IY_1F_'+ap
    list_ap_database = show_command(vMM_aosip,token,command)
    df[ap] = pd.DataFrame(list_ap_database['Monitored AP Table'])
    df[ap]['curr-rssi'] = pd.to_numeric(df[ap]['curr-rssi'])
    df[ap] = df[ap][(df[ap]['ap-type']!='valid')
                                        &(df[ap]['essid']!='eduroam')
                                        &(df[ap]['essid']!='sensor')
                                        &(df[ap]['essid']!='NTUST-PEAP')
                                        &(df[ap]['essid']!='NTUST-UAM')][['essid','bssid','curr-rssi','ap-type', 'chan']]
    df[ap] = df[ap][(df[ap]['curr-rssi']>0)&(df[ap]['curr-rssi']<60)]

ap1_int = df[ap_iy[0]]['bssid']
print('Number of interfering AP detected in AP1: ', ap1_int.count())

ap3_int = df[ap_iy[1]]['bssid']
print('Number of interfering AP detected in AP3: ', ap3_int.count())

ap5_int = df[ap_iy[2]]['bssid']
print('Number of interfering AP detected in AP5: ', ap5_int.count())

ap7_int = df[ap_iy[3]]['bssid']
print('Number of interfering AP detected in AP7: ', ap7_int.count())

# Group all the interfering APs on IY- 1F

ap13_int = pd.concat([ap1_int,ap3_int]).reset_index(drop=True).drop_duplicates()
ap57_int = pd.concat([ap5_int,ap7_int]).reset_index(drop=True).drop_duplicates()
ap_all_int = pd.concat([ap13_int,ap57_int]).reset_index(drop=True).drop_duplicates()
print('Total number of interfering APs detected in IY-1F:', ap_all_int.count())

ap_all = pd.DataFrame(ap_all_int).reset_index(drop=True)
ap_all['essid'], ap_all['ap type'], ap_all['channel'], ap_all[ap_iy[0]], ap_all[ap_iy[1]], ap_all[ap_iy[2]]= '','','',None,None,None
ap_all[ap_iy[3]] = None
# ap_all_int[ap_iy[4]] = None
ap_all['mon AP number'] = None

for i in range(len(ap_all)):
    no_ap = 0
    
    for ap in ap_iy:
        try:
        # Get essid
            ap_all['essid'][i] = list(df[ap][(df[ap]['bssid']==ap_all['bssid'][i])]['essid'])[0]
            ap_all['ap type'][i] = list(df[ap][(df[ap]['bssid']==ap_all['bssid'][i])]['ap-type'])[0]
            ap_all['channel'][i] = list(df[ap][(df[ap]['bssid']==ap_all['bssid'][i])]['chan'])[0]
        # Get rssi
            if df[ap]['bssid'].str.contains(ap_all['bssid'][i]).any():
                ap_all[ap][i] = -list(df[ap][df[ap]['bssid']==ap_all['bssid'][i]]['curr-rssi'])[0] 
                no_ap+=1
        except Exception:
            pass
    ap_all['mon AP number'][i] = no_ap
print('Interfering APs detected in IY-1F (with more than 1 RSSI values):')
ap_all = ap_all[(ap_all['mon AP number']>1)].sort_values('essid').reset_index(drop=True).drop_duplicates()


ap_all['xloc'], ap_all['yloc'] = '', ''
ap_all_int = ap_all['bssid']
print (df[ap])
# =============================================================================

# IY-1F APs location from WISE-PaaS (scale 1:100) => sc = 0.01

sc = 0.01

AP1_loc = (410.95816*sc, 600*sc)
AP3_loc = (488.56726*sc, 259.36988*sc)
AP5_loc = (613.29732*sc, 472.62618*sc)
AP7_loc = (893.28036*sc, 419.36988*sc)

# Function to get monitoring AP location and RSSI
def count_rssi(input_bssid):
    count_AP = 0
    neighbor_AP = []
    try: 
        rssi_1 = df[ap_iy[0]].loc[df[ap_iy[0]]['bssid'] == input_bssid]['curr-rssi'].item()
        if rssi_1 > 0:
            count_AP+=1
            neighbor_AP.append(AP1_loc)
            neighbor_AP.append(rssi_1)
    except:
        count_AP +=0
    try: 
        rssi_3 = df[ap_iy[1]].loc[df[ap_iy[1]]['bssid'] == input_bssid]['curr-rssi'].item()
        if rssi_3 > 0:
            count_AP+=1
            neighbor_AP.append(AP3_loc)
            neighbor_AP.append(rssi_3)
    except:
        count_AP +=0
    try: 
        rssi_5 = df[ap_iy[2]].loc[df[ap_iy[2]]['bssid'] == input_bssid]['curr-rssi'].item()
        if rssi_5 > 0:
            count_AP+=1
            neighbor_AP.append(AP5_loc)
            neighbor_AP.append(rssi_5)
        else:
            count_AP +=0
    except:
        count_AP +=0
    try: 
        rssi_7 = df[ap_iy[3]].loc[df[ap_iy[3]]['bssid'] == input_bssid]['curr-rssi'].item()
        if rssi_7 > 0:
            count_AP+=1
            neighbor_AP.append(AP7_loc)
            neighbor_AP.append(rssi_7)
    except:
        count_AP +=0
    return count_AP, neighbor_AP

ap_list = []
ap_list_2 = []
ap_list_4 = []
for i in ap_all_int:
    if count_rssi(i)[0]==3:
        ap_list.append(i)
    if count_rssi(i)[0]==2:
        ap_list_2.append(i)
    if count_rssi(i)[0]>3:
        ap_list_4.append(i)
        
# =============================================================================

# RSSI-based Distance calculation functions

# RSSI distance calculation function
# n: path loss exponent
# a: reference power (dB)
# w: walls attenuation (dB)
# k: number of walls 
# rssi: Tx power (P_d)
# cal_d: calculated distance (d)

n=3.185
a=-37.84
w=-7.1274
k = 0

def calc_dist(rssi,a,n,k,w):
    cal_d= pow(10,((rssi-a-k*w)/(-10*n)))
    return cal_d

# Distance between 2 points

def calculateDistance(x1,y1,x2,y2):  
     dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)  
     return dist 

# Trilateration algorithm
def trilateration(x1,y1,r1,x2,y2,r2,x3,y3,r3):
    A = 2*x2 - 2*x1
    B = 2*y2 - 2*y1
    C = r1**2 - r2**2 - x1**2 + x2**2 - y1**2 + y2**2
    D = 2*x3 - 2*x2
    E = 2*y3 - 2*y2
    F = r2**2 - r3**2 - x2**2 + x3**2 - y2**2 + y3**2
    x = (C*E - F*B) / (E*A - B*D)
    y = (C*D - A*F) / (B*D - A*E)
    return x,y

# Get intersection points
def get_intersections(x0, y0, r0, x1, y1, r1):
    # circle 1: (x0, y0), radius r0
    # circle 2: (x1, y1), radius r1

    d=math.sqrt((x1-x0)**2 + (y1-y0)**2)

    # non intersecting
    if d > r0 + r1 :
        return None
    # One circle within other
    if d < abs(r0-r1):
        return None
    # coincident circles
    if d == 0 and r0 == r1:
        return None
    else:
        a=(r0**2-r1**2+d**2)/(2*d)
        if r0**2 > a**2:
            h=math.sqrt(r0**2-a**2)
        else:
            h=math.sqrt(a**2-r0**2)
        x2=x0+a*(x1-x0)/d   
        y2=y0+a*(y1-y0)/d   

        x3=x2+h*(y1-y0)/d     
        y3=y2-h*(x1-x0)/d 

        x4=x2-h*(y1-y0)/d
        y4=y2+h*(x1-x0)/d

        return (x3, y3, x4, y4)

# =============================================================================

# 3 RSSI values

def indoor_trilateration_3(mac):

    d1 = calc_dist(-count_rssi(mac)[1][1], a, n, k, w)
    d2 = calc_dist(-count_rssi(mac)[1][3], a, n, k, w)
    d3 = calc_dist(-count_rssi(mac)[1][5], a, n, k, w)


    x1, y1, x2, y2, x3, y3 = (count_rssi(mac)[1][0][0], count_rssi(mac)[1][0][1], 
                      count_rssi(mac)[1][2][0], count_rssi(mac)[1][2][1], 
                      count_rssi(mac)[1][4][0], count_rssi(mac)[1][4][1])
    # for inside trilateration

    if d1 > (calculateDistance(x1, y1, x2, y2) + d2):
        d1 = calculateDistance(x1, y1, x2, y2) + d2
    if d1 > (calculateDistance(x1, y1, x3, y3) + d3):
        d1 = calculateDistance(x1, y1, x3, y3) + d3
    if d2 > (calculateDistance(x2, y2, x3, y3) +d3):
        d2 = calculateDistance(x2, y2, x3, y3) + d3
    if d2 > (calculateDistance(x2, y2, x1, y1) + d1):
        d2 = calculateDistance(x2, y2, x1, y1) + d1
    if d3 > (calculateDistance(x3, y3, x2, y2) + d2):
        d3 = calculateDistance(x3, y3, x2, y2) + d2 
    if d3 > (calculateDistance(x3, y3, x1, y1) + d1):
        d3 = calculateDistance(x3, y3, x1, y1) +d1

    # Get intersection location

    intersections_1 = get_intersections(x1, y1, d1, x2, y2, d2)
    intersections_2 = get_intersections(x1, y1, d1, x3, y3, d3)
    intersections_3 = get_intersections(x2, y2, d2, x3, y3, d3)


    # For weighted trilateration

    if intersections_1 and intersections_2 and intersections_3 is not None:
        i_x3, i_y3, i_x4, i_y4 = intersections_1 
        i1 = (i_x3, i_y3)
        i2 = (i_x4, i_y4)

        i_x3, i_y3, i_x4, i_y4 = intersections_2 
        i3 = (i_x3, i_y3)
        i4 = (i_x4, i_y4)

        i_x3, i_y3, i_x4, i_y4 = intersections_3
        i5 = (i_x3, i_y3)
        i6 = (i_x4, i_y4)

        # Find smallest area and apply min-max algorithm

        x_i = []
        y_i = []

        int_dis = []

        ### 1, 3, 5
        x_i.append((i1[0] + i3[0] + i5[0])/3)
        y_i.append((i1[1] + i3[1] + i5[1])/3)

        int_dis.append(calculateDistance(i1[0], i1[1], i3[0], i3[1]) + calculateDistance(i1[0], i1[1], i6[0], i6[1])+ calculateDistance(i3[0], i3[1], i6[0], i6[1]))

        ### 1, 3, 6
        x_i.append((i1[0] + i3[0] + i6[0])/3)
        y_i.append((i1[1] + i3[1] + i6[1])/3)

        int_dis.append(calculateDistance(i1[0], i1[1], i3[0], i3[1]) + calculateDistance(i1[0], i1[1], i6[0], i6[1])+ calculateDistance(i3[0], i3[1], i6[0], i6[1]))

        ### 1, 4, 5
        x_i.append((i1[0] + i4[0] + i5[0])/3)
        y_i.append((i1[1] + i4[1] + i5[1])/3)

        int_dis.append(calculateDistance(i1[0], i1[1], i4[0], i4[1]) + calculateDistance(i1[0], i1[1], i5[0], i5[1])+ calculateDistance(i4[0], i4[1], i5[0], i5[1]))

        ### 1, 4, 6
        x_i.append((i1[0] + i4[0] + i6[0])/3)
        y_i.append((i1[1] + i4[1] + i6[1])/3) 

        int_dis.append(calculateDistance(i1[0], i1[1], i4[0], i4[1]) + calculateDistance(i1[0], i1[1], i6[0], i6[1])+ calculateDistance(i4[0], i4[1], i6[0], i6[1]))

        ### 2, 3, 5
        x_i.append((i2[0] + i3[0] + i5[0])/3)
        y_i.append((i2[1] + i3[1] + i5[1])/3)

        int_dis.append(calculateDistance(i2[0], i2[1], i3[0], i3[1]) + calculateDistance(i2[0], i2[1], i5[0], i5[1])+ calculateDistance(i3[0], i3[1], i5[0], i5[1]))

        ### 2, 3, 6
        x_i.append((i2[0] + i3[0] + i6[0])/3)
        y_i.append((i2[1] + i3[1] + i6[1])/3)

        int_dis.append(calculateDistance(i2[0], i2[1], i3[0], i3[1]) + calculateDistance(i2[0], i2[1], i6[0], i6[1])+ calculateDistance(i3[0], i3[1], i6[0], i6[1]))

        ### 2, 4, 5
        x_i.append((i2[0] + i4[0] + i5[0])/3)
        y_i.append((i2[1] + i4[1] + i5[1])/3)

        int_dis.append(calculateDistance(i2[0], i2[1], i4[0], i4[1]) + calculateDistance(i2[0], i2[1], i5[0], i5[1])+ calculateDistance(i4[0], i4[1], i5[0], i5[1]))

        ### 2, 4, 6
        x_i.append((i2[0] + i4[0] + i6[0])/3)
        y_i.append((i2[1] + i4[1] + i6[1])/3)

        int_dis.append(calculateDistance(i2[0], i2[1], i4[0], i4[1]) + calculateDistance(i2[0], i2[1], i6[0], i6[1])+ calculateDistance(i4[0], i4[1], i6[0], i6[1]))

        for i in range(len(int_dis)):
            if int_dis[i] == min(int_dis):
                x = x_i[i]
                y = y_i[i]
    else:
        x,y = trilateration(x1,y1,d1,x2,y2,d2,x3,y3,d3)
        

    ap_all['xloc'][(ap_all['bssid']==mac)] = x/sc
    ap_all['yloc'][(ap_all['bssid']==mac)] = y/sc

    return x/sc, y/sc

# =============================================================================

# > 3 RSSI values

def indoor_trilateration_4(mac):
    d1 = calc_dist(-count_rssi(mac)[1][1], a, n, k, w)
    d2 = calc_dist(-count_rssi(mac)[1][3], a, n, k, w)
    d3 = calc_dist(-count_rssi(mac)[1][5], a, n, k, w)
    d4 = calc_dist(-count_rssi(mac)[1][7], a, n, k, w)

    x1, y1, x2, y2, x3, y3, x4, y4 = (count_rssi(mac)[1][0][0], count_rssi(mac)[1][0][1], 
                                      count_rssi(mac)[1][2][0], count_rssi(mac)[1][2][1], 
                                      count_rssi(mac)[1][4][0], count_rssi(mac)[1][4][1],
                                      count_rssi(mac)[1][6][0], count_rssi(mac)[1][6][1],)


    x_1, y_1 = trilateration(x1,y1,d1,x2,y2,d2,x3,y3,d3)
    x_2, y_2 = trilateration(x1,y1,d1,x2,y2,d2,x4,y4,d4)
    x_3, y_3 = trilateration(x1,y1,d1,x3,y3,d3,x4,y4,d4)
    x_4, y_4 = trilateration(x2,y2,d2,x3,y3,d3,x4,y4,d4)
    
    x, y = ((x_1 + x_2 + x_3 + x_4)/4, (y_1 + y_2 + y_3 + y_4)/4)
        

    ap_all['xloc'][(ap_all['bssid']==mac)] = x/sc
    ap_all['yloc'][(ap_all['bssid']==mac)] = y/sc

    return x/sc, y/sc

                        
# =============================================================================

# 2 RSSI values

def indoor_trilateration_2(mac):

    d1 = calc_dist(-count_rssi(mac)[1][1], a, n, k, w)
    d2 = calc_dist(-count_rssi(mac)[1][3], a, n, k, w)

    x1, y1, x2, y2 = (count_rssi(mac)[1][0][0], count_rssi(mac)[1][0][1], 
                        count_rssi(mac)[1][2][0], count_rssi(mac)[1][2][1])

    # for inside trilateration

    if d1 > (calculateDistance(x1, y1, x2, y2) + d2):
        d1 = calculateDistance(x1, y1, x2, y2) + d2 - 0.0001
    if d2 > (calculateDistance(x2, y2, x1, y1) + d1):
        d2 = calculateDistance(x2, y2, x1, y1) + d1 - 0.0001


    # For weighted trilateration

    intersections_1 = get_intersections(x1, y1, d1, x2, y2, d2)

    if intersections_1 is not None:
        i_x3, i_y3, i_x4, i_y4 = intersections_1 
        x_1, y_1 = (i_x3, i_y3)
        x_2, y_2 = (i_x4, i_y4)

    #For no intersection

    else:
        x_1 = (x1 + x2)*d1/(d1 +d2)
        y_1 = (y1 + y2)*d1/(d1 +d2)
        x_2 = (x1 + x2)*d1/(d1 +d2)
        y_2 = (y1 + y2)*d1/(d1 +d2)
    
    x = (x_1 + x_2)/2
    y = (y_1 + y_2)/2
    
    ap_all['xloc'][(ap_all['bssid']==mac)] = x/sc
    ap_all['yloc'][(ap_all['bssid']==mac)] = y/sc

    return x/sc, y/sc

# =============================================================================

# Run localization algorithm

for mac in ap_list:
    for i in range(len(ap_iy)):
        try:
            int_info = df[ap_iy[i]][df[ap_iy[i]]['bssid']==mac][['essid','bssid','ap-type','chan']]
        except Exception:
            pass
    x, y = indoor_trilateration_3(mac)
    


for mac in ap_list_4:
    for i in range(len(ap_iy)):
        try:
            int_info = df[ap_iy[i]][df[ap_iy[i]]['bssid']==mac][['essid','bssid','ap-type','chan']]
        except Exception:
            pass
    x, y = indoor_trilateration_4(mac)
    

for mac in ap_list_2:
    for i in range(len(ap_iy)):
        try:
            int_info = df[ap_iy[i]][df[ap_iy[i]]['bssid']==mac][['essid','bssid','ap-type','chan']]
        except Exception:
            pass
    x, y = indoor_trilateration_2(mac)
    
# =============================================================================

# Add datetime (GMT +8) and timestamp

import datetime
from datetime import timedelta

ts = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
ts = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fz")
ts
n = 8
# Subtract 8 hours from datetime object
ts = ts - timedelta(hours=n)
ts_tw_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
ts_tw = datetime.datetime.now()

data_json = json.loads(ap_all.to_json(orient='records'))

for i in range(len(data_json)):
    data_json[i]['ts'] = ts 
    data_json[i]['DatetimeStr'] = ts_tw_str
    data_json[i]['Datetime'] = ts_tw

# =============================================================================

data_json2 = json.loads(df[ap].to_json(orient='records'))

for i in range(len(data_json2)):
    try:
        data_json2[i]['curr_rssi'] = int(data_json2[i]['curr_rssi'])
    except Exception:
        pass
# Store json data to MongoDB
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import pymongo
from pymongo import MongoClient
import re

previous_day = datetime.now() - timedelta(days=30) 

client = MongoClient("140.118.70.40",27017)
db = client['AP']
col=db["RSSI"]
col.delete_many({"Datetime": {"$lt": previous_day}})
col.insert_many(data_json2)

print('Done!')