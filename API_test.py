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
password='Ter@Bgh543Asg#1234Ftgtyu'
vMM_aosip='140.118.151.249'

# =============================================================================

# Login & get data

#Get the token to access vMM information  -- via API
token = authentication(username,password,vMM_aosip)

command = 'show+ap+active+ap-name+DF_9F_AP01'
list_ap_database = show_command(vMM_aosip,token,command)
print(list_ap_database)