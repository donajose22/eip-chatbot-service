from flask import Blueprint,request, jsonify
import datetime
import json
from langchain_sdk.Langchain_sdk import LangChainCustom 
import sys
import requests
from src.apigee import get_access_token
from src.loadModel import load_model
from . import formatter
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

def create_prompt(question, documents):

    prompt = '''Using the information from the provided relevant documents, please answer the following query. 
    Make sure to reference the sources in your response. Provide the links when citing the sources. 
    If you think the provided documents are not relevant to the query, refer to the conversation history to answer the query.
    If you don't know the answer, just say that you don't know, don't try to make up an answer. 

    Generate the response in proper html format according to the instructions given below. Refer to the examples provided.
    
    Query : '''+question+'''

    Relevant Documents and Sources:

    Document : '''+documents[0]['Result:']+''' 
    \nSource: ''' + documents[0]['Source'] +'''

    \nDocument : '''+documents[1]['Result:']+''' 
    \nSource : ''' + documents[1]['Source'] +'''

    \nDocument : '''+documents[2]['Result:']+''' 
    \nSource : ''' + documents[2]['Source'] +'''

    Instructions for generating response in html format.

    Do not modify any of the content. Only add the appropriate HTML tags wherever necessary.

    Do not include any <html> or <body> tags. The output should contain only the content and relevant HTML tags within the body of the page.

    If there are any SQL Queries in the text, it should be highlighted and emphasized.

    Paragraphs: Each paragraph should be separated by the <p></p> tags.

    Unordered Lists: Items in an unordered list should be denoted using the <ul> and <li> tags. Use - to mark list items in the original text and convert them to HTML list items.

    Ordered Lists: Items in an ordered list should be denoted using the <ol> and <li> tags. Convert numbered points in the text to an ordered list.

    Bold Important Words: Some words that are important or emphasized (such as terms, names, or concepts) should be enclosed in the <b></b> tags. You can infer the importance based on context. 
    Only highlight the important words once in the beginning. Emphasize at most 2 words/phrases in a sentence. Emphasize the main words that answer the question.

    Line Breaks: Use <br> where necessary for line breaks (i.e., where a paragraph should continue on a new line but does not require a full paragraph break).

    Images: If the text contains image URLs, use the <img> tag to insert the image with the src attribute. Ensure the image source URL is inserted properly, for example:
    <img src="URL_HERE" alt="Description of the image">

    Links: For any webpage URLs or references to external sources, use the <a> tag to create clickable links. The link should point to the source, and the anchor text should describe the content or provide context. The links should open in a new tab. For example:
    <a href="URL_HERE">Link Description</a>

    Headings: If the text contains headings or subheadings, use the appropriate heading tags (<h1>, <h2>, etc.) based on the hierarchy of the text. For example, major headings should use <h1>, subheadings should use <h2>, and so on.

    Additional Formatting: If there are any other formatting elements (such as italics, bold, etc.), make sure to convert them properly into HTML tags (<i></i> for italics, <b></b> for bold, etc.).

    Example Input:

    "Here is a sample paragraph. It's followed by a list of items:

    - Item one
    - Item two
    - Item three

    Also, visit this page for more information: www.example.com

    Here's an important image:
    http://example.com/sample-image.jpg"

    Expected HTML Output:

    "<p>Here is a sample paragraph. It's followed by a list of items:</p>

    <ul>
    <li>Item one</li>
    <li>Item two</li>
    <li>Item three</li>
    </ul>

    <p>Also, visit this page for more information: <a href="http://www.example.com">www.example.com</a></p>

    <p>Here's an important image:</p>
    <img src="http://example.com/sample-image.jpg" alt="Sample Image">"


    Do not include the <html> or <body> tags in the output. 
    Only highlight the main words/phrases that answer the question. Do not highlight/bold any unnecessary words.
    Do not include any additional text or quotes in the beginning or end of the response. No quotes or backticks.
    Do not truncate the response. Make sure all the information needed is present in the response.

    '''
    return prompt

def format_json(text):
    try:
        # text = text[2:-1]
        # text = text.replace("\\'", "'").replace('\\"', '"').replace("\\\\n", "\n")
        json_data = json.loads(text, strict=False)
        return json_data
    except Exception as e:
        print("ERROR:inference:format_json")
        raise e

# @inference.route("/inference/<question>",methods=["GET"])
def generate_response(question, conversation=[]):

    try: 
        # retrieve relevant wiki documents
        print("===================RETRIEVING WIKI DOCUMENTS==============================")
        documents = retrieve_documents(question)
    except Exception as e:
        print("ERROR:inference:generate_response: "+str(e))
        raise(e)

    # create prompt
    prompt = create_prompt(question, documents['top_k_results']['response'])

    # llm = generate_model(conversation_history=conversation, prompt=prompt)
    llm = load_model()

    print("=====================GENERATING RESPONSE===================================")
    response = llm.invoke(prompt)

    # convert response to json format
    try:
        json_data = format_json(response)
    except Exception as e:
        print("ERROR:inference:generate_response: "+str(e))
        raise e

    # update conversation history
    # conversation = json_data["conversation"]

    resp = json_data['currentResponse']
    # convert the text to html format
    # formatted_generated_response = formatter.format(question, json_data["currentResponse"])
    # resp = formatted_generated_response

    print("________________________________INFERENCE RESPONSE_____________________________________")
    print(resp)

    return [prompt, resp]
