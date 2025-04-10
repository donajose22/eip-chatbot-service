from mysql.connector import connect
from langchain_sdk.Langchain_sdk import LangChainCustom
from src.ticketStatus import get_ticket_details
from src.mySqlConnection import mySqlConnection
from src import formatter
from src.loadModel import load_model
import json
from config.config import global_config

config = global_config
host = config["eda_ip_tracker_host"]
port = config["eda_ip_tracker_port"]
username = config["eda_ip_tracker_username"]
password = config["eda_ip_tracker_password"]
db = config["eda_ip_tracker_database"]

# def connect_db():
#   mydb = connect(
#     host="maria4197-lb-fm-in.iglb.intel.com",
#     port=3307,
#     user="eda_ip_tracker_so",
#     password="l0iElPrPaGcGa3r",
#     database="eda_ip_tracker"
#   )

#   return mydb

# def execute_sql_query(sql):
#     conn=connect_db()
#     cur=conn.cursor()
#     cur.execute(sql)
#     rows=cur.fetchall()
#     conn.commit()
#     conn.close()
#     return rows

prompt_sql_query = """

You are an agent designed to interact with a SQL database.
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
A ticket id provided can be either the dms id or alt id unless specified otherwise.
When asked to fetch the status of a ticket, for each unique supplier recipient pair of the ticket, provide all the FlowSteps of the most recent revision.

Also provide the query type in the response.
Query type is "status", if the query is related to the status of the ticket, or the current flowstep, or if the question is about any ticket, only if the ticket dms id/alt id is provided. If the ticket dms id/alt id is provided add it in the response json.
Query type is "other", otherwise. No additional detail is required.

Response should be in the json format:
"{
    "query": "SELECT COUNT(*) FROM FlowStep ;",
    "type": "status",
    "id"": "123456789"
}"


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

    Do not access any other tables.

\n\nFor example,
\n
Example 1 - How many entries are present in FlowStep?, 
    the response will be something like this 
    "{"query": "SELECT COUNT(*) FROM FlowStep ;",
        "type": "other"}"
\n
Example 2 - What all tickets are in complete status?, 
    the response will be something like this 
    "{"query": "SELECT * FROM FlowStep WHERE status='completed' ; ",
        "type": "other"}"
    
\n
Example 3 - How many flow steps where the recipient is Cadence, 
    the response will be something like this 
    "{"query": "SELECT * FROM FlowStep WHERE recipient='Cadence' ; ",
        "type": "other"}"
    
\n
Example 4 - Status of active flowstep of ticket 14017507755, 
    the response will be something like this 
    "{"query": "SELECT fs.id, fs.dmsId, fs.altId, fs.supplier, fs.recipient, fs.rev, fs.pass, fs.status, fs.eta, fs.updatedAt
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
    "{"query": "SELECT fs.id, fs.dmsId, fs.altId, fs.mappingId, fsm.description, fs.supplier, fs.recipient, fs.rev, fs.pass, fs.status, fs.eta, fs.updatedAt
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
    
    Please provide your response in the form of a valid JSON string. 
    Ensure that the JSON is properly formatted, including necessary quotes around keys and string values, proper escaping of special characters if any, and valid data types (e.g., strings, numbers, booleans, arrays, and objects). 
    Your output should not contain any extra text outside the JSON string to avoid errors during parsing.
"""

def create_prompt(question, sql_query, sql_query_results):
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

def generate_model():
    client_id = config["genai_client_id"]
    client_secret = config["genai_secret"]

    llm = LangChainCustom(client_id=client_id,
                            client_secret=client_secret,
                            model="gpt-4-turbo",
                            temperature=1,
                            chat_conversation=True,
                            conversation_history = [],
                            system_prompt='Summarize everything in 100 words.')
                            # system_prompt=prompt
                            
    return llm

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
    required_fields = ['query', 'type']
    for field in required_fields:
        if field not in data:
            print(f"Missing required field: {field}")
            return False
    print("no missing fields1")
    # Check for 'id' field if 'type' is 'status'
    if data['type'] == 'status' and 'id' not in data:
        print("Missing required field: id (for type 'status')")
        return False
    print("no missing fields2")
    print("JSON is valid and contains all required fields.")
    return True

def generate_model_response(question,prompt):
    try:
        # model=generate_model()
        model = load_model()
        response=model.invoke([prompt, question])
        response = format_json(response)
        return response
    except Exception as e:
        print("ERROR:nltosql:generate_model_response: "+str(e))
        raise e

def generate_response(question):
    valid_json=False
    try_count=1

    # Generate Response and validate json
    # Run 5 times in case of invalid json
    while(valid_json==False and try_count<=5):
        resp = generate_model_response(question, prompt_sql_query)   # use llm model to create sql query
        resp = resp['currentResponse']
        # INSERT JSON VALIDATOR
        print("**********************VALIDATING JSON**********************************************")
        valid_json=validate_json(resp)
        try_count+=1        

    if(valid_json==False):
        raise Exception("ERROR:nltosql:Incorrect JSON response")
    
    # resp = format_json(resp)
    # resp = resp["currentResponse"]
    # print("GENERATED SQL QUERY: \n", resp)


    # Convert String to json
    try:
        # resp = format_json(resp)
        # query_data = resp["currentResponse"]
        query_data = json.loads(resp)
        print("GENERATED SQL QUERY: \n", query_data)
    except Exception as e:
        print("ERROR:nltosql: json.loads: "+str(e))
        raise e

    query = query_data['query']
    query_type = query_data['type']
    if(query_type=="status"):
        ticket_id = query_data['id']
        # Get ticket status details
        ticket_details = get_ticket_details(ticket_id)

    print("=======================================================================================================")
    
    # Execute the sql query
    try:
        mySql = mySqlConnection(host, port, username, password, db)
        query_results = mySql.execute_query(query)
        # query_results = execute_sql_query(query)   # execute sql query
    except Exception as e:
        print("ERROR:nltosql:mySQL: "+str(e))
        raise e
    
    print("SQL QUERY RESULTS: \n")
    for x in query_results:
        print(x)

    print("=======================================================================================================")

    # Create prompt to summarize sql query results
    print("********************SUMMARIZING SQL QUERY RESULTS*****************************************")
    prompt = create_prompt(question, query, query_results)  
    response = generate_model_response(question, prompt)   # use llm model to summarize sql query response
    print("GENERATED RESPONSE: \n", response["currentResponse"])
    
    print("=======================================================================================================")

    # convert the text to html format
    # formatted_generated_response = formatter.format(question, response["currentResponse"])
    formatted_generated_response = response['currentResponse']

    if(query_type=="status" and ticket_details is not None):
        resp = ticket_details+f"<b>Summary</b><br> "+formatted_generated_response
        
        # query_format = """            
        #     <button type="button" class="query-collapsible" id="{1}" onClick="expandCollapseContent()">SQL Query</button>
        #     <div className='sql-query-content' id="{1}" style= "display:none" >{0}</div>
        # """

        # query_format = """            
        #     <button type="button" class="query-collapsible" id="{1}">SQL Query <div class='plusminus'>+</div></button>
        #     <div class='sql-query-content' id="{1}" style= "display:none" >{0}</div>
        # """

        # resp += query_format.format(query, i)

    else:
        resp = formatted_generated_response
    
    print("______________________________________NL TO SQL RESPONSE_____________________________________")
    print(resp)

    return [prompt, query, resp]