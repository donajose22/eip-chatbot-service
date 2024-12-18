from flask import Blueprint,request, jsonify
from langchain_sdk.Langchain_sdk import LangChainCustom 
from src.mySqlConnection import mySqlConnection
from src.mongoDbConnection import mongoDbConnection
from src.ticketStatus import get_ticket_details
from src.sendEmail import send_email
from config.config import global_config
from src.apigee import get_access_token
import requests
import json
import time
import datetime

config = global_config

igenerate= Blueprint('igenerate', __name__)

host = config["eda_ip_tracker_host"]
port = config["eda_ip_tracker_port"]
username = config["eda_ip_tracker_username"]
password = config["eda_ip_tracker_password"]
db = config["eda_ip_tracker_database"]

conversation = [
    {
    "content": "Summarize everything in 100 words.",
    "role": "system"
  }
]

def generate_model(prompt = None):
    client_id = global_config["genai_client_id"]
    client_secret = global_config["genai_secret"]

    if(prompt==None):
        prompt = 'Summarize everything in 100 words.'
    llm = LangChainCustom(client_id=client_id,
                            client_secret=client_secret,
                            # model="gpt-4-turbo",
                            model = "gpt-4o",
                            temperature=1,
                            chat_conversation=True,
                            conversation_history = [],
                            system_prompt=prompt)
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

