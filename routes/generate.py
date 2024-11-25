from flask import Blueprint,request, jsonify
from langchain_sdk.Langchain_sdk import LangChainCustom 
from src import inference, nltosql, formater
from src.mongoDbConnection import mongoDbConnection
from src.apigee import get_access_token
from config.config import global_config
import datetime
import json

config = global_config

igenerate= Blueprint('igenerate', __name__)

conversation = [
    {
    "content": "Summarize everything in 100 words.",
    "role": "system"
  }
]

def generate_model(prompt = None):
    client_id = config["genai_client_id"]
    client_secret = config["genai_secret"]

    if(prompt==None):
        prompt = 'Summarize everything in 100 words.'

    llm = LangChainCustom(client_id=client_id,
                            client_secret=client_secret,
                            model="gpt-4-turbo",
                            temperature=1,
                            chat_conversation=True,
                            conversation_history = [],
                            system_prompt=prompt)
                            # system_prompt=prompt
                            
    return llm

def create_prompt_supervisor(question):

    prompt = f'''

    You are an intelligent assistant that evaluates user queries to decide the best way to respond. Based on the user's question, determine if it is more appropriate to provide a direct response or to generate an SQL query that can be executed on a database.
    If the question only contains a an integer value, it is implied that it is dms id/alt id of a ticket. It requires an SQL query.
    Please analyze the following user query:

    {question}

    Respond with:

    0 if a direct response is sufficient.
    1 if an SQL query should be generated instead.
    Consider the nature of the query and the information required to provide a complete answer.

    Always respond with 0 or 1.

    Examples:
    \n\n
    1. What is EIP?
    Expected Response: 0
    \n 
    2. How to get IP from IPX?
    Expected Response: 0
    \n
    3. How many entries are present in FlowStep?, 
    Expected Response: 1
    \n
    4. What all tickets are in complete status?, 
    Expected Response: 1
    \n
    5. How many flow steps where the recipient is Cadence, 
    Expected Response: 1
    \n
    6. Status of ticket 123456789
    Expected Response: 1
    \n
    7. 123456789
    Expected Response: 1
    '''
    return prompt

def format_json(text):
    try:
        text = text[2:-1]
        text = text.replace("\\'", "'").replace('\\"', '"').replace("\\\\n", "\n")
        json_data = json.loads(text, strict=False)
        return json_data
    except Exception as e:
        raise Exception("generate:format_json:"+str(e))


def update_db(query_text, prompt, response, sql_query=None, feedback=None):
    config = global_config
    connection_string = config["chat_db_url"]
    collection_name = config["chat_collection_name"]
    mongoClient = mongoDbConnection(connection_string, collection_name)
    record = {
        "user_wwid": "",
        "username": "",
        "query": query_text,
        "prompt": prompt,
        "response": response,
        "sql_query": sql_query,
        "feedback": feedback, 
        "time": datetime.datetime.now()
    }
    resp = mongoClient.addDetails(record)
    # print(resp)


@igenerate.route("/generate/<query_text>",methods=["GET"])
def generate(query_text):

    # json_response = {
    #     "response": "current_response",
    #     "sql_query": "1"
    # }

    # return jsonify(json_response)

    global conversation
    sql_query = None

    # print("------------PREVIOUS CONVERSATION----------------------")
    # print(conversation)
    # print()
    conversation = []

    # create prompt check if inference or nl to sql
    prompt = create_prompt_supervisor(query_text)

    # executing 5 times in case of incorrect response
    choice = "b''"
    count = 5
    while(choice=="b''" and count>0):
        llm = generate_model(prompt)
        choice = llm.invoke(prompt)
        count-=1

    try:
        # convert response to json format
        json_data = format_json(choice)
        is_sql_query = json_data['currentResponse']
    except Exception as e:
        is_sql_query = "0"

    try:
        if(is_sql_query == "0"):
            print("***********************INFERENCE*************************************************")
            response_prompt, response = inference.generate_response(query_text, conversation)
            # Formatting response to html format
            current_response = formater.format(query_text, response)

        elif(is_sql_query == "1"):
            print("***********************NL TO SQL*************************************************")
            is_sql_query = 1
            response_prompt, sql_query, response = nltosql.generate_response(query_text)
            current_response = response
    except Exception as e:
        raise Exception("Incorrect response from llm model: "+is_sql_query)
        

    # update conversation history

    current_conversation = [
        {
            'role': 'user',
            'content': query_text
        },
        {
            'role': 'assistant',
            'content': current_response
        }
    ]
    conversation.append(current_conversation)

    # Update conversation in Database
    update_db(query_text, response_prompt, response, sql_query)

    # print(jsonify(current_response))

    json_response = {
        "response": current_response,
        "is_sql_query": is_sql_query,
        "sql_query": sql_query
    }

    return jsonify(json_response)
