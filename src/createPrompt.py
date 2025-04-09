from flask import Flask, session
from src.sendEmail import send_email
from src.mySqlConnection import mySqlConnection
from src.mongoDbConnection import mongoDbConnection
from config.config import global_config
import json


config = global_config

def send_error_email(error, message):
    print("SENDING EMAIL")
    sender_email = config["eip_chatbot_email"]
    sender_password = config["eip_chatbot_password"]
    receiver_emails = config["receiver_emails"]
    subject = "ERROR IN EIP CHATBOT SERVICE"
    body = str(error)+"\n"+message
    send_email(sender_email, sender_password, receiver_emails, subject, body)

def load_json(file_path='prompts/prompt_templates.json'):
    with open(file_path, 'r') as f:
        json_data = json.load(f)
    return json_data

def save_json(json_data, file_path='prompts/prompt_templates.json'):
    with open(file_path, 'w') as f:
        json.dump(json_data, f, indent=4)

def create_supervisor_prompt(topic, database_id):
    try:
        # load from json file
        json_data = load_json()

        # mongodb connection
        connection_string = config["prompt_templates_db_url"]
        db_name = config["prompt_templates_db_name"]
        collection_name = config["prompt_templates_collection_name"]

        mongoClient = mongoDbConnection(connection_string, db_name, collection_name)
        
        query = {'template_name':'supervisor'}
        # get prompt template
        cursor = mongoClient.getDetails(query)
        template = cursor[0]['template']
        
        try:
            query_prompt = """"""
            if(database_id is not None): # sql database question
                query = {'template_name':'direct_response'}
                # get prompt template
                cursor = mongoClient.getDetails(query)
                direct_response_prompt = cursor[0]['template']
                query_prompt = direct_response_prompt + create_query_prompt(topic, database_id)
            else:  # jira questions
                query = {'template_name':'jira_query'}
                # get prompt template
                cursor = mongoClient.getDetails(query)
                query_prompt = cursor[0]['template']
                
        except Exception as e:
            print(e)
        supervisor_prompt = template + query_prompt
        
        # Adding space to add the question
        supervisor_prompt = supervisor_prompt + '\n\nQuestion: $question\n'
        
        # add template to json object
        json_data['supervisor'] = supervisor_prompt
        print("Added supervisor to json file")
        # save json object
        save_json(json_data)
    except Exception as e:
        print("ERROR:generate:create_supervisor_prompt: "+str(e))
        send_error_email("ERROR:generate:create_supervisor_prompt: "+str(e), "Creating sueprvisor prompt")

def create_query_prompt(topic, database_id):
    try:
        # # load from json file
        # json_data = load_json()
        
        # mongodb connection
        connection_string = config["prompt_templates_db_url"]
        db_name = config["prompt_templates_db_name"]
        collection_name = config["prompt_templates_collection_name"]

        mongoClient = mongoDbConnection(connection_string, db_name, collection_name)
        
        query = {'template_name':'query'}
        
        # get prompt template
        cursor = mongoClient.getDetails(query)
        template = cursor[0]['template']
        
        # mysql connection
        host = config["database_schema_mysql"]["host"]
        port = config["database_schema_mysql"]["port"]
        username = config["database_schema_mysql"]["username"]
        password = config["database_schema_mysql"]["password"]
        database = config["database_schema_mysql"]["database"]
        
        mySql = mySqlConnection(host, port, username, password, database)
        
        # fetch details of database
        fetch_database_query = f"SELECT name, description, responseInstructions, queryInstructions, tableRelations FROM database_info WHERE id = {database_id};"
        database_query_results = mySql.execute_query(fetch_database_query)
        database = database_query_results[0]
        database_name = database[0]
        database_description = database[1]
        response_format = database[2]
        query_instructions = database[3]
        table_relations = database[4]
        
        # get table and fields information
        database_information = ""
        
        fetch_tables_query = f"SELECT * FROM table_info WHERE database_id='{database_id}'"
        tables = mySql.execute_query(fetch_tables_query)
        
        table_count = 1
        
        for table in tables:
            table_id = table[0]
            database_information += f"\n\nTable {table_count}: {table[2]}"
            if(table[3]!=''):
                database_information += f"\n Description: {table[3]}"
            
            database_information += "\n\nFields: "
            fetch_fields_query = f"SELECT * FROM field_info WHERE table_id='{table_id}'"
            fields = mySql.execute_query(fetch_fields_query)
            
            field_count = 1
            for field in fields:
                database_information += f"\n{field_count}. {field[2]} - Type: {field[3]}"
                if(field[4]!=''):
                    database_information += f", Description: {field[4]}"
                
                field_count+=1
            
            table_count+=1
        
        # fetch examples
        examples_text = ""
        
        fetch_examples_query = f"SELECT question, response from examples WHERE topic_id = {topic} AND type = 'query';"
        examples = mySql.execute_query(fetch_examples_query)
        
        example_count = 1
        for example in examples:
            examples_text += f"\n\nExample Input {example_count}: {example[0]}"
            examples_text += f"\nExample Response {example_count}: {example[1]}"
            example_count+=1
        
        # compile prompt template
        prompt = template.format(database_name, database_description, database_name, query_instructions, response_format, database_information, table_relations,examples_text)
        # print(prompt)
        return prompt
        
        # # add template to json object
        # json_data['query'] = prompt
        
        # # save json object
        # save_json(json_data)
    except Exception as e:
        print("ERROR:generate:create_query_prompt: "+str(e))
        send_error_email("ERROR:generate:create_query_prompt: "+str(e), "Creating query prompt")

