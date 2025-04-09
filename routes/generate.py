from flask import Flask, Blueprint,request, jsonify, session
from langchain_sdk.Langchain_sdk import LangChainCustom 
from src.mySqlConnection import mySqlConnection
from src.mongoDbConnection import mongoDbConnection
from src.loadModel import load_model
from src.ticketStatus import get_ticket_details
from src.executeJql import execute_jql_query
from src.sendEmail import send_email
from config.config import global_config
from src.apigee import get_apigee_access_token
from string import Template
import requests
import json
import time
import datetime

config = global_config
app = Flask(__name__)
app.secret_key = config['app_secret_key']

igenerate= Blueprint('igenerate', __name__)

host = config["eda_ip_tracker_host"]
port = config["eda_ip_tracker_port"]
username = config["eda_ip_tracker_username"]
password = config["eda_ip_tracker_password"]
db = config["eda_ip_tracker_database"]

def retrieve_documents(prompt):
    config = global_config
    retriever_api_url = config["retriever_url"]

    headers = {
        'Authorization': f'Bearer {get_apigee_access_token()}',
        'Content-Type': 'application/json'
        }
    
    proxies=config["proxies"]
    body = '''{
    "prompt": "'''+prompt+'''",
    "metadata": {
        "top_k": 3,
        "sources": [
        "'''+config["eipteam_contract_id"]+'''",
        "'''+config["rdse_contract_id"]+'''",
        "'''+config["disclosures_contract_id"]+'''"
        ],
        "user_email": "'''+config["user_email"]+'''"
    }
    }'''

    try:
        response = requests.post(retriever_api_url, 
                                 headers=headers, 
                                 data=body,
                                 proxies=proxies)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve wiki docs: {e}")
        raise e

    return response.json()

def load_template(type, file_path='prompts/prompt_templates.json'):
    with open(file_path, 'r') as f:
        json_data = json.load(f)
    return json_data[type]

def load_supervisor_prompt(question):
    supervisor_prompt_template = load_template("supervisor")
    
    template_string = Template(supervisor_prompt_template)
    supervisor_prompt = template_string.substitute(question=question)
    
    return supervisor_prompt

def load_query_prompt(question):
    query_prompt_template = load_template("query")
    
    template_string = Template(query_prompt_template)
    query_prompt = template_string.substitute(question=question)
    
    return query_prompt

def load_inference_prompt(question, documents):
    inference_prompt_template = load_template("inference")
    template_string = Template(inference_prompt_template)
    inference_prompt = template_string.substitute(question=question, document1=documents[0]['Result:'], source1=documents[0]['Source'], document2=documents[1]['Result:'], source2=documents[1]['Source'], document3=documents[2]['Result:'], source3=documents[2]['Source'])
    
    return inference_prompt

def load_summary_prompt(question, query, query_results):
    summary_prompt_template = load_template("summary")
    
    template_string = Template(summary_prompt_template)
    summary_prompt = template_string.substitute(question=question, query=query, query_results=query_results)
    
    return summary_prompt

def update_db(question, prompt=None, response=None, query=None, feedback=None, error=None):
    config = global_config
    connection_string = config["chat_db_url"]
    db_name = config["chat_db_name"]
    collection_name = config["chat_collection_name"]
    resp=None
    try:
        mongoClient = mongoDbConnection(connection_string, db_name, collection_name)
        record = {
            "user_wwid": "",
            "username": "",
            "query": question,
            "prompt": prompt,
            "response": response,
            "query": query,
            "error": error,
            "feedback": feedback, 
            "time": datetime.datetime.now()
        }
        resp = mongoClient.addDetails(record)
        # print(resp)
        return resp
    except Exception as e:
        print("Error:generate:update_db: "+str(e))
        raise e

def format_json(text):
    try:
        byte_data = eval(text)
        json_str = byte_data.decode("utf-8")
        json_data = json.loads(json_str)
        # text = text[1:]
        # text = text.replace("\\'", "'").replace('\\"', '"').replace("\\\\n", "\n")
        # print(text)
        # json_data = json.loads(text, strict=False)
        return json_data
    except Exception as e:
        print("ERROR:format_json:"+str(e))
        raise e

