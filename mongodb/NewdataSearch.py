import pymongo
from pymongo import MongoClient
mongo_url_01 = "mongodb://admin:administrator@140.118.70.40:27017/"
mongo_url_02 = "mongodb://admin:administrator@140.118.70.40:27017/"
mongo_url_03 = "mongodb://admin:administrator@140.118.70.40:27017/"

def WriteInDB(DB,Collection,new_data):
    try:
        conn = MongoClient(mongo_url_01)
        db = conn[DB]
        collection = db[Collection]
        collection.insert(new_data)
    except:
        try:
            conn = MongoClient(mongo_url_02)
            db = conn[DB]
            collection = db[Collection]
            collection.insert(new_data)
        except:
            try:
                conn = MongoClient(mongo_url_03)
                db = conn[DB]
                collection = db[Collection]
                collection.insert(new_data)
            except:
                print("no one success to write data into DB !")

def Membersdata(DB, Collection, Search={}):
    #Membersdata(DB="xinxing_dispenser", Collection="members_data_test", Search={'Class':'701})

    global mongo_url_01, mongo_url_02
    try:
        conn = MongoClient(mongo_url_01)
        db = conn[DB]
        collection = db[Collection]
        cursor = collection.find(Search)
        data = [d for d in cursor]
    except:
        conn = MongoClient(mongo_url_02)
        db = conn[DB]
        collection = db[Collection]
        cursor = collection.find(Search)
        data = [d for d in cursor]
    if data == []:
        return False
    else:
        return data
