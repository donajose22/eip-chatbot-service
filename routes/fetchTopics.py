from flask import Blueprint,request, jsonify
from src.mySqlConnection import mySqlConnection
from config.config import global_config
import requests
import json

config = global_config

ifetchtopics= Blueprint('ifetchtopics', __name__)

@ifetchtopics.route("/topics",methods=["GET"])
def fetch_topics():
    try:
        # mysql connection
        host = config["database_schema_mysql"]["host"]
        port = config["database_schema_mysql"]["port"]
        username = config["database_schema_mysql"]["username"]
        password = config["database_schema_mysql"]["password"]
        database = config["database_schema_mysql"]["database"]
        
        topics_query = "SELECT * FROM topics_info;"
        mySql = mySqlConnection(host, port, username, password, database)
        topics = mySql.execute_query(topics_query)
        
        return topics
    except Exception as e:
        print(e)