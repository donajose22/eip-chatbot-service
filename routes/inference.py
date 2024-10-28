from flask import Blueprint,request, jsonify
import datetime
import json
from langchain_sdk.Langchain_sdk import LangChainCustom 
import sys
import requests
from src.apigee import get_access_token
from config.config import global_config
from src.mongoDbConnection import mongoDbConnection


inference= Blueprint('inference', __name__)

def generate_model(conversation_history, prompt):
    config = global_config
    client_id=config["apigee"]["client_id"]
    client_secret=config["apigee"]["client_secret"]
    client_id = "d36a38f9-f7ff-4052-9660-9d1dd493c297"
    client_secret = "G6c8Q~110PnYPcEK24RCCdapuGjtdnnBr6bj-aHr"

    llm = LangChainCustom(client_id=client_id,
                            client_secret=client_secret,
                            model="gpt-4-turbo",
                            temperature=1,
                            chat_conversation=True,
                            conversation_history = conversation_history,
                            system_prompt=prompt)
                            # system_prompt='Summarize everything in 100 words.')
    return llm
    


conversation = [
    {
    "content": "Summarize everything in 100 words.",
    "role": "system"
  }
]

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
        "de7170a9-f3b4-442d-98ff-b9490058f48d",
        "ebaa280a-0a23-45c7-a09d-ceb2becc620b"
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
        # print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve wiki docs: {e}")
        raise

    return response.json()

def create_prompt(query_text, documents):

    prompt = '''Using the information from the provided relevant documents, please answer the following query. Make sure to reference the sources in your response. Provide the links when citing the sources. If you don't know the answer, just say that you don't know, don't try to make up an answer. 
    
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
    print(text)
    json_data = json.loads(text, strict=False)
    return json_data

def update_db(query_text, prompt, response, feedback):
    config = global_config
    connection_string = config["dms_chat_db_url"]
    collection_name = config["dms_chat_collection_name"]
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
    print(resp)

@inference.route("/inference/<query_text>",methods=["GET"])
def generate_response(query_text):

    global conversation
    #print("Previous conversation: ", conversation)

    # retrieve relevant wiki documents
    documents = retrieve_documents(query_text)

    # create prompt
    prompt = create_prompt(query_text, documents['top_k_results']['response'])

    # print(prompt)

    llm = generate_model(conversation_history=conversation, prompt=prompt)

    response = llm.invoke(prompt)
    print(response)
    # print(type(response))
    # return response

    # convert response to json format
    json_data = format_json(response)
    # json_data = response

    # update conversation history
    conversation = json_data["conversation"]

    update_db(query_text, prompt, json_data['currentResponse'], "" )

    # return the response
    print(json_data['currentResponse'])
    return jsonify(json_data["currentResponse"])

