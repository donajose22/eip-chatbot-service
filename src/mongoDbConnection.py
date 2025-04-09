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
            print("**********Connected to DB**********")
        except Exception as e:
            print(e)
            if self.client is not None:
                self.client.close()
    

    def addDetails(self, data:dict):
        try:
            database = self.client[self.db_name]
            collection = database[self.collection_name]
            result = collection.insert_one(data)
            print("**********Record added to MongoDB**********")
            # print(result.inserted_id)
            return result
        except pymongo.errors.DuplicateKeyError:
            print("MongoDB ERROR: Duplicate Key Error")
            return({"message":"Duplicate Key Error"},200)
        except Exception as e:
            print("MongoDB:addDetails"+str(e))
            raise Exception("MongoDB:addDetails:"+str(e))
    
    def updateDetails(self, _id, record:dict):
        try:
            database = self.db_name
            collection = database[self.collection_name]
            data = {'$set': record}
            result = collection.update_one(_id, data)
            print("**********Record Updated*************")
        except pymongo.errors.DuplicateKeyError:
            print("MongoDB ERROR: Duplicate Key Error")
            return({"message":"Duplicate Key Error"},200)
        except Exception as e:
            print("MongoDB:updateDetails"+str(e))
            raise Exception("MongoDB:updateDetails:"+str(e))
    
    def getDetails(self, query:dict):
        try:
            database = self.client[self.db_name]
            collection = database[self.collection_name]
            result = collection.find(query)
            print("**********Records fetched from MongoDB**********")
            # print(result.inserted_id)
            return result
        except Exception as e:
            print("MongoDB:getDetails"+str(e))
            raise Exception("MongoDB:getDetails:"+str(e))


# class MongoDbConnection():
#     def __init__(self,logger,conn_details):
#         """Connect to MongoDB"""
#         self.collection_name="WrongDocumentId"
#         conn_string=conn_details["db_string"]
#         self.conn_details=conn_details
#         self.logger = logger
#         if("VCAP_APPLICATION" in os.environ):
#             if (loads(os.environ["VCAP_APPLICATION"])["space_name"].lower()=="production"):
#                 self.collection_name="WrongDocumentIdProd"
#         try:
#             self.client = pymongo.MongoClient(conn_string, tls=True, tlsAllowInvalidCertificates=False, tlsCAFile="IntelSHA256RootCA-base64.crt")
#             print("Connected to DB")
#         except Exception as e:
#             emailAPIConnection(self.logger,self.conn_details).sendMail(({
#                     "type":"error",
#                     "subject":"Error in CreateDACronjob",
#                     "body":"MongoDbConnection:__init__:"+format_exc()
#                 }))
#             return(e)