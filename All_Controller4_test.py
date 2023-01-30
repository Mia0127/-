# -*- coding: utf-8 -*-

import pandas as pd
import requests
import warnings
import time
# from time import sleep
from bs4 import BeautifulSoup
import json
import os
import datetime
import numpy as np
import pymongo
from pymongo import MongoClient
import re
import arubaapi 

# =============================================================================

# MongoDB Database & Collection

# Database="WiFi_Client_Data"
# Collections="Controller_4"

# =============================================================================

# Aruba API account & password

account = 'apiUser'
password = 'x564#kdHrtNb563abcde'

# =============================================================================


Controller_url='https://140.118.151.248:4343'

# Avoid warning

warnings.filterwarnings('ignore') 
path = 'data.txt'
# =============================================================================

# auto login and get cookie

url = Controller_url+'/screens/wms/wms.login'
headers = {'Content-Type': 'text/html','User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}
chartData = 'opcode=login&url=%2Flogin.html&needxml=0&uid='+account+'&passwd='+password
res_data = requests.post(url, verify=False, headers = headers, data = chartData.encode('utf-8'))
cookieStr = res_data.cookies['SESSION']

# =============================================================================

################################ DASHBOARD DATA ###############################

# =============================================================================

# Retrieve and parse AP data

url = Controller_url+'/screens/cmnutil/execUiQuery.xml'
headers = {'Content-Type': 'text/plain'}
cookie = {"SESSION":cookieStr}
payloadData = 'query=<aruba_queries><query><qname>backend-observer-radio-8</qname><type>list</type><list_query><device_type>radio</device_type><requested_columns>ap_eth_mac_address mesh_portal_ap_mac mesh_uplink_age ap_name role radio_band radio_bssid radio_ht_phy_type channel_str channel_5_ghz channel_2_4_ghz radio_generic_mode radio_mode radio_number pcap_id pcap_state pcap_target_ip pcap_target_port eirp_10x max_eirp noise_floor arm_ch_qual total_moves successful_moves sta_count current_channel_utilization rx_time tx_time channel_interference channel_free channel_busy avg_data_rate tx_avg_data_rate rx_avg_data_rate tx_frames_transmitted tx_frames_dropped tx_bytes_transmitted tx_bytes_dropped tx_time_transmitted tx_time_dropped tx_data_transmitted tx_data_dropped tx_data_retried tx_data_transmitted_retried tx_data_bytes_transmitted tx_data_bytes_dropped tx_bcast_data tx_mcast_data tx_ucast_data tx_time_data_transmitted tx_time_data_dropped tx_mgmt rx_promisc_good rx_promisc_bad rx_frames rx_frames_others rx_promisc_bytes rx_bytes rx_bytes_others rx_promisc_data rx_data rx_data_others rx_promisc_data_bytes rx_data_bytes rx_data_bytes_others rx_data_retried rx_bcast_data rx_mcast_data rx_ucast_data tx_data_frame_rate_dist rx_data_frame_rate_dist tx_data_bytes_rate_dist rx_data_bytes_rate_dist total_data_throughput tx_data_throughput rx_data_throughput total_bcast_data total_mcast_data total_ucast_data total_data_frames total_data_bytes total_data_type_dist tx_data_type_dist rx_data_type_dist vap_count ap_quality mesh_rssi mesh_tx_goodput mesh_rx_goodput mesh_tx_throughput mesh_rx_throughput mesh_tx_success mesh_tx_retry mesh_tx_drop mesh_rx_success mesh_rx_retry</requested_columns><sort_by_field>ap_name</sort_by_field><sort_order>asc</sort_order><pagination><start_row>0</start_row><num_rows>200</num_rows></pagination></list_query></query></aruba_queries>&UIDARUBA='+cookieStr

res = requests.post(url, verify=False, headers = headers, cookies = cookie, data = payloadData.encode('utf-8'))

soup = BeautifulSoup(res.text, 'html.parser')
header_tags = soup.find_all('header')
row_tags=soup.find_all('row')

# =============================================================================

# Rearrange DataFrame

df=pd.DataFrame()
index=0

row_tags[0]
for values in row_tags:
    
    data=values.find_all('value')
    data_total=[]
    
    time_stamp =int(time.time())
    struct_time = time.localtime(time_stamp) 
    timeString = time.strftime("%Y-%m-%d-%H-%M", struct_time) 
    data_total.append(time_stamp)

    for i in range(len(data)):

        data_total.append(data[i].text)
        
    index+=1
    df[index]=data_total

# =============================================================================

# Add header to dataframe

for values in header_tags:
    Client_Data=[] 
    Client_Data.append('time_stamp')
    column_name=values.find_all('column_name')
    for i in range(len(column_name)) :
        Client_Data.append(column_name[i].text)

df.index=Client_Data
df=df.T
df.reset_index(drop=True, inplace=True)
df2 = df[['ap_name','radio_band','arm_ch_qual','ap_quality','noise_floor','rx_time','tx_time','channel_interference','channel_free','channel_busy','sta_count', 'eirp_10x', 'tx_bytes_transmitted','rx_data_bytes','total_data_bytes','mesh_tx_goodput', 'mesh_rx_goodput','current_channel_utilization','channel_str' ]]

df2['sta_count_all'] = df2['sta_count']
for i in range(len(df2)):
    # df2['radio_band'][i] = int(df2['radio_band'][i])
    # df2['noise_floor'][i] = int(df2['noise_floor'][i]) 
    # df2['sta_count'][i] = int(df2['sta_count'][i])
    
    try :
        df2['rx_time'][i] = int(re.findall("([0-9]+)\/", df2['rx_time'][i])[0])/60000
    except Exception:
        df2['rx_time'][i] = 0
    try :
        df2['tx_time'][i] = int(re.findall("([0-9]+)\/", df2['tx_time'][i])[0])/60000
    except Exception:
        df2['tx_time'][i] = 0
    try :
        df2['channel_interference'][i] = int(re.findall("([0-9]+)\/", df2['channel_interference'][i])[0])/60000
    except Exception:
        df2['channel_interference'][i] = 0
    try :
        df2['channel_free'][i] = int(re.findall("([0-9]+)\/", df2['channel_free'][i])[0])/60000
    except Exception:
        df2['channel_free'][i] = 0
    try :
        df2['channel_busy'][i] = int(re.findall("([0-9]+)\/", df2['channel_busy'][i])[0])/60000
    except Exception:
        df2['channel_busy'][i] = 0
    # Add total client number
    for i in range(len(df2) - 1):
        if df2['ap_name'][i] == df2['ap_name'][i+1]:
            df2['sta_count_all'][i] = int(df2['sta_count'][i]) + int(df2['sta_count'][i+1])
            df2['sta_count_all'][i+1] = df2['sta_count_all'][i]

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

data_json = json.loads(df2.to_json(orient='records'))

for i in range(len(data_json)):
    data_json[i]['ts'] = ts 
    data_json[i]['DatetimeStr'] = ts_tw_str
    data_json[i]['Datetime'] = ts_tw

# =============================================================================

# Store json data to MongoDB
from bson.objectid import ObjectId
from datetime import datetime, timedelta

previous_day = datetime.now() - timedelta(days=1) 

# =============================================================================

################################ AP DATA ######################################

# # C0ntroller_4===============================================================

# -*- coding: utf-8 -*-
"""
Created on  Oct 27 12:21:21 2022

@author: Hoai-Nam
"""

import pandas as pd
import requests
import warnings
import time
# from time import sleep
from bs4 import BeautifulSoup
import json
import os
import datetime
import numpy as np
import pymongo
from pymongo import MongoClient
import re

# =============================================================================

# MongoDB Database & Collection

# Database="AP_Data"
# Collections="Controller4"

# =============================================================================

# Aruba API account & password

account = 'apiUser'
password = 'x564#kdHrtNb563abcde'

# =============================================================================


Controller_url='https://140.118.151.248:4343'

# Avoid warning

warnings.filterwarnings('ignore') 
path = 'data.txt'
# =============================================================================

# auto login and get cookie

url = Controller_url+'/screens/wms/wms.login'
headers = {'Content-Type': 'text/html','User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}
chartData = 'opcode=login&url=%2Flogin.html&needxml=0&uid='+account+'&passwd='+password
res_data = requests.post(url, verify=False, headers = headers, data = chartData.encode('utf-8'))
cookieStr = res_data.cookies['SESSION']

# =============================================================================

# Retrieve and parse AP data

url = Controller_url+'/screens/cmnutil/execUiQuery.xml'
headers = {'Content-Type': 'text/plain'}
cookie = {"SESSION":cookieStr}
payloadData = 'query=<aruba_queries><query><qname>backend-observer-ap-42</qname><type>list</type><list_query><device_type>ap</device_type><requested_columns>ap_name ap_eth_mac_address ap_group ap_deployment_mode ap_model ap_serial_number ap_ip_address ap_status ap_state_reason ap_provisioned ap_uptime lms_ip ap_active_aac ap_standby_aac ap_cluster_name ap_cur_dual_5g_mode ap_tri_radio_mode radio_count total_data_bytes sta_count ssid_count ap_datazone role pcap_on green_state mesh_role mesh_cluster_name mesh_portal_ap_mac mesh_portal_name mesh_parent_ap_mac mesh_parent_name mesh_uplink_time mesh_uplink_age mesh_child_num</requested_columns><sort_by_field>sta_count</sort_by_field><sort_order>desc</sort_order><pagination><start_row>0</start_row><num_rows>200</num_rows></pagination></list_query><filter><global_operator>and</global_operator><filter_list><filter_item_entry><field_name>ap_status</field_name><comp_operator>equals</comp_operator><value><![CDATA[1]]></value></filter_item_entry><filter_item_entry><field_name>role</field_name><comp_operator>equals</comp_operator><value><![CDATA[1]]></value></filter_item_entry></filter_list></filter></query></aruba_queries>&UIDARUBA='+cookieStr

res = requests.post(url, verify=False, headers = headers, cookies = cookie, data = payloadData.encode('utf-8'))

soup = BeautifulSoup(res.text, 'html.parser')
header_tags = soup.find_all('header')
row_tags=soup.find_all('row')

# =============================================================================

# Rearrange DataFrame

df=pd.DataFrame()
index=0

for values in row_tags:
    
    data=values.find_all('value')
    data_total=[]
    
    time_stamp =int(time.time())
    struct_time = time.localtime(time_stamp) 
    timeString = time.strftime("%Y-%m-%d-%H-%M", struct_time) 
    data_total.append(time_stamp)

    for i in range(len(data)):

        data_total.append(data[i].text)
        
    index+=1
    df[index]=data_total

# =============================================================================

# Add header to dataframe

for values in header_tags:
    Header_Data=[] 
    Header_Data.append('time_stamp')
    column_name=values.find_all('column_name')
    for i in range(len(column_name)) :
        Header_Data.append(column_name[i].text)


df.index=Header_Data
df=df.T
df.reset_index(drop=True, inplace=True)

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

# =============================================================================

# create json

data_json2 = json.loads(df.to_json(orient='records'))

for i in range(len(data_json2)):
    try:
        data_json2[i]['sta_count'] = int(data_json2[i]['sta_count'])
        data_json2[i]['ap_status'] = int(data_json2[i]['ap_status'])
        data_json2[i]['ap_provisioned'] = int(data_json2[i]['ap_provisioned'])
        data_json2[i]['ap_uptime'] = int(data_json2[i]['ap_uptime'])
        data_json2[i]['ap_deployment_mode'] = int(data_json2[i]['ap_deployment_mode'])
        data_json2[i]['ap_model'] = int(data_json2[i]['ap_model'])
    except Exception:
        pass
    data_json2[i]['ts'] = ts 
    data_json2[i]['DatetimeStr'] = ts_tw_str
    data_json2[i]['Datetime'] = ts_tw
#data_json[1]
# print(data_json[1])
for i in range(len(data_json2)):
    for j in range(len(data_json)):
        if(data_json2[i]['ap_name']==data_json[j]['ap_name']):
            data_json2[i]['radio_band']=data_json[j]['radio_band']
            data_json2[i]['arm_ch_qual']=data_json[j]['arm_ch_qual']
            data_json2[i]['ap_quality']=data_json[j]['ap_quality']
            data_json2[i]['rx_time']=data_json[j]['rx_time']
            data_json2[i]['tx_time']=data_json[j]['tx_time']
            data_json2[i]['channel_interference']=data_json[j]['channel_interference']
            data_json2[i]['channel_free']=data_json[j]['channel_free']
            data_json2[i]['channel_busy']=data_json[j]['channel_busy']
            data_json2[i]['sta_count']=data_json[j]['sta_count']
            data_json2[i]['eirp_10x']=data_json[j]['eirp_10x']
            data_json2[i]['tx_bytes_transmitted']=data_json[j]['tx_bytes_transmitted']
            data_json2[i]['rx_data_bytes']=data_json[j]['rx_data_bytes']
            data_json2[i]['total_data_bytes']=data_json[j]['total_data_bytes']
            data_json2[i]['mesh_tx_goodput']=data_json[j]['mesh_tx_goodput']
            data_json2[i]['mesh_rx_goodput']=data_json[j]['mesh_rx_goodput']
            data_json2[i]['current_channel_utilization']=data_json[j]['current_channel_utilization']
            data_json2[i]['channel_str']=data_json[j]['channel_str']            
            break

# =============================================================================

# Store json data to MongoDB

from bson.objectid import ObjectId
from datetime import datetime, timedelta

previous_day = datetime.now() - timedelta(days=1)

client = MongoClient("140.118.70.40",27017)
db = client['AP']
col=db["Controller4"]
col.delete_many({"Datetime": {"$lt": previous_day}})
col.insert_many(data_json2)

# =============================================================================

################################ CLIENT DATA ##################################

# =============================================================================

# Retrieve and parse AP data

url = Controller_url+'/screens/cmnutil/execUiQuery.xml'
headers = {'Content-Type': 'text/plain'}
cookie = {"SESSION":cookieStr}
payloadData = 'query=<aruba_queries><query><qname>backend-observer-sta-13</qname><type>list</type><list_query><device_type>sta</device_type><requested_columns>sta_mac_address client_ht_phy_type openflow_state client_ip_address client_user_name client_dev_type client_ap_location client_conn_port client_conn_type client_timestamp client_role_name client_active_uac client_standby_uac ap_cluster_name client_health total_moves successful_moves steer_capability ssid ap_name channel channel_str channel_busy tx_time rx_time channel_free channel_interference current_channel_utilization radio_band bssid speed max_negotiated_rate noise_floor radio_ht_phy_type snr total_data_frames total_data_bytes avg_data_rate tx_avg_data_rate rx_avg_data_rate tx_frames_transmitted tx_frames_dropped tx_bytes_transmitted tx_bytes_dropped tx_time_transmitted tx_time_dropped tx_data_transmitted tx_data_dropped tx_data_retried tx_data_transmitted_retried tx_data_bytes_transmitted tx_abs_data_bytes tx_data_bytes_dropped tx_time_data_transmitted tx_time_data_dropped tx_mgmt rx_frames rx_bytes rx_data rx_data_bytes rx_abs_data_bytes rx_data_retried tx_data_frame_rate_dist rx_data_frame_rate_dist tx_data_bytes_rate_dist rx_data_bytes_rate_dist connection_type_classification total_data_throughput tx_data_throughput rx_data_throughput client_auth_type client_auth_subtype client_encrypt_type client_fwd_mode</requested_columns><sort_by_field>client_ip_address</sort_by_field><sort_order>asc</sort_order><pagination><start_row>0</start_row><num_rows>200</num_rows></pagination></list_query><filter><global_operator>and</global_operator><filter_list><filter_item_entry><field_name>client_conn_type</field_name><comp_operator>not_equals</comp_operator><value><![CDATA[0]]></value></filter_item_entry></filter_list></filter></query></aruba_queries>&UIDARUBA='+cookieStr
res = requests.post(url, verify=False, headers = headers, cookies = cookie, data = payloadData.encode('utf-8'))
soup = BeautifulSoup(res.text, 'html.parser')
header_tags = soup.find_all('header')
row_tags=soup.find_all('row')

# =============================================================================

# Rearrange DataFrame

df=pd.DataFrame()
index=0
for values in row_tags:
    
    data=values.find_all('value')
    data_total=[]
    
    time_stamp =int(time.time())
    struct_time = time.localtime(time_stamp)
    timeString = time.strftime("%Y-%m-%d-%H-%M", struct_time)
    data_total.append(time_stamp)

    for i in range(len(data)):

        data_total.append(data[i].text)
        
    index+=1
    df[index]=data_total

for values in header_tags:
    Client_Data=[] 
    Client_Data.append('time_stamp')
    column_name=values.find_all('column_name')
    for i in range(len(column_name)) :
        #print(column_name[i].text)
        Client_Data.append(column_name[i].text)


df.index=Client_Data
df=df.T
df=df.sort_values(by=['ap_name'])
df.reset_index(drop=True, inplace=True)

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

# =============================================================================

# create json

data_json = json.loads(df.to_json(orient='records'))

for i in range(len(data_json)):
    try:
        data_json[i]['time_stamp'] = int(data_json[i]['time_stamp'])
        data_json[i]['client_ht_phy_type'] = int(data_json[i]['client_ht_phy_type'])
        data_json[i]['client_conn_port'] = int(data_json[i]['client_conn_port'])
        data_json[i]['client_conn_type'] = int(data_json[i]['client_conn_type'])
        data_json[i]['client_timestamp'] = int(data_json[i]['client_timestamp'])
        data_json[i]['client_health'] = int(data_json[i]['client_health'])
        data_json[i]['total_moves'] = int(data_json[i]['total_moves'])
        data_json[i]['successful_moves'] = int(data_json[i]['successful_moves'])
        data_json[i]['steer_capability'] = int(data_json[i]['steer_capability'])
        data_json[i]['channel'] = int(data_json[i]['channel'])
        data_json[i]['radio_band'] = int(data_json[i]['radio_band'])
        data_json[i]['speed'] = int(data_json[i]['speed'])
        data_json[i]['max_negotiated_rate'] = int(data_json[i]['max_negotiated_rate'])
        data_json[i]['noise_floor'] = int(data_json[i]['noise_floor'])
        data_json[i]['radio_ht_phy_type'] = int(data_json[i]['radio_ht_phy_type'])
        data_json[i]['snr'] = int(data_json[i]['snr'])
        data_json[i]['total_data_frames'] = int(data_json[i]['total_data_frames'])
        data_json[i]['total_data_bytes'] = int(data_json[i]['total_data_bytes'])
        data_json[i]['avg_data_rate'] = int(data_json[i]['avg_data_rate'])
        data_json[i]['tx_avg_data_rate'] = int(data_json[i]['tx_avg_data_rate'])
        data_json[i]['rx_avg_data_rate'] = int(data_json[i]['rx_avg_data_rate'])
        data_json[i]['tx_frames_transmitted'] = int(data_json[i]['tx_frames_transmitted'])
        data_json[i]['tx_data_transmitted'] = int(data_json[i]['tx_data_transmitted'])
        data_json[i]['tx_data_bytes_transmitted'] = int(data_json[i]['tx_data_bytes_transmitted'])
        data_json[i]['tx_abs_data_bytes'] = int(data_json[i]['tx_abs_data_bytes'])
        data_json[i]['tx_mgmt'] = int(data_json[i]['tx_mgmt'])
        data_json[i]['rx_frames'] = int(data_json[i]['rx_frames'])
        data_json[i]['rx_bytes'] = int(data_json[i]['rx_bytes'])
        data_json[i]['rx_data'] = int(data_json[i]['rx_data'])
        data_json[i]['rx_data_bytes'] = int(data_json[i]['rx_data_bytes'])
        data_json[i]['rx_abs_data_bytes'] = int(data_json[i]['rx_abs_data_bytes'])
        data_json[i]['total_data_throughput'] = int(data_json[i]['total_data_throughput'])
        data_json[i]['tx_data_throughput'] = int(data_json[i]['tx_data_throughput'])
        data_json[i]['rx_data_throughput'] = int(data_json[i]['rx_data_throughput'])
        data_json[i]['client_auth_type'] = int(data_json[i]['client_auth_type'])
        data_json[i]['client_auth_subtype'] = int(data_json[i]['client_auth_subtype'])
        data_json[i]['client_encrypt_type'] = int(data_json[i]['client_encrypt_type'])
        data_json[i]['client_fwd_mode'] = int(data_json[i]['client_fwd_mode'])
        # Append int values for ratio units
        data_json[i]['tx_time_int'] = int(re.findall("([0-9]+)\/", data_json[i]['tx_time'])[0])
        data_json[i]['rx_time_int'] = int(re.findall("([0-9]+)\/", data_json[i]['rx_time'])[0])
        data_json[i]['channel_free_int'] = int(re.findall("([0-9]+)\/", data_json[i]['channel_free'])[0])
        data_json[i]['channel_interference_int'] = int(re.findall("([0-9]+)\/", data_json[i]['channel_interference'])[0])
        data_json[i]['channel_busy_int'] = int(re.findall("([0-9]+)\/", data_json[i]['channel_busy'])[0])
        data_json[i]['tx_frames_dropped_int'] = int(re.findall("([0-9]+)\/", data_json[i]['tx_frames_dropped'])[0])
#         data_json[i]['tx_bytes_transmitted_int'] = int(re.findall("([0-9]+)\/", data_json[i]['tx_bytes_transmitted'])[0])
        data_json[i]['tx_bytes_dropped_int'] = int(re.findall("([0-9]+)\/", data_json[i]['tx_bytes_dropped'])[0])
        data_json[i]['tx_time_transmitted_int'] = int(re.findall("([0-9]+)\/", data_json[i]['tx_time_transmitted'])[0])
        data_json[i]['tx_time_dropped_int'] = int(re.findall("([0-9]+)\/", data_json[i]['tx_time_dropped'])[0])
        data_json[i]['tx_data_dropped_int'] = int(re.findall("([0-9]+)\/", data_json[i]['tx_data_dropped'])[0])
        data_json[i]['tx_data_retried_int'] = int(re.findall("([0-9]+)\/", data_json[i]['tx_data_retried'])[0])
        data_json[i]['tx_data_transmitted_retried_int'] = int(re.findall("([0-9]+)\/", data_json[i]['tx_data_transmitted_retried'])[0])
        data_json[i]['tx_data_dropped_int'] = int(re.findall("([0-9]+)\/", data_json[i]['tx_data_dropped'])[0])
        data_json[i]['tx_data_retried_int'] = int(re.findall("([0-9]+)\/", data_json[i]['tx_data_retried'])[0])
        data_json[i]['tx_data_transmitted_retried_int'] = int(re.findall("([0-9]+)\/", data_json[i]['tx_data_transmitted_retried'])[0])
        data_json[i]['tx_time_data_transmitted_int'] = int(re.findall("([0-9]+)\/", data_json[i]['tx_time_data_transmitted'])[0])
        data_json[i]['tx_time_data_dropped_int'] = int(re.findall("([0-9]+)\/", data_json[i]['tx_time_data_dropped'])[0])
        data_json[i]['rx_data_retried_int'] = int(re.findall("([0-9]+)\/", data_json[i]['rx_data_retried'])[0])
        # Append ISODate
    except Exception:
        pass
    data_json[i]['ts'] = ts
    data_json[i]['DatetimeStr'] = ts_tw_str
    data_json[i]['Datetime'] = ts_tw
    
data_json[1]
# =============================================================================

# Store json data to MongoDB

client = MongoClient("140.118.70.40",27017)
db = client['Client']
col=db["Controller4"]
#col.delete_many({})
col.insert_many(data_json)

# =============================================================================

################################ INTERFERENCE DATA ############################

# =============================================================================

# Retrieve and parse AP data


url = Controller_url+'/screens/cmnutil/execUiQuery.xml'
headers = {'Content-Type': 'text/plain'}
cookie = {"SESSION":cookieStr}
payloadData = 'query=<aruba_queries><query><qname>backend-observer-mon_bssid-17</qname><type>list</type><list_query><device_type>mon_bssid</device_type><requested_columns>mon_ap mon_bssid mon_radio_phy_type mon_ssid mon_radio_band mon_ap_current_channel mon_ht_sec_channel mon_sta_count mon_ap_classification mon_ap_match_conf_level mon_ap_encr mon_ap_encr_auth mon_ap_encr_cipher mon_ap_is_dos mon_ap_type mon_ap_status mon_is_ibss mon_ap_create_time mon_ap_match_type mon_ap_match_method mon_ap_match_name mon_ap_match_time wms_event_count</requested_columns><sort_by_field>mon_ssid</sort_by_field><sort_order>desc</sort_order><pagination><start_row>0</start_row><num_rows>200</num_rows></pagination></list_query><filter><global_operator>and</global_operator><filter_list><filter_item_entry><field_name>mon_ap_status</field_name><comp_operator>equals</comp_operator><value><![CDATA[1]]></value></filter_item_entry></filter_list></filter></query></aruba_queries>&UIDARUBA='+cookieStr

res = requests.post(url, verify=False, headers = headers, cookies = cookie, data = payloadData.encode('utf-8'))

soup = BeautifulSoup(res.text, 'html.parser')
header_tags = soup.find_all('header')
row_tags=soup.find_all('row')

# =============================================================================

# Rearrange DataFrame

df=pd.DataFrame()
index=0

row_tags[0]
for values in row_tags:
    
    data=values.find_all('value')
    data_total=[]
    
    time_stamp =int(time.time())
    struct_time = time.localtime(time_stamp) 
    timeString = time.strftime("%Y-%m-%d-%H-%M", struct_time) 
    data_total.append(time_stamp)

    for i in range(len(data)):

        data_total.append(data[i].text)
        
    index+=1
    df[index]=data_total

# =============================================================================

# Add header to dataframe

for values in header_tags:
    Client_Data=[] 
    Client_Data.append('time_stamp')
    column_name=values.find_all('column_name')
    for i in range(len(column_name)) :
        Client_Data.append(column_name[i].text)


df.index=Client_Data
df=df.T
df.reset_index(drop=True, inplace=True)


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

data_json = json.loads(df.to_json(orient='records'))

for i in range(len(data_json)):
    try:
        data_json[i]['mon_ssid'] = data_json[i]['mon_ssid'].encode('latin-1').decode('utf-8')
        data_json[i]['mon_radio_band'] = int(data_json[i]['mon_radio_band'])
        data_json[i]['mon_ap_current_channel'] = int(data_json[i]['mon_ap_current_channel'])
        data_json[i]['mon_ht_sec_channel'] = int(data_json[i]['mon_ht_sec_channel'])
        data_json[i]['mon_sta_count'] = int(data_json[i]['mon_sta_count'])
        data_json[i]['mon_ap_classification'] = int(data_json[i]['mon_ap_classification'])
        data_json[i]['mon_ap_match_conf_level'] = int(data_json[i]['mon_ap_match_conf_level'])
        data_json[i]['mon_ap_encr'] = int(data_json[i]['mon_ap_encr'])
        data_json[i]['mon_ap_encr_auth']= int(data_json[i]['mon_ap_encr_auth'])
        data_json[i]['mon_ap_encr_cipher']= int(data_json[i]['mon_ap_encr_cipher'])
        data_json[i]['mon_ap_is_dos']= int(data_json[i]['mon_ap_is_dos'])
        data_json[i]['mon_ap_type']= int(data_json[i]['mon_ap_type'])
        data_json[i]['mon_ap_status']= int(data_json[i]['mon_ap_status'])
        data_json[i]['mon_is_ibss']= int(data_json[i]['mon_is_ibss'])
        data_json[i]['mon_ap_create_time']= int(data_json[i]['mon_ap_create_time'])
        data_json[i]['mon_ap_match_type']= int(data_json[i]['mon_ap_match_type'])
        data_json[i]['mon_ap_match_method']= int(data_json[i]['mon_ap_match_method'])
        data_json[i]['mon_ap_match_name']= int(data_json[i]['mon_ap_match_name'])
        data_json[i]['mon_ap_match_time']= int(data_json[i]['mon_ap_match_time'])
        data_json[i]['wms_event_count']= int(data_json[i]['wms_event_count'])
    except Exception:
        pass
    data_json[i]['ts'] = ts 
    data_json[i]['DatetimeStr'] = ts_tw_str
    data_json[i]['Datetime'] = ts_tw
data_json[1]

# =============================================================================

# Store json data to MongoDB

client = MongoClient("140.118.70.40",27017)
db = client['Interference']
col=db["Controller4"]
col.delete_many({"Datetime": {"$lt": previous_day}})
# col.delete_many({})
col.insert_many(data_json)

print('ok')
