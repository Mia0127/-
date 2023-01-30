# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 11:01:47 2023

@author: Administrator
"""
mongo_url_01= "mongodb://administrator:administrator@140.118.70.40:27017/"
mongo_url_02= "mongodb://administrator:administrator@140.118.70.40:27017/"
mongo_url_03= "mongodb://administrator:administrator@140.118.70.40:27017/"

from wisepaasdatahubedgesdk.EdgeAgent import EdgeAgent
import wisepaasdatahubedgesdk.Common.Constants as constant
from wisepaasdatahubedgesdk.Model.Edge import EdgeAgentOptions, MQTTOptions, DCCSOptions, EdgeData, EdgeTag, EdgeStatus, EdgeDeviceStatus, EdgeConfig, NodeConfig, DeviceConfig, AnalogTagConfig, DiscreteTagConfig, TextTagConfig
from wisepaasdatahubedgesdk.Common.Utils import RepeatedTimer
#import pingcheck
import pymongo
from pymongo import MongoClient
import time
import datetime
nodeID="2b01864b-9e35-4fdd-aab1-bf6eb230f1c4"
apiURL="https://api-dccs-ensaas.education.wise-paas.com/"
CredentialKEY="ddec7a8ff76662a01ed89da79e157f0m"
edgeAgentOptions = EdgeAgentOptions(nodeId = nodeID)#nodeID
edgeAgentOptions.connectType = constant.ConnectType['DCCS']
dccsOptions = DCCSOptions(apiUrl = apiURL, credentialKey = CredentialKEY)
edgeAgentOptions.DCCS = dccsOptions
_edgeAgent = EdgeAgent(edgeAgentOptions)
_edgeAgent.connect()


#creat data connect

def creatdataconnect(_edgeAgent, map_data):
    config = __generateConfig(map_data)
    _edgeAgent.uploadConfig(action = constant.ActionType['Create'], edgeConfig = config)
def __generateConfig(map_data):
    config = EdgeConfig()
    nodeConfig = NodeConfig(nodeType = constant.EdgeType['Gateway'])
    config.node = nodeConfig
    for i in range(1):
        deviceConfig = DeviceConfig(id = 'Map',
          name = 'Map',
          description = 'Map',
          deviceType = 'Smart Device',
          retentionPolicyName = '')
        for j in range(len(map_data)):
            analog = AnalogTagConfig(name = map_data[j]['ap_name'],
                description = map_data[j]['total_data_bytes'],
                readOnly = False,
                arraySize = 0,
                spanHigh = 1000,
                spanLow = 0,
                engineerUnit = '',
                integerDisplayFormat = 4,
                fractionDisplayFormat = 2)
            deviceConfig.analogTagList.append(analog)
              
            
        config.node.deviceList.append(deviceConfig)
    return config

def Membersdata(DB="AP", Collection="Controller4",Search={ }):
    global mongo_url_01, mongo_url_02
    try:
        conn = MongoClient(mongo_url_01)
        db=conn[DB]
        collection = db[Collection]
        cursor = collection.find(Search).sort("_id",-1).limit(5)
        map_data=[d for d in cursor]
    except:
        conn = MongoClient(mongo_url_02)
        db = conn[DB]
        collection = db[Collection]
        cursor = collection.find(Search).limit(5)
        map_data=[d for d in cursor]
    if map_data==[]:
        return False
    else:
        return map_data
    
map_data= Membersdata()
creatdataconnect(_edgeAgent, map_data)