def validate_json(json_string):
    # Checking if the supervisor response is a valid json as per the given instructions.
    try:
        # Attempt to load the JSON string
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        return False, f"Invalid JSON: {e}"

    # Check for required fields
    print("checking required fields")
    required_fields = ['type']
    for field in required_fields:
        if field not in data:
            print(f"Missing required field: {field}")
            return False, f"Missing required field: {field}"
    
    # Check for 'response' and 'id' field if 'type' is 'status' or 'other
    if data['type'] == 'other' and 'response' not in data:
        print("Missing required field: response (for type 'other')")
        return False, "Missing required field: response (for type 'other')"
    if data['type'] == 'status' and 'response' not in data:
        print("Missing required field: response (for type 'status')")
        return False, "Missing required field: response (for type 'status')"
    if data['type'] == 'status' and 'id' not in data:
        print("Missing required field: id (for type 'status')")
        return False, "Missing required field: id (for type 'status')"
    if data['type'] == 'jql' and 'response' not in data:
        print("Missing required field: response (for type 'jql')")
        return False, "Missing required field: response (for type 'jql')"
    print("JSON is valid and contains all required fields.")
    return True, ""

def send_error_email(error, question):
    print("SENDING EMAIL")
    sender_email = config["eip_chatbot_email"]
    sender_password = config["eip_chatbot_password"]
    receiver_emails = config["receiver_emails"]
    subject = "ERROR IN EIP CHATBOT SERVICE"
    body = str(error)+"\nQuestion: "+question
    send_email(sender_email, sender_password, receiver_emails, subject, body)