def create_inference_prompt():
    try:
        # load from json file
        json_data = load_json()
        
        # mongodb connection
        connection_string = config["prompt_templates_db_url"]
        db_name = config["prompt_templates_db_name"]
        collection_name = config["prompt_templates_collection_name"]

        mongoClient = mongoDbConnection(connection_string, db_name, collection_name)
        
        query = {'template_name':'inference'}
        
        # get prompt template
        cursor = mongoClient.getDetails(query)
        template = cursor[0]['template']
        prompt = template

        # add template to json object
        json_data['inference'] = prompt
        print("added inference to json file")
        # save json object
        save_json(json_data)  
    except Exception as e:
        print("ERROR:generate:create_inference_prompt: "+str(e))
        send_error_email("ERROR:generate:create_inference_prompt: "+str(e), "Creating inference prompt")

def create_summary_prompt(topic, database_id):
    try:
        print("inside summary prompt")
        # load from json file
        json_data = load_json()
        
        # mongodb connection
        connection_string = config["prompt_templates_db_url"]
        db_name = config["prompt_templates_db_name"]
        collection_name = config["prompt_templates_collection_name"]

        mongoClient = mongoDbConnection(connection_string, db_name, collection_name)
        
        # mysql connection
        host = config["database_schema_mysql"]["host"]
        port = config["database_schema_mysql"]["port"]
        username = config["database_schema_mysql"]["username"]
        password = config["database_schema_mysql"]["password"]
        database = config["database_schema_mysql"]["database"]
        
        mySql = mySqlConnection(host, port, username, password, database)
        
        if(database_id is None):
            print("Database id is none. topic = "+topic)
            if(topic == "2"): # JQL Summary
                query = {'template_name': 'jql_summary'}
                # get prompt template
                cursor = mongoClient.getDetails(query)
                template = cursor[0]['template']
                query_summary_prompt = template
        else:
            print("database id is not none")
            query = {'template_name':'sql_summary'}
            
            # get prompt template
            cursor = mongoClient.getDetails(query)
            template = cursor[0]['template']
            
            # fetch details of database
            fetch_database_query = f"SELECT name, description, summaryInstructions, tableRelations FROM database_info WHERE id = {database_id};"
            database_query_results = mySql.execute_query(fetch_database_query)
            database = database_query_results[0]
            database_name = database[0]
            database_description = database[1]
            summary_instructions = database[2]
            table_relations = database[3]
            
            # get table and fields information
            database_information = ""
            
            fetch_tables_query = f"SELECT * FROM table_info WHERE database_id='{database_id}'"
            tables = mySql.execute_query(fetch_tables_query)
            
            table_count = 1
            
            for table in tables:
                table_id = table[0]
                database_information += f"\n\nTable {table_count}: {table[2]}"
                if(table[3]!=''):
                    database_information += f"\n Description: {table[3]}"
                
                database_information += "\n\nFields: "
                fetch_fields_query = f"SELECT * FROM field_info WHERE table_id='{table_id}'"
                fields = mySql.execute_query(fetch_fields_query)
                
                field_count = 1
                for field in fields:
                    database_information += f"\n{field_count}. {field[2]} - Type: {field[3]}"
                    if(field[4]!=''):
                        database_information += f", Description: {field[4]}"
                    
                    field_count+=1
                
                table_count+=1
        
                # fetch summary examples
                summary_examples_text = ""
                
                fetch_summary_examples_query = f"SELECT question, response from examples WHERE topic_id = {topic} AND type = 'summary';"
                summary_examples = mySql.execute_query(fetch_summary_examples_query)
        
                example_count = 1
                for example in summary_examples:
                    summary_examples_text += f"\n\nExample Input {example_count}: {example[0]}"
                    summary_examples_text += f"\nExample Response {example_count}: {example[1]}"
                    example_count+=1
                    
                query_summary_prompt = template.format(database_name, database_description, database_name, summary_instructions, database_information, table_relations, summary_examples_text)
        
        # html instructions template
        query = {'template_name':'html_instruction'}
            
        # get prompt template
        cursor = mongoClient.getDetails(query)
        template = cursor[0]['template']
            
        # fetch html examples
        html_examples_text = ""
        fetch_html_examples_query = f"SELECT question, response from examples WHERE topic_id = {topic} AND type = 'html';"
        html_examples = mySql.execute_query(fetch_html_examples_query)

        example_count = 1
        for example in html_examples:
            html_examples_text += f"\n\nExample Input {example_count}: {example[0]}"
            html_examples_text += f"\nExpected HTML Output {example_count}: {example[1]}"
            example_count+=1

        html_instructions_prompt = template.format(html_examples_text)
        prompt = query_summary_prompt + html_instructions_prompt

        # add template to json object
        json_data['summary'] = prompt
        print("added summary to json file")
        # save json object
        save_json(json_data)
    except Exception as e:
        print("ERROR:generate:create_summary_prompt: "+str(e))
        send_error_email("ERROR:generate:create_summary_prompt: "+str(e), "Creating summary prompt")