def create_supervisor_prompt(question):

    prompt = """

    You are an intelligent assistant that evaluates user queries to decide the best way to respond. Based on the user's question, determine if it is more appropriate to provide a direct response (inference) or to generate an SQL query that can be executed on a database.
    If the question only contains a an integer value, it is implied that it is dms id/alt id of a ticket. It requires an SQL query.
    Please analyze the following user query:

    Respond with a json object in the following format. It should have 3 fields: type, response and id.
    - type: can take three values ["inference", "status", "other"]. inference means that it requires a direct response. status/other implies that it requires the generation of an sql query to be executed on a database.
    - response: should contain the sql query (only in case of type = "status" or "other")
    - id: should contain the ticket id provided in the question (if there is one). Only if the type = "status", otherwise don't include this field.
    "{
    "type": "status",
    "response": "Select * from Flowsteps;",
    "id": "11166"
    }"
    
    In case of  DIRECT RESPONSE
    Response with the json
    "{
        "type": "inference"
    }"
    Do not add any addition text or information or quotes.

    In case of SQL QUERY
    Given an input question, create a syntactically correct MySQL query to run, then look at the results of the query and return the answer.
    You can order the results by a relevant column to return the most interesting examples in the database.
    Never query for all the columns from a specific table, only ask for the relevant columns given the question.
    When asked to fetch the current details, always fetch the most recent record based on updatedAt or createdAt.
    You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.
    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
    To start you should ALWAYS look at the tables in the database to see what you can query.
    Do NOT skip this step.
    Then you should query the schema of the most relevant tables.
    Do not write any additional details. also the sql code should not have ``` in beginning or end and sql word in output.

    If the question only contains a an integer value, it is implied that it is dms id/alt id of a ticket. Provide the status details of the ticket.
    If the question only contains the dms id/alt id of a ticket, provide the ticket status details.
    A ticket id provided can be either the dms id or alt id unless specified otherwise.
    When asked to fetch the status of a ticket, for each unique supplier recipient pair of the ticket, provide all the FlowSteps of the most recent revision.
    
    Response type is "status", if the query is related to the status of the ticket, or the current flowstep, or if the question is about any ticket, only if the ticket dms id/alt id is provided. If the ticket dms id/alt id is provided add it in the response json. Add the generated sql query in the response field.
    Response type is "other", otherwise. Add the generated sql query in the response field.
    
    Database Tables and Schemas

    1. Activity
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Activity Id 
    flowStepId - Type: int(11), Description: Flow Step Id, Foreign Key, Primary Key to the FlowStep Table
    dmsId - Type: varchar(255), Description: DMS Ticket Id
    description - Type: varchar(255), Description: Description of the activity
    status - Type: varchar(255), Description: Status of the activity. Can take values ["created", "revised", "deleted", "rejected", "process", "completed", "approvalCompleted", "cancelled", "onHold", "pending"]
    createdBy - Type: varchar(255) , Description: created By Name
    createdAt - Type: datetime , Description: Created at time
    updatedAt - Type: datetime , Description: updated at time
    deletedAt - Type: datetime , Description: deleted at time
    altId - Type: varchar(255) , Description: Alt id

    2. AddDa
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Activity Id 
    dmsId - Type: varchar(255), Description: DMS Ticket Id
    supplier - Type: varchar(255) , Description: Supplier Name. Can take values ["Siemens", "Synopsys", "Cadence"]
    recipient - Type: varchar(255) , Description: Recipient Name
    createdBy - Type: varchar(255) , Description: created By Name
    createdAt - Type: datetime , Description: Created at time
    updatedAt - Type: datetime , Description: updated at time
    deletedAt - Type: datetime , Description: deleted at time
    transmittalDocId - Type: datetime , Description: Transmittal Doc Id
    altId - Type: varchar(255) , Description: Alt id

    3. Comments
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Activity Id 
    flowStepId - Type: int(11), Description: Flow Step Id, Foreign Key, Primary Key to the FlowStep Table
    org - Type: varchar(255), Description: Organization, can take values [ "Intel", "Siemens", "Synopsys", "Cadence", "Other", "Arteris", "Ansys", "Ltts" ]
    orgType - Type: varchar(255), Description: Organization Type, can take values - ["Internal", "External"]
    comment - Type: longtext, Description: Comment Content
    commentType - Type: text, Description: Comment Type. Can take values - [ "delete", "rejected", "process", "completed", "cancelled", "default", "onHold" ]
    pushToDms - Type: tinyint(1), Description: Push to DMS. Can take values 0 and 1
    createdBy - Type: varchar(255) , Description: created By Name
    createdAt - Type: datetime , Description: Created at time
    updatedAt - Type: datetime , Description: updated at time
    deletedAt - Type: datetime , Description: deleted at time
    dmsId - Type: varchar(255), Description: DMS Ticket Id

    4. Completed
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Activity Id 
    dmsId - Type: varchar(255), Description: DMS Ticket Id
    rev - Type: int(11), Description: Revision Number
    pass - Type: int(11), Description: Current pass number
    pairId - Type: int(11), Description: Pair Id, Foreign Key, Primary Key of the SupplierRecipent Table
    documentId - Type: varchar(255) , Description: Document Id
    createdAt - Type: datetime , Description: Created at time
    duration - Type: int(11) , Description: Duration taken for the ticket to be completed.
    finalFlowStep - Type: int(11) , Description: Flow step id of the Final Flow step that was completed.
    updatedAt - Type: datetime , Description: updated at time
    supplier - Type: varchar(255) , Description: Supplier Name. Can take values ["Siemens", "Synopsys", "Cadence"]
    recipient - Type: varchar(255) , Description: Recipient Name
    dmsRev - Type: int(11) , Description: DMS revision

    5. FlowStep
    - Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Flow Step Id
    dmsId - Type: varchar(255), Description: DMS Ticket Id, Foreign Key
    mappingId - Type: int(11), Description: Foreign Key, Primary Key to the FlowStepMapping Table
    rev - Type: int(11), Description: Revision Number
    pass - Type: int(11), Description: Current pass number
    status - Type: varchar(255) , Description: Current status of the flow step. Can take values ["deleted","revised","rejected","completed","cancelled","process","notStarted"]
    documentId - Type: varchar(255) , Description: Document Id
    createdByEmail - Type: varchar(255) , Description: Created by email id
    eta - Type: datetime , Description: ETA
    onHoldEta - Type: datetime , Description: on hold ETA
    createdBy - Type: varchar(255) , Description: created By Name
    updatedBy - Type: varchar(255) , Description: Updated By Name
    createdAt - Type: datetime , Description: Created at time
    updatedAt - Type: datetime , Description: updated at time
    deletedAt - Type: datetime , Description: deleted at time
    recipientEmail - Type: varchar(255) , Description: Recipient email id
    recipient - Type: varchar(255) , Description: Recipient Name
    onHoldAt - Type: datetime , Description: On hold at time
    startedAt - Type: datetime , Description: Started at time
    altId - Type: varchar(255) , Description: Alt id
    supplier - Type: varchar(255) , Description: Supplier Name. Can take values ["Siemens", "Synopsys", "Cadence"]
    onHoldDuration - Type: int(11) , Description: On hold duration
    dmsRev - Type: int(11) , Description: DMS revision
    changeSummary - Type: varchar(255) , Description: Change Summary. Takes values (0 - No, 1 - Yes)

    6. FlowStepMapping
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Flow Step Mapping Id
    ownerId - Type: int(11), Description: Owner Id, Foreign Key, Primary Key of the FlowStepOwner Table
    pairId - Type: int(11), Description: Pair Id, Foreign Key, Primary Key of the SupplierRecipent Table
    stepNo - Type: int(11), Description: Step No in the entire flow
    description - Type: varchar(255), Description: Description of the Flow step
    header - Type: varchar(255), Description: Header of the Flow Step
    dependency - Type: int(11), Description: Dependency on other Flow Step Numbers. -1 indicates no dependency.
    hasDocument - Type: tinyint(1), Description: Has Document. Takes values (0 - No, 1 - Yes)
    version - Type: int(11), Description: Version
    eta - Type: int(11), Description: ETA
    createdBy - Type: varchar(255), Description: created By Name
    updatedBy - Type: varchar(255), Description: updated By Name
    createdAt - Type: datetime, Description: created at time
    updatedAt - Type: datetime, Description: updated at time
    deletedAt - Type: datetime, Description: deleted at time
    changeSummary - Type: tinyint(1), Description: Change Summary. Takes values (0 - No, 1 - Yes)
    canSendReminderEmails - Type: tinyint(1), Description: Can send reminder emails. Takes values (0 - No, 1 - Yes)
    docuSign - Type: tinyint(1), Description: Uses DocuSign. Takes values (0 - No, 1 - Yes)

    7. FlowStepOwner
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Flow Step Mapping Id
    owner - Type: varchar(255), Description: Owner Organization
    members - Type: longtext, Description: Members
    createdBy - Type: varchar(255), Description: created By Name
    updatedBy - Type: varchar(255), Description: updated By Name
    createdAt - Type: datetime, Description: created at time
    updatedAt - Type: datetime, Description: updated at time
    deletedAt - Type: datetime, Description: deleted at time
    intelSigner - Type: longtext, Description: Intel Signers
    signer - Type: longtext, Description: Signers
    intelMembers - Type: longtext, Description: Intel members
    stepZeroApprovers - Type: longtex, Description: step zero approvers

    8. Rejected
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Flow Step Mapping Id
    dmsId - Type: varchar(255), Description: DMS Ticket Id, Foreign Key
    rev - Type: int(11), Description: Revision Number
    pass - Type: int(11), Description: Current pass number
    flowStepId - Type: int(11), Description: Flow Step Id, Foreign Key, Primary Key to the FlowStep Table
    status - Type: varchar(255) , Description: Current status. Can take values ["renewed","notApplicable","rejected"]
    renewedAt - Type: datetime, Description: renewed at time 
    createdAt - Type: datetime, Description: created at time
    updatedAt - Type: datetime, Description: updated at time
    deletedAt - Type: datetime, Description: deleted at time
    supplier - Type: varchar(255) , Description: Supplier Name. Can take values ["Siemens", "Synopsys", "Cadence"]
    recipient - Type: varchar(255) , Description: Recipient Name

    9. SupplierRecipent
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, SupplierRecipent pair Id
    supplier - Type: varchar(255), Description: Supplier Name
    recipient - Type: varchar(255), Description: Recipient Name
    createdBy - Type: varchar(255), Description: created By Name
    updatedBy - Type: varchar(255), Description: updated By Name
    createdAt - Type: datetime, Description: created at time
    updatedAt - Type: datetime, Description: updated at time
    deletedAt - Type: datetime, Description: deleted at time

    Do not access any other tables.
    
    Based on the given information, refer to the inputs given below, generate the response in an appropriate format.
    
    QUESTION: 
    """+question+"""
    
    EXAMPLES
    \n
    Example 1 - How many entries are present in FlowStep?, 
        the response will be something like this 
        "{"response": "SELECT COUNT(*) FROM FlowStep ;",
            "type": "other"}"
    \n
    Example 2 - What all tickets are in complete status?, 
        the response will be something like this 
        "{"response": "SELECT * FROM FlowStep WHERE status='completed' ; ",
            "type": "other"}"
        
    \n
    Example 3 - How many flow steps where the recipient is Cadence, 
        the response will be something like this 
        "{"response": "SELECT * FROM FlowStep WHERE recipient='Cadence' ; ",
            "type": "other"}"
        
    \n
    Example 4 - Status of active flowstep of ticket 14017507755, 
        the response will be something like this 
        "{"response": "SELECT fs.id, fs.dmsId, fs.altId, fs.supplier, fs.recipient, fs.rev, fs.pass, fs.status, fs.eta, fs.updatedAt
            FROM FlowStep fs
            INNER JOIN (
            SELECT fs.supplier, fs.recipient, subq1.maxRev, MAX(fs.pass) as maxPass, MAX(fs.startedAt) as maxStart
            FROM FlowStep fs
            INNER JOIN (
                SELECT supplier, recipient, MAX(rev) AS maxRev
                FROM FlowStep
                WHERE dmsId = '15016930033' OR altId = '15016930033' 
                GROUP BY supplier, recipient
            ) subq1 ON fs.supplier = subq1.supplier AND fs.recipient = subq1.recipient AND fs.rev = subq1.maxRev 
            WHERE fs.dmsId = '15016930033' OR fs.altId = '15016930033' 
            group by fs.supplier, fs.recipient
            ) AS subq2 ON fs.supplier = subq2.supplier AND fs.recipient = subq2.recipient AND fs.rev = subq2.maxRev AND fs.pass = subq2.maxPass AND fs.startedAt = subq2.maxStart
            WHERE (fs.dmsId = '15016930033' OR fs.altId = '15016930033') ;",
            "type": "status",
            "id": "14017507755"}"
    \n
    Example 5 - 14017507755, 
        the response will be something like this 
        "{"response": "SELECT fs.id, fs.dmsId, fs.altId, fs.mappingId, fsm.description, fs.supplier, fs.recipient, fs.rev, fs.pass, fs.status, fs.eta, fs.updatedAt
            FROM FlowStepMapping fsm, FlowStep fs
            INNER JOIN (
            SELECT fs.supplier, fs.recipient, subq1.maxRev, MAX(fs.pass) as maxPass, MAX(fs.startedAt) as maxStart
            FROM FlowStep fs
            INNER JOIN (
                SELECT supplier, recipient, MAX(rev) AS maxRev
                FROM FlowStep
                WHERE dmsId = '14017507755' OR altId = '14017507755' 
                GROUP BY supplier, recipient
            ) subq1 ON fs.supplier = subq1.supplier AND fs.recipient = subq1.recipient AND fs.rev = subq1.maxRev 
            WHERE fs.dmsId = '14017507755' OR fs.altId = '14017507755' 
            group by fs.supplier, fs.recipient
            ) AS subq2 ON fs.supplier = subq2.supplier AND fs.recipient = subq2.recipient AND fs.rev = subq2.maxRev AND fs.pass = subq2.maxPass 
            WHERE (fs.dmsId = '14017507755' OR fs.altId = '14017507755') AND fsm.id = fs.mappingId ",
            "type": "status",
            "id": "14017507755"}"
            
    Example 6 -  How to get IP from IPX?
        the response will be something like this
        "{
            "type": "inference"
        }"

            
    Please provide your response in the form of a valid JSON string. 
    Ensure that the JSON is properly formatted, including necessary quotes around keys and string values, proper escaping of special characters if any, and valid data types (e.g., strings, numbers, booleans, arrays, and objects). 
    Your output should not contain any extra text outside the JSON string to avoid errors during parsing.
    
    """
    return prompt

def create_inference_prompt(question, documents):

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

def create_sql_summary_prompt(question, sql_query, sql_query_results):
    response_prompt = f"""
    You are an agent designed to interact with a SQL query results.
    Given an input question, and the sql database query results for that question, generate a summary of the query results to answer the question.
    You have been provided with the database tables and schema details for your reference.
    Do not mention about the provided sql query results in the response.

    If the question only contains a an integer value, it is implied that it is dms id/alt id of a ticket. The alt id usually has 5 digits while the dms id usually has 11 digits. Provide the status details of the ticket.
    When asked to fetch the status of a ticket, for each unique supplier recipient pair of the ticket, provide a summary the details of the FlowSteps of the most recent revision and pass.
    Important details include: unique supplier recipient pair, dms id, alt id, rev, pass, status, eta, updatedAt.
    Find the details from the SQL Query Results by looking at the SQL Query.
    Generate the response in proper html format according to the instructions given below. Refer to the examples provided.

    Input Question: {question}

    SQL Query: {sql_query}

    SQL Query Results: {sql_query_results}

    \n
    Database Tables and Schemas

    1. Activity
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Activity Id 
    flowStepId - Type: int(11), Description: Flow Step Id, Foreign Key, Primary Key to the FlowStep Table
    dmsId - Type: varchar(255), Description: DMS Ticket Id
    description - Type: varchar(255), Description: Description of the activity
    status - Type: varchar(255), Description: Status of the activity. Can take values ["created", "revised", "deleted", "rejected", "process", "completed", "approvalCompleted", "cancelled", "onHold", "pending"]
    createdBy - Type: varchar(255) , Description: created By Name
    createdAt - Type: datetime , Description: Created at time
    updatedAt - Type: datetime , Description: updated at time
    deletedAt - Type: datetime , Description: deleted at time
    altId - Type: varchar(255) , Description: Alt id

    2. AddDa
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Activity Id 
    dmsId - Type: varchar(255), Description: DMS Ticket Id
    supplier - Type: varchar(255) , Description: Supplier Name. Can take values ["Siemens", "Synopsys", "Cadence"]
    recipient - Type: varchar(255) , Description: Recipient Name
    createdBy - Type: varchar(255) , Description: created By Name
    createdAt - Type: datetime , Description: Created at time
    updatedAt - Type: datetime , Description: updated at time
    deletedAt - Type: datetime , Description: deleted at time
    transmittalDocId - Type: datetime , Description: Transmittal Doc Id
    altId - Type: varchar(255) , Description: Alt id

    3. Comments
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Activity Id 
    flowStepId - Type: int(11), Description: Flow Step Id, Foreign Key, Primary Key to the FlowStep Table
    org - Type: varchar(255), Description: Organization, can take values [ "Intel", "Siemens", "Synopsys", "Cadence", "Other", "Arteris", "Ansys", "Ltts" ]
    orgType - Type: varchar(255), Description: Organization Type, can take values - ["Internal", "External"]
    comment - Type: longtext, Description: Comment Content
    commentType - Type: text, Description: Comment Type. Can take values - [ "delete", "rejected", "process", "completed", "cancelled", "default", "onHold" ]
    pushToDms - Type: tinyint(1), Description: Push to DMS. Can take values 0 and 1
    createdBy - Type: varchar(255) , Description: created By Name
    createdAt - Type: datetime , Description: Created at time
    updatedAt - Type: datetime , Description: updated at time
    deletedAt - Type: datetime , Description: deleted at time
    dmsId - Type: varchar(255), Description: DMS Ticket Id

    4. Completed
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Activity Id 
    dmsId - Type: varchar(255), Description: DMS Ticket Id
    rev - Type: int(11), Description: Revision Number
    pass - Type: int(11), Description: Current pass number
    pairId - Type: int(11), Description: Pair Id, Foreign Key, Primary Key of the SupplierRecipent Table
    documentId - Type: varchar(255) , Description: Document Id
    createdAt - Type: datetime , Description: Created at time
    duration - Type: int(11) , Description: Duration taken for the ticket to be completed.
    finalFlowStep - Type: int(11) , Description: Flow step id of the Final Flow step that was completed.
    updatedAt - Type: datetime , Description: updated at time
    supplier - Type: varchar(255) , Description: Supplier Name. Can take values ["Siemens", "Synopsys", "Cadence"]
    recipient - Type: varchar(255) , Description: Recipient Name
    dmsRev - Type: int(11) , Description: DMS revision

    5. FlowStep
    - Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Flow Step Id
    dmsId - Type: varchar(255), Description: DMS Ticket Id, Foreign Key
    mappingId - Type: int(11), Description: Foreign Key, Primary Key to the FlowStepMapping Table
    rev - Type: int(11), Description: Revision Number
    pass - Type: int(11), Description: Current pass number
    status - Type: varchar(255) , Description: Current status of the flow step. Can take values ["deleted","revised","rejected","completed","cancelled","process","notStarted"]
    documentId - Type: varchar(255) , Description: Document Id
    createdByEmail - Type: varchar(255) , Description: Created by email id
    eta - Type: datetime , Description: ETA
    onHoldEta - Type: datetime , Description: on hold ETA
    createdBy - Type: varchar(255) , Description: created By Name
    updatedBy - Type: varchar(255) , Description: Updated By Name
    createdAt - Type: datetime , Description: Created at time
    updatedAt - Type: datetime , Description: updated at time
    deletedAt - Type: datetime , Description: deleted at time
    recipientEmail - Type: varchar(255) , Description: Recipient email id
    recipient - Type: varchar(255) , Description: Recipient Name
    onHoldAt - Type: datetime , Description: On hold at time
    startedAt - Type: datetime , Description: Started at time
    altId - Type: varchar(255) , Description: Alt id
    supplier - Type: varchar(255) , Description: Supplier Name. Can take values ["Siemens", "Synopsys", "Cadence"]
    onHoldDuration - Type: int(11) , Description: On hold duration
    dmsRev - Type: int(11) , Description: DMS revision
    changeSummary - Type: varchar(255) , Description: Change Summary. Takes values (0 - No, 1 - Yes)

    6. FlowStepMapping
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Flow Step Mapping Id
    ownerId - Type: int(11), Description: Owner Id, Foreign Key, Primary Key of the FlowStepOwner Table
    pairId - Type: int(11), Description: Pair Id, Foreign Key, Primary Key of the SupplierRecipent Table
    stepNo - Type: int(11), Description: Step No in the entire flow
    description - Type: varchar(255), Description: Description of the Flow step
    header - Type: varchar(255), Description: Header of the Flow Step
    dependency - Type: int(11), Description: Dependency on other Flow Step Numbers. -1 indicates no dependency.
    hasDocument - Type: tinyint(1), Description: Has Document. Takes values (0 - No, 1 - Yes)
    version - Type: int(11), Description: Version
    eta - Type: int(11), Description: ETA
    createdBy - Type: varchar(255), Description: created By Name
    updatedBy - Type: varchar(255), Description: updated By Name
    createdAt - Type: datetime, Description: created at time
    updatedAt - Type: datetime, Description: updated at time
    deletedAt - Type: datetime, Description: deleted at time
    changeSummary - Type: tinyint(1), Description: Change Summary. Takes values (0 - No, 1 - Yes)
    canSendReminderEmails - Type: tinyint(1), Description: Can send reminder emails. Takes values (0 - No, 1 - Yes)
    docuSign - Type: tinyint(1), Description: Uses DocuSign. Takes values (0 - No, 1 - Yes)

    7. FlowStepOwner
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Flow Step Mapping Id
    owner - Type: varchar(255), Description: Owner Organization
    members - Type: longtext, Description: Members
    createdBy - Type: varchar(255), Description: created By Name
    updatedBy - Type: varchar(255), Description: updated By Name
    createdAt - Type: datetime, Description: created at time
    updatedAt - Type: datetime, Description: updated at time
    deletedAt - Type: datetime, Description: deleted at time
    intelSigner - Type: longtext, Description: Intel Signers
    signer - Type: longtext, Description: Signers
    intelMembers - Type: longtext, Description: Intel members
    stepZeroApprovers - Type: longtex, Description: step zero approvers

    8. Rejected
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, Flow Step Mapping Id
    dmsId - Type: varchar(255), Description: DMS Ticket Id, Foreign Key
    rev - Type: int(11), Description: Revision Number
    pass - Type: int(11), Description: Current pass number
    flowStepId - Type: int(11), Description: Flow Step Id, Foreign Key, Primary Key to the FlowStep Table
    status - Type: varchar(255) , Description: Current status. Can take values ["renewed","notApplicable","rejected"]
    renewedAt - Type: datetime, Description: renewed at time 
    createdAt - Type: datetime, Description: created at time
    updatedAt - Type: datetime, Description: updated at time
    deletedAt - Type: datetime, Description: deleted at time
    supplier - Type: varchar(255) , Description: Supplier Name. Can take values ["Siemens", "Synopsys", "Cadence"]
    recipient - Type: varchar(255) , Description: Recipient Name

    9. SupplierRecipent
    Columns:
    id - Type: int(11), Description: Automatic Increment, Primary Key, SupplierRecipent pair Id
    supplier - Type: varchar(255), Description: Supplier Name
    recipient - Type: varchar(255), Description: Recipient Name
    createdBy - Type: varchar(255), Description: created By Name
    updatedBy - Type: varchar(255), Description: updated By Name
    createdAt - Type: datetime, Description: created at time
    updatedAt - Type: datetime, Description: updated at time
    deletedAt - Type: datetime, Description: deleted at time


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

    """

    return response_prompt

def update_db(question, prompt=None, response=None, sql_query=None, feedback=None, error=None):
    config = global_config
    connection_string = config["chat_db_url"]
    collection_name = config["chat_collection_name"]
    resp=None
    try:
        mongoClient = mongoDbConnection(connection_string, collection_name)
        record = {
            "user_wwid": "",
            "username": "",
            "query": question,
            "prompt": prompt,
            "response": response,
            "sql_query": sql_query,
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
        # text = text[2:-1]
        # text = text.replace("\\'", "'").replace('\\"', '"').replace("\\\\n", "\n")
        json_data = json.loads(text, strict=False)
        return json_data
    except Exception as e:
        # raise Exception("generate:format_json:"+str(e))
        print("ERROR:nltosql:format_json")
        raise e

def validate_json(json_string):
    try:
        # Attempt to load the JSON string
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        return False

    # Check for required fields
    print("checking required fields")
    required_fields = ['type']
    for field in required_fields:
        if field not in data:
            print(f"Missing required field: {field}")
            return False
    
    # Check for 'response' and 'id' field if 'type' is 'status' or 'other
    # if data['type'] == 'inference' and 'response' not in data:
    #     print("Missing required field: response (for type 'inference')")
    #     return False
    if data['type'] == 'other' and 'response' not in data:
        print("Missing required field: response (for type 'other')")
        return False
    if data['type'] == 'status' and 'response' not in data:
        print("Missing required field: response (for type 'status')")
        return False
    if data['type'] == 'status' and 'id' not in data:
        print("Missing required field: id (for type 'status')")
        return False
    print("JSON is valid and contains all required fields.")
    return True

def send_error_email(error, question):
    print("*******************SENDING EMAIL**********************************")
    sender_email = config["eip_chatbot_email"]
    sender_password = config["eip_chatbot_password"]
    receiver_emails = config["receiver_emails"]
    subject = "ERROR IN EIP CHATBOT SERVICE"
    body = str(error)+"\nQuestion: "+question
    send_email(sender_email, sender_password, receiver_emails, subject, body)

@igenerate.route("/generate/<question>",methods=["GET"])
def generate(question):
    
    global conversation
    sql_query = None
    is_sql_query = 0

    json_response = {
        "id": None,
        "response": "Something went wrong while processing your request. Please try again later.",
        "is_sql_query": 0,
        "sql_query": None,
        "time_taken": None,
    }

    print("Question: ",question)
    
    try:
        llm = generate_model()
        start_time = time.time()
        # create prompt
        prompt = create_supervisor_prompt(question)
        print("created prompt")
        print('-------------INVOKING SUPERVISOR MODEL----------------')
        s = time.time()
        response=llm.invoke(prompt)
        et = time.time()
        print("Time taken by supervisor: ", et-s)
        print("--------------RECEIVED RESPONSE---------------")
        
        try:
            json.loads(response)
        except:
            print("json loads throwing error")

        response = json.loads(response)
        # print(response)
        try:
            valid_json=validate_json(response['currentResponse'])
        except Exception as e:
            print("ERROR:generate:validate_json: "+str(e))
            send_error_email(str(e), question)
            update_db(question, error=str(e))
            return json_response
        
        if(valid_json==False):
            raise Exception("ERROR:generate:Incorrect JSON response")
        response = json.loads(response['currentResponse'])
        if(response["type"]=="inference"):
            try: 
                # retrieve relevant wiki documents
                print("===================RETRIEVING WIKI DOCUMENTS==============================")
                s = time.time()
                documents = retrieve_documents(question)
                et = time.time()
                print("time taken for retrieving: ", et-s)
            except Exception as e:
                print("ERROR:generate:retreiving wiki documents: "+str(e))
                send_error_email(str(e), question)
                update_db(question, error=str(e))
                return json_response

            print("------SUMMARIZING RETRIEVED DOCUMENTS------------")
            s = time.time()
            inference_response = llm.invoke(create_inference_prompt(question, documents['top_k_results']['response']))
            et = time.time()
            print("Time taken for inference: ", et-s)
            inference_response = json.loads(inference_response)
            # inference_response = format_json(inference_response)
            resp = inference_response['currentResponse']
        
        else:
            is_sql_query = 1
            sql_query = response["response"]
            # Execute the sql query
            try:
                mySql = mySqlConnection(host, port, username, password, db)
                sql_query_results = mySql.execute_query(sql_query)
                # query_results = execute_sql_query(sql_query)   # execute sql query
            except Exception as e:
                print("ERROR:generate:mySQL: "+str(e))
                send_error_email(str(e), question)
                update_db(question, error=str(e))
                return json_response
            
            sql_summary_prompt = create_sql_summary_prompt(question, sql_query, sql_query_results)
            print("----------SUMMARIZING SQL QUERY RESULTS------------")
            s = time.time()
            sql_summary_response = llm.invoke(sql_summary_prompt)
            et = time.time()
            print("Time taken to summarize sql results: ", et-s)
            sql_summary_response = json.loads(sql_summary_response)
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
                resp = ticket_details+"<b>Summary</b><br> "+sql_summary
        
        # Update conversation in Database
        print("*********UPDATING IN DB*************************************")
        try:
            chat_id = update_db(question, response, sql_query)
        except Exception as e:
            print("ERROR:generate: "+str(e))
            send_error_email(str(e), question)
            return json_response
        
        end_time = time.time()
        execution_time = end_time - start_time
        print("EXECUTION TIME: ", execution_time)
        
        # resp += "<br>Time taken to generate response: "+"{:.1f}".format(execution_time)+" s <br>We are continuously working on improving our response time to enhance your experience. Thank you for your patience and understanding."

        json_response["id"]=str(chat_id)
        json_response["response"]=resp
        json_response["is_sql_query"]=is_sql_query
        json_response["sql_query"]=sql_query
        json_response["time_taken"]="{:.1f}".format(execution_time)
        
        return json_response

    except Exception as e:
        print("ERROR:generate: "+str(e))
        send_error_email(str(e), question)
        update_db(question, error=str(e))
        return jsonify(json_response)

