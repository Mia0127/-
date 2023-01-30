# -*- coding: utf-8 -*-
"""
Created on Sun Dec 25 00:00:26 2022

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

def main_loc(IY, loc_iy, floor):    
    #Get the token to access vMM information  -- via API
    token = authentication(username,password,vMM_aosip)
    df = {}
    
    for ap in IY:
        command = 'show+ap+monitor+ap-list+ap-name+IY_'+ap
        list_ap_database = show_command(vMM_aosip,token,command)
        df[ap] = pd.DataFrame(list_ap_database['Monitored AP Table'])
        df[ap]['curr-rssi'] = pd.to_numeric(df[ap]['curr-rssi'])
        df[ap] = df[ap][(df[ap]['ap-type']!='valid')
                                            &(df[ap]['essid']!='eduroam')
                                            &(df[ap]['essid']!='sensor')
                                            &(df[ap]['essid']!='NTUST-PEAP')
                                            &(df[ap]['essid']!='NTUST-UAM')][['essid','bssid','curr-rssi','ap-type', 'chan']]
        df[ap] = df[ap][(df[ap]['curr-rssi']>0)&(df[ap]['curr-rssi']<60)]

    try:
        ap1_int = df[IY[0]]['bssid']
    except Exception:
        ap1_int = None

    try:
        ap3_int = df[IY[1]]['bssid']
    except Exception:
        ap3_int = None

    try:
        ap5_int = df[IY[2]]['bssid']
    except Exception:
        ap5_int = None

    try:
        ap7_int = df[IY[3]]['bssid']
    except Exception:
        ap7_int = None

    try:
        ap9_int = df[IY[4]]['bssid']
    except Exception:
        ap9_int = None

    # Group all the interfering APs on IY- 1F

    ap13_int = pd.concat([ap1_int,ap3_int]).reset_index(drop=True).drop_duplicates()
    ap57_int = pd.concat([ap5_int,ap7_int]).reset_index(drop=True).drop_duplicates()
    ap_all_int = pd.concat([ap13_int,ap57_int]).reset_index(drop=True).drop_duplicates()
    ap_all_int = pd.concat([ap_all_int,ap9_int]).reset_index(drop=True).drop_duplicates()

    ap_all = pd.DataFrame(ap_all_int).reset_index(drop=True)
    ap_all['essid'], ap_all['ap type'], ap_all['channel'], ap_all[IY[0]]= '','','', None
    try:
        ap_all[IY[1]] = None
    except Exception:
        pass
    try:
        ap_all[IY[2]] = None
    except Exception:
        pass
    try:
        ap_all[IY[3]] = None
    except Exception:
        pass
    try:
        ap_all[IY[4]] = None
    except Exception:
        pass
    ap_all['mon AP number'] = None

    for i in range(len(ap_all)):
        no_ap = 0

        for ap in IY:
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

    ap_all = ap_all[(ap_all['mon AP number']>0)].sort_values('essid').reset_index(drop=True).drop_duplicates()


    ap_all['xloc'], ap_all['yloc'], ap_all['floor'] = '', '', ''
    ap_all_int = ap_all['bssid']
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

    # > 3 RSSI values

    def indoor_trilateration_5(mac):
        d1 = calc_dist(-count_rssi(mac)[1][1], a, n, k, w)
        d2 = calc_dist(-count_rssi(mac)[1][3], a, n, k, w)
        d3 = calc_dist(-count_rssi(mac)[1][5], a, n, k, w)
        d4 = calc_dist(-count_rssi(mac)[1][7], a, n, k, w)
        d5 = calc_dist(-count_rssi(mac)[1][9], a, n, k, w)

        x1, y1, x2, y2, x3, y3, x4, y4, x5, y5 = (count_rssi(mac)[1][0][0], count_rssi(mac)[1][0][1], 
                                          count_rssi(mac)[1][2][0], count_rssi(mac)[1][2][1], 
                                          count_rssi(mac)[1][4][0], count_rssi(mac)[1][4][1],
                                          count_rssi(mac)[1][6][0], count_rssi(mac)[1][6][1],
                                          count_rssi(mac)[1][8][0], count_rssi(mac)[1][8][1])


        x_1, y_1 = trilateration(x1,y1,d1,x2,y2,d2,x3,y3,d3)
        x_2, y_2 = trilateration(x1,y1,d1,x2,y2,d2,x4,y4,d4)
        x_3, y_3 = trilateration(x1,y1,d1,x2,y2,d2,x5,y5,d5)
        x_4, y_4 = trilateration(x1,y1,d1,x3,y3,d3,x4,y4,d4)
        x_5, y_5 = trilateration(x1,y1,d1,x3,y3,d3,x5,y5,d5)
        x_6, y_6 = trilateration(x1,y1,d1,x4,y4,d4,x5,y5,d5)
        x_7, y_7 = trilateration(x2,y2,d2,x3,y3,d3,x4,y4,d4)
        x_8, y_8 = trilateration(x2,y2,d2,x3,y3,d3,x5,y5,d5)
        x_9, y_9 = trilateration(x2,y2,d2,x4,y4,d4,x5,y5,d5)
        x_10, y_10 = trilateration(x3,y3,d3,x4,y4,d4,x5,y5,d5)

        x, y = ((x_1 + x_2 + x_3 + x_4 + x_5 + x_6 + x_7 + x_8 + x_9 + x_10)/10, 
                (y_1 + y_2 + y_3 + y_4 + y_5 + y_6 + y_7 + y_8 + y_9 + y_10)/10)


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

    # IY-1F APs location from WISE-PaaS (scale 1:100) => sc = 0.01

    rssi = [0, 0, 0, 0, 0]

    # Function to get monitoring AP location and RSSI
    def count_rssi(input_bssid):
        count_AP = 0
        neighbor_AP = []
        for i in range(len(loc_iy)):
            try: 
                rssi[i] = df[IY[i]].loc[df[IY[i]]['bssid'] == input_bssid]['curr-rssi'].item()
                if rssi[i] > 0:
                    count_AP+=1
                    neighbor_AP.append(loc_iy[i])
                    neighbor_AP.append(rssi[i])
                else:
                    count_AP +=0
            except:
                count_AP +=0

        return count_AP, neighbor_AP
    
    ap_list_3 = []
    ap_list_2 = []
    ap_list_4 = []
    ap_list_5 = []
    for i in ap_all_int:
        if count_rssi(i)[0]==3:
            ap_list_3.append(i)
        if count_rssi(i)[0]==2:
            ap_list_2.append(i)
        if count_rssi(i)[0]==4:
            ap_list_4.append(i)
        if count_rssi(i)[0]==5:
            ap_list_5.append(i)

    # =============================================================================

    # Run localization algorithm

    for mac in ap_list_3:
        for i in range(len(IY)):
            try:
                int_info = df[IY[i]][df[IY[i]]['bssid']==mac][['essid','bssid','ap-type','chan']]
            except Exception:
                pass
        try:
            x, y = indoor_trilateration_3(mac)
        except Exception:
            pass


    for mac in ap_list_4:
        for i in range(len(IY)):
            try:
                int_info = df[IY[i]][df[IY[i]]['bssid']==mac][['essid','bssid','ap-type','chan']]
            except Exception:
                pass
        try:
            x, y = indoor_trilateration_4(mac)
        except Exception:
            pass

    for mac in ap_list_2:
        for i in range(len(IY)):
            try:
                int_info = df[IY[i]][df[IY[i]]['bssid']==mac][['essid','bssid','ap-type','chan']]
            except Exception:
                pass
        try:
            x, y = indoor_trilateration_2(mac)
        except Exception:
            pass

    for mac in ap_list_5:
        for i in range(len(IY)):
            try:
                int_info = df[IY[i]][df[IY[i]]['bssid']==mac][['essid','bssid','ap-type','chan']]
            except Exception:
                pass
        try:
            x, y = indoor_trilateration_5(mac)
        except Exception:
            pass
        
    ap_all['floor'] = floor
        
    return ap_all
    
# =============================================================================

# Username & password & API

username='apiUser'
password='x564#kdHrtNb563abcde'
vMM_aosip='140.118.151.248'
# =============================================================================

# Login & get data

sc = 0.01

IYB1 = ['B1F_AP01', 'B1F_AP03', 'B1F_AP05']
IY1 = ['1F_AP01','1F_AP03','1F_AP05','1F_AP07']
IY2 = ['2F_AP01','2F_AP03','2F_AP05']
IY3 = ['3F_AP01','3F_AP03','3F_AP05','3F_AP07','3F_AP09']
IY4 = ['4F_AP01','4F_AP03','4F_AP05','4F_AP07']
IY5 = ['5F_AP01','5F_AP03','5F_AP05','5F_AP07','5F_AP09']
IY6 = ['6F_AP01','6F_AP03','6F_AP05','6F_AP07','6F_AP09']
IY7 = ['7F_AP01','7F_AP03','7F_AP05','7F_AP07','7F_AP09']
IY8 = ['8F_AP01','8F_AP03','8F_AP05','8F_AP07','8F_AP09']
IY9 = ['9F_AP01','9F_AP03','9F_AP05','9F_AP07']
IY10 = ['10F_AP01','10F_AP03','10F_AP05','10F_AP07']
IY11= ['11F_AP01']

loc_iyb1 = [(587.6262*sc, 478.14872*sc), (874.49187*sc, 430.33777*sc), (448.82023*sc, 259.14374*sc)]
loc_iy1 = [(410.95816*sc, 600*sc), (488.56726*sc, 259.36988*sc), (613.29732*sc, 472.62618*sc), (893.28036*sc, 419.36988*sc)]
loc_iy2 = [(417.97446*sc, 356.30792*sc), (680*sc, 555*sc), (721.80531*sc, 280.73578*sc)]
loc_iy3 = [(266.83018*sc, 197.4522*sc), (456.53167*sc, 475.06414*sc), (550.61128*sc, 226.75568*sc), (701.75555*sc, 499.74076*sc), (877.57645*sc, 269.93976*sc)]
loc_iy4 = [(442.65108*sc, 303.87011*sc), (427.22819*sc, 539.84026*sc), (899.16849*sc, 294.61638*sc), (757.27794*sc, 542.92484*sc)]
loc_iy5 = [(256.03416*sc, 229.84026*sc), (328.52172*sc, 512.07907*sc), (411.80531*sc, 229.84026*sc), (596.87993*sc, 512.07907*sc), (774.24312*sc, 382.52683*sc)]
loc_iy6 = [(254.49187*sc, 623.12384*sc), (518.22322*sc, 630.83529*sc), (711.00929*sc, 627.75071*sc), (333.14859*sc, 283.82036*sc), (805.08889*sc, 357.85021*sc)]
loc_iy7 = [(350.11376*sc, 232.92484*sc), (404.09386*sc, 512.07907*sc), (558.32272*sc, 234.46713*sc), (624.64113*sc, 513.62136*sc), (795.83516*sc, 257.601456*sc)]
loc_iy8 = [(357.82521*sc, 232.92484*sc), (382.50182*sc, 519.79051*sc), (542.89983*sc, 232.92484*sc), (629.26799*sc, 521.3328*sc), (903.79536*sc, 232.92484*sc)]
loc_iy9 = [(359.3675*sc, 558.34772*sc), (740.31277*sc, 288.44723*sc), (368.62123*sc, 274.56663*sc), (760.36252*sc, 541.38255*sc)]
loc_iy10 = [(408.72073*sc, 259.14374*sc), (359.3675*sc, 519.79051*sc), (778.86998*sc, 229.84026*sc), (778.86998*sc, 535.21339*sc)]
loc_iy11 = [(357.82521*sc, 479.69101*sc)]

fb1, f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11 = 'B1F', '1F', '2F', '3F', '4F', '5F', '6F', '7F', '8F', '9F', '10F', '11F'

dfb1 = main_loc(IYB1, loc_iyb1, fb1)
df1 = main_loc(IY1, loc_iy1, f1)
df1 = df1.rename({'1F_AP01': 'AP01', '1F_AP03': 'AP03','1F_AP05':'AP05','1F_AP07':'AP07'}, axis=1)
df2 = main_loc(IY2, loc_iy2, f2)
df3 = main_loc(IY3, loc_iy3, f3)
df4 = main_loc(IY4, loc_iy4, f4)
df5 = main_loc(IY5, loc_iy5, f5)
df6 = main_loc(IY6, loc_iy6, f6)
df7 = main_loc(IY7, loc_iy7, f7)
df8 = main_loc(IY8, loc_iy8, f8)
df9 = main_loc(IY9, loc_iy9, f9)
df10 = main_loc(IY10, loc_iy10, f10)

# =============================================================================

# Add 11F

ap_iy = ['11F_AP01']
print(ap_iy)
dataframe = {} 

#Get the token to access vMM information  -- via API
token = authentication(username,password,vMM_aosip)

for ap in ap_iy:
    try:
        command = 'show+ap+monitor+ap-list+ap-name+IY_'+ap
        list_ap_database = show_command(vMM_aosip,token,command)
        dataframe[ap] = pd.DataFrame(list_ap_database['Monitored AP Table'])
        dataframe[ap]['curr-rssi'] = pd.to_numeric(dataframe[ap]['curr-rssi'])
        dataframe[ap] = dataframe[ap][(dataframe[ap]['ap-type']!='valid')
                                            &(dataframe[ap]['essid']!='eduroam')
                                            &(dataframe[ap]['essid']!='sensor')
                                            &(dataframe[ap]['essid']!='NTUST-PEAP')
                                            &(dataframe[ap]['essid']!='NTUST-UAM')][['essid','bssid','curr-rssi','ap-type','chan']]
        dataframe[ap] = dataframe[ap][(dataframe[ap]['curr-rssi']>0)&(dataframe[ap]['curr-rssi']<60)]
    except Exception:
        pass

ap_all_int = pd.DataFrame(dataframe[ap_iy[0]]['bssid']).reset_index(drop=True)

ap_all_int['essid'], ap_all_int['ap type'], ap_all_int['channel'], ap_all_int[ap_iy[0]]= '','','',None
ap_all_int['x location'] = ''
ap_all_int['y location'] = ''
ap_all_int['mon AP number'] = None
ap_all_int['floor'] = '11F'

for i in range(len(ap_all_int)):
    no_ap = 0
    
    for ap in ap_iy:
        try:
        # Get essid
            ap_all_int['essid'][i] = list(dataframe[ap][(dataframe[ap]['bssid']==ap_all_int['bssid'][i])]['essid'])[0]
            ap_all_int['ap type'][i] = list(dataframe[ap][(dataframe[ap]['bssid']==ap_all_int['bssid'][i])]['ap-type'])[0]
            ap_all_int['channel'][i] = list(dataframe[ap][(dataframe[ap]['bssid']==ap_all_int['bssid'][i])]['chan'])[0]
        # Get rssi
            if dataframe[ap]['bssid'].str.contains(ap_all_int['bssid'][i]).any():
                ap_all_int[ap][i] = -list(dataframe[ap][dataframe[ap]['bssid']==ap_all_int['bssid'][i]]['curr-rssi'])[0] 
                no_ap+=1
        except Exception:
            pass
    ap_all_int['mon AP number'][i] = no_ap
print('Interfering APs detected in IY-B1F:')
df11 = ap_all_int[(ap_all_int['mon AP number']>0)].sort_values('essid').reset_index(drop=True).drop_duplicates()

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

data_jsonb1 = json.loads(dfb1.to_json(orient='records'))
data_json1 = json.loads(df1.to_json(orient='records'))
data_json2 = json.loads(df2.to_json(orient='records'))
data_json3 = json.loads(df3.to_json(orient='records'))
data_json4 = json.loads(df4.to_json(orient='records'))
data_json5 = json.loads(df5.to_json(orient='records'))
data_json6 = json.loads(df6.to_json(orient='records'))
data_json7 = json.loads(df7.to_json(orient='records'))
data_json8 = json.loads(df8.to_json(orient='records'))
data_json9 = json.loads(df9.to_json(orient='records'))
data_json10 = json.loads(df10.to_json(orient='records'))
data_json11 = json.loads(df11.to_json(orient='records'))

for i in range(len(data_jsonb1)):
    data_jsonb1[i]['ts'] = ts 
    data_jsonb1[i]['DatetimeStr'] = ts_tw_str
    data_jsonb1[i]['Datetime'] = ts_tw
    
for i in range(len(data_json1)):
    data_json1[i]['ts'] = ts 
    data_json1[i]['DatetimeStr'] = ts_tw_str
    data_json1[i]['Datetime'] = ts_tw

for i in range(len(data_json2)):
    data_json2[i]['ts'] = ts 
    data_json2[i]['DatetimeStr'] = ts_tw_str
    data_json2[i]['Datetime'] = ts_tw

for i in range(len(data_json3)):
    data_json3[i]['ts'] = ts 
    data_json3[i]['DatetimeStr'] = ts_tw_str
    data_json3[i]['Datetime'] = ts_tw
    
for i in range(len(data_json4)):
    data_json4[i]['ts'] = ts 
    data_json4[i]['DatetimeStr'] = ts_tw_str
    data_json4[i]['Datetime'] = ts_tw
    
for i in range(len(data_json5)):
    data_json5[i]['ts'] = ts 
    data_json5[i]['DatetimeStr'] = ts_tw_str
    data_json5[i]['Datetime'] = ts_tw
    
for i in range(len(data_json6)):
    data_json6[i]['ts'] = ts 
    data_json6[i]['DatetimeStr'] = ts_tw_str
    data_json6[i]['Datetime'] = ts_tw

for i in range(len(data_json7)):
    data_json7[i]['ts'] = ts 
    data_json7[i]['DatetimeStr'] = ts_tw_str
    data_json7[i]['Datetime'] = ts_tw
    
for i in range(len(data_json8)):
    data_json8[i]['ts'] = ts 
    data_json8[i]['DatetimeStr'] = ts_tw_str
    data_json8[i]['Datetime'] = ts_tw
    
for i in range(len(data_json1)):
    data_json1[i]['ts'] = ts 
    data_json1[i]['DatetimeStr'] = ts_tw_str
    data_json1[i]['Datetime'] = ts_tw
    
for i in range(len(data_json9)):
    data_json9[i]['ts'] = ts 
    data_json9[i]['DatetimeStr'] = ts_tw_str
    data_json9[i]['Datetime'] = ts_tw
    
for i in range(len(data_json10)):
    data_json10[i]['ts'] = ts 
    data_json10[i]['DatetimeStr'] = ts_tw_str
    data_json10[i]['Datetime'] = ts_tw

for i in range(len(data_json11)):
    data_json11[i]['ts'] = ts 
    data_json11[i]['DatetimeStr'] = ts_tw_str
    data_json11[i]['Datetime'] = ts_tw
# =============================================================================

# Store json data to MongoDB
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import pymongo
from pymongo import MongoClient
import re

# previous_day = datetime.now() - timedelta(days=30) 

client = MongoClient("140.118.70.40",27017)
db = client['WiFi_Dashboard_Data']

try:
    col=db["Int_Loc_B1F"]
    col.insert_many(data_jsonb1)
except Exception:
    pass

try:
    col=db["Int_Loc_1F"]
    col.insert_many(data_json1)
except Exception:
    pass

try:
    col=db["Int_Loc_2F"]
    col.insert_many(data_json2)
except Exception:
    pass

try:
    col=db["Int_Loc_3F"]
    col.insert_many(data_json3)
except Exception:
    pass

try:
    col=db["Int_Loc_4F"]
    col.insert_many(data_json4)
except Exception:
    pass

try:
    col=db["Int_Loc_5F"]
    col.insert_many(data_json5)
except Exception:
    pass

try:
    col=db["Int_Loc_6F"]
    col.insert_many(data_json6)
except Exception:
    pass

try:
    col=db["Int_Loc_7F"]
    col.insert_many(data_json7)
except Exception:
    pass

try:
    col=db["Int_Loc_8F"]
    col.insert_many(data_json8)
except Exception:
    pass

try:
    col=db["Int_Loc_9F"]
    col.insert_many(data_json9)
except Exception:
    pass

try:
    col=db["Int_Loc_10F"]
    col.insert_many(data_json10)
except Exception:
    pass

try:
    col=db["Int_Loc_11F"]
    col.insert_many(data_json11)
except Exception:
    pass

print('Done!')