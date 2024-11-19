from flask import Blueprint,request, jsonify
import datetime
import json
from langchain_sdk.Langchain_sdk import LangChainCustom 
import sys
import requests
from src.apigee import get_access_token
from config.config import global_config
from src.mongoDbConnection import mongoDbConnection

# inference= Blueprint('inference', __name__)
config = global_config

def generate_model(conversation_history, prompt):
    client_id = config["genai_client_id"]
    client_secret = config["genai_secret"]

    llm = LangChainCustom(client_id=client_id,
                            client_secret=client_secret,
                            model="gpt-4-turbo",
                            temperature=1,
                            chat_conversation=True,
                            conversation_history = conversation_history,
                            system_prompt=prompt)
                            # system_prompt='Summarize everything in 100 words.')
    return llm
    

def retrieve_documents(prompt):
    config = global_config
    retriever_api_url = config["retriever_url"]

    headers = {
        'Authorization': f'Bearer {get_access_token()}',
        'Content-Type': 'application/json'
        }
    proxies=config["proxies"]
    body = '''{
    "prompt": "'''+prompt+'''",
    "metadata": {
        "top_k": 3,
        "sources": [
        "'''+config["eipteam_contract_id"]+'''",
        "'''+config["rdse_contract_id"]+'''"
        ],
        "user_email": "dona.jose@intel.com"
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
        raise

    return response.json()

def create_prompt(query_text, documents):

    prompt = '''Using the information from the provided relevant documents, please answer the following query. 
    Make sure to reference the sources in your response. Provide the links when citing the sources. 
    If you think the provided documents are not relevant to the query, refer to the conversation history to answer the query.
    If you don't know the answer, just say that you don't know, don't try to make up an answer. 
    
    Query : '''+query_text+'''

    Relevant Documents and Sources:

    Document : '''+documents[0]['Result:']+''' 
    \nSource: ''' + documents[0]['Source'] +'''

    \nDocument : '''+documents[1]['Result:']+''' 
    \nSource : ''' + documents[1]['Source'] +'''

    \nDocument : '''+documents[2]['Result:']+''' 
    \nSource : ''' + documents[2]['Source'] +'''

    '''
    return prompt

def format_json(text):
    text = text[2:-1]
    text = text.replace("\\'", "'").replace('\\"', '"').replace("\\\\n", "\n")
    json_data = json.loads(text, strict=False)
    return json_data

def update_db(query_text, prompt, response, feedback):
    connection_string = config["chat_db_url"]
    collection_name = config["chat_collection_name"]
    mongoClient = mongoDbConnection(connection_string, collection_name)
    record = {
        "user_wwid": "",
        "username": "",
        "query": query_text,
        "prompt": prompt,
        "response": response,
        "feedback": feedback, 
        "time": datetime.datetime.now()
    }
    resp = mongoClient.addDetails(record)

# @inference.route("/inference/<query_text>",methods=["GET"])
def generate_response(query_text, conversation=[]):

    # retrieve relevant wiki documents
    documents = retrieve_documents(query_text)

    # create prompt
    prompt = create_prompt(query_text, documents['top_k_results']['response'])

    llm = generate_model(conversation_history=conversation, prompt=prompt)

    response = llm.invoke(prompt)

    # convert response to json format
    json_data = format_json(response)

    # update conversation history
    conversation = json_data["conversation"]

    # update_db(query_text, prompt, json_data['currentResponse'], "" )

    return [prompt, json_data['currentResponse']]