@igenerate.route("/generate/<question>",methods=["GET"])
def generate(question):    
    global conversation
    
    json_response = {
        "id": None,
        "response": "Something went wrong while processing your request. Please try again later.",
        "is_query": 0,
        "query": None,
        "time_taken": None,
    }
    prompt=None
    resp=None
    is_query = 0
    query=None
    error=None

    print("Question: ",question)
    
    try:
        llm = load_model()
        
        start_time = time.time()
        # create prompt 
        supervisor_prompt = load_supervisor_prompt(question)
        print("loaded supervisor prompt")
        print('-------------INVOKING SUPERVISOR MODEL----------------')
        s = time.time()
        response=llm.invoke(supervisor_prompt)
        et = time.time()
        print("Time taken by supervisor: ", et-s)
        print("--------------RECEIVED RESPONSE---------------")
        
        response = format_json(response)
        print(response['currentResponse'])        
        try:
            valid_json, message=validate_json(response['currentResponse'])
        except Exception as e:
            print("ERROR:generate:validate_json: "+str(e))
            send_error_email(str(e), question)
            update_db(question, prompt=supervisor_prompt, response=response, error=str(e))
            return json_response
        
        if(valid_json==False):
            print("ERROR:generate::Incorrect/Invalid JSON response")
            send_error_email("ERROR:generate::Incorrect/Invalid JSON response:"+message, question)
            update_db(question, prompt=supervisor_prompt, response=response, error="ERROR:generate::Incorrect/Invalid JSON response")
            return json_response
        
        response = json.loads(response['currentResponse'])        
        print("SUPERVISOR RESPONSE: "+str(response))
        
        if(response["type"]=="inference"):
            try: 
                # retrieve relevant wiki documents
                print("===================RETRIEVING WIKI DOCUMENTS==============================")
                s = time.time()
                documents = retrieve_documents(question)
                et = time.time()
                print("time taken for retrieving: ", et-s)
                print("RETRIEVED DOCUMENTS: "+str(documents))
            except Exception as e:
                print("ERROR:generate:retreiving wiki documents: "+str(e))
                send_error_email(str(e), question)
                update_db(question, error=str(e))
                return json_response

            print("------SUMMARIZING RETRIEVED DOCUMENTS------------")
            s = time.time()
            prompt = load_inference_prompt(question, documents['top_k_results']['response'])
            print("SUMMARIZE PROMPT CREATED")
            inference_response = llm.invoke(prompt)
            et = time.time()
            print("Time taken for inference: ", et-s)
            
            # inference_response = json.loads(inference_response)
            inference_response = format_json(inference_response)
            resp = inference_response['currentResponse']
        elif(response["type"] =="jql"): # if question is regarding JIRA
            is_query = 1
            query = response["response"]
            
            # Execute the sql query
            try:
                print("--------------EXECUTING THE QUERY--------------")
                s = time.time()
                result_status, query_results = execute_jql_query(query)
                et = time.time()
                print("Time taken to execute sql query: ", et-s)
            except Exception as e:
                print("ERROR:generate:jql: "+str(e))
                send_error_email(str(e), question)
                return json_response

            if(result_status == 200):
                issues = []
                query_result_issues = query_results['issues']
                for result_issue in query_result_issues:
                    issue = {}
                    issue['expand'] = result_issue['expand']
                    issue['id'] = result_issue['id']
                    issue['self'] = result_issue['self']
                    issue['key'] = result_issue['key']
                    issue['fields'] = {}
                    for key in result_issue['fields'].keys():
                        if(result_issue['fields'][key] is not None):
                            # print(result_issue[key], type(result_issue[key]))
                            issue['fields'][key] = result_issue['fields'][key]
                    issues.append(issue)
                query_results['issues'] = issues
            else:
                is_query = 0
                print(query_results)
            
            # setting the limit for query results. Query results are being limited to 18500 words.
            query_results = str(query_results)
            word_limit = 18500  # the entire prompt should not go beyond 20000 words
            if(len(query_results.split(" ")) > 18500):
                query_results_size = len(query_results.split(" "))
                print(f'Size of query results: {query_results_size} words')
                query_results = ' '.join(query_results.split(" ")[:word_limit])
                query_results_size = len(query_results.split(" "))
                print(f'Size of query results after reduction: {query_results_size} words')
                
            # create summary prompt 
            summary_prompt = load_summary_prompt(question, query, query_results)
            print("loaded summary prompt")
            summary_prompt_size = len(summary_prompt.split(" "))
            print(f'Size of summary prompt: {summary_prompt_size} words')
            print('-------------INVOKING SUMMARY MODEL----------------')
            s = time.time()
            response=llm.invoke(summary_prompt)
            et = time.time()
            print("Time taken by summary generator: ", et-s)
            print("--------------RECEIVED RESPONSE---------------")
            response = format_json(response)
            if('currentResponse' in response.keys()):
                resp = response['currentResponse'] 
            else:
                print(response)
                if('StatusCode' in response.keys() and response['StatusCode']==400):
                    raise Exception(response['Message']) 
        else: # if question is regarding sql database
            is_query = 1
            query = response["response"]
            # Execute the sql query
            try:
                print("--------------EXECUTING THE QUERY--------------")
                s = time.time()
                mySql = mySqlConnection(host, port, username, password, db)
                query_results = mySql.execute_query(query)
                et = time.time()
                print("Time taken to execute sql query: ", et-s)
            except Exception as e:
                print("ERROR:generate:mySQL: "+str(e))
                send_error_email(str(e), question)
                update_db(question, error=str(e))
                return json_response
            
            sql_summary_prompt = load_summary_prompt(question, query, query_results)
            print("----------SUMMARIZING SQL QUERY RESULTS------------")
            s = time.time()
            sql_summary_response = llm.invoke(sql_summary_prompt)
            et = time.time()
            print("Time taken to summarize sql results: ", et-s)
            # sql_summary_response = json.loads(sql_summary_response)
            sql_summary_response = format_json(sql_summary_response)            
            sql_summary = sql_summary_response['currentResponse']
            
            if(response["type"]=="other"):
                resp = sql_summary
                
            elif(response["type"]=="status"):
                ticket_id = response["id"]
                s = time.time()
                try:
                    print("---------GETTING TICKET DETAILS--------------")
                    ticket_details = get_ticket_details(ticket_id)
                except Exception as e:
                    print("ERROR:generate:get_ticket_details: "+str(e))
                    send_error_email(str(e), question)
                    update_db(question, error=str(e))
                    return json_response
                et = time.time()
                print("Time taken to get ticket status details: ", et-s)
                if(ticket_details is not None):
                    resp = ticket_details+"<h3><b>Summary</b></h3>"+sql_summary
                else:
                    resp = sql_summary
        
        # Update conversation in Database
        print("---------UPDATING IN DB---------")
        try:
            result = update_db(question, prompt = prompt , response=resp, query=query)
            chat_id = result.inserted_id
        except Exception as e:
            print("ERROR:generate: "+str(e))
            send_error_email(str(e), question)
            return json_response
        
        end_time = time.time()
        execution_time = end_time - start_time
        print("EXECUTION TIME: ", execution_time)
        
        json_response["id"]=str(chat_id)
        json_response["response"]=resp
        json_response["is_query"]=is_query
        json_response["query"]=query
        json_response["time_taken"]="{:.1f}".format(execution_time)
        
        return json_response

    except Exception as e:
        print("ERROR:generate: "+str(e))
        send_error_email(str(e), question)
        update_db(question, error=str(e))
        return jsonify(json_response)

