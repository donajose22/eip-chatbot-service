from src.logger import Logger
import pymongo
from json import loads,load
import os
from datetime import datetime
from config.config import global_config

config = global_config

class mongoDbConnection():
    def __init__(self, conn_string, db_name, collection_name):
        try:
            self.client = pymongo.MongoClient(conn_string, 
                                        tls=True, 
                                        tlsAllowInvalidCertificates=False, 
                                        tlsCAFile=config["ssl"]["ca"]) 
            self.db_name = db_name
            self.collection_name = collection_name
            Logger().getLogger().info("**********Connected to DB**********")
        except Exception as e:
            Logger().getLogger().error(e)
            if self.client is not None:
                self.client.close()
    

    def addDetails(self, data:dict):
        try:
            database = self.client[self.db_name]
            collection = database[self.collection_name]
            result = collection.insert_one(data)
            Logger().getLogger().info("**********Record added to MongoDB**********")
            # Logger().getLogger().info(result.inserted_id)
            return result
        except pymongo.errors.DuplicateKeyError:
            Logger().getLogger().error("MongoDB ERROR: Duplicate Key Error")
            return({"message":"Duplicate Key Error"},200)
        except Exception as e:
            Logger().getLogger().error("MongoDB:addDetails"+str(e))
            raise Exception("MongoDB:addDetails:"+str(e))
    
    def updateDetails(self, _id, record:dict):
        try:
            database = self.db_name
            collection = database[self.collection_name]
            data = {'$set': record}
            result = collection.update_one(_id, data)
            Logger().getLogger().info("**********Record Updated*************")
        except pymongo.errors.DuplicateKeyError:
            Logger().getLogger().error("MongoDB ERROR: Duplicate Key Error")
            return({"message":"Duplicate Key Error"},200)
        except Exception as e:
            Logger().getLogger().error("MongoDB:updateDetails"+str(e))
            raise Exception("MongoDB:updateDetails:"+str(e))
    
    def getDetails(self, query:dict):
        try:
            database = self.client[self.db_name]
            collection = database[self.collection_name]
            result = collection.find(query)
            Logger().getLogger().info("**********Records fetched from MongoDB**********")
            # Logger().getLogger().info(result.inserted_id)
            return result
        except Exception as e:
            Logger().getLogger().error("MongoDB:getDetails"+str(e))
            raise Exception("MongoDB:getDetails:"+str(e))
