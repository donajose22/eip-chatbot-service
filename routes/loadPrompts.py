from flask import Blueprint,request, jsonify, session
from src.mySqlConnection import mySqlConnection
from src.createPrompt import create_inference_prompt, create_query_prompt, create_summary_prompt, create_supervisor_prompt
from config.config import global_config
import requests
import json

config = global_config

iloadprompts= Blueprint('iloadprompts', __name__)

def load_json(file_path='prompts/prompt_templates.json'):
    with open(file_path, 'r') as f:
        json_data = json.load(f)
    return json_data

def save_json(json_data, file_path='prompts/prompt_templates.json'):
    with open(file_path, 'w') as f:
        json.dump(json_data, f, indent=4)

@iloadprompts.route("/load/<topic>",methods=["GET"])
def load_prompts(topic):
    
    try:
        # mysql connection
        host = config["database_schema_mysql"]["host"]
        port = config["database_schema_mysql"]["port"]
        username = config["database_schema_mysql"]["username"]
        password = config["database_schema_mysql"]["password"]
        database = config["database_schema_mysql"]["database"]
        
        print("----GETTING DATABASE_ID--------")
        topics_query = "SELECT * FROM topics_info;"
        mySql = mySqlConnection(host, port, username, password, database)
        topics = mySql.execute_query(topics_query)
        
        database_id = 1
        for row in topics:
            if(str(row[0])==topic):
                database_id = row[2]
        print("--------DATABASE_ID--------"+ str(database_id))
        
        create_prompts_flag = True
        print("--------LOADING JSON FILE----------")
        json_data = load_json()
        
        if('database_id' in json_data.keys()):
            if(json_data['database_id'] is None):
                if('topic' in json_data.keys() and json_data['topic']==topic):
                    create_prompts_flag = False
            elif(json_data['database_id'] ==  database_id):
                create_prompts_flag = False
        
        print("create_prompts_flag : "+str(create_prompts_flag))
        
        if(create_prompts_flag):
            print("--------CREATING PROMPTS----------")
            create_supervisor_prompt(topic, database_id)
            create_inference_prompt()
            create_summary_prompt(topic, database_id)
            print("----------CREATED PROMPTS-------------------")
            print("-----ADDING TOPIC AND DATABASE ID TO JSON FILE--------")
            json_data = load_json()
            json_data['topic'] = topic
            json_data['database_id'] = database_id
            save_json(json_data)
        else:
            print("PROMPTS ALREADY SAVED IN FILE")        

        return "Successfully Loaded"
    except Exception as e:
        return "Loading Failed"
    