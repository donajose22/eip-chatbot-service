import sys
sys.path.append('./')

from config.config import global_config
from src.apigee import get_access_token
import json
import requests

config = global_config

topics = [
    "Contract Log / EIP Deal Tracker",
    "EIP Cabinet: 'Local' copy of all EIP Legal Agreements",
    "EIP Control Panel Testing",
    "EIP Operations: Processes and flows",
    "Legal",
    "DSS",
    "Carbon",
    "Licensing",
    "Supplier setup for IP uploads",
    "IRR",
    "IPX",
    "Cheatsheet for IPX commands",
    "Flow Steps for releasing IP to Habana from IPX to IFS through UCM",
    "GB access to IPX",
    "iBi and Looker queries for IPX uploads or permissions",
    "Migration from IPA@.lineA to IPB@.lineB",
    "Migration from IRR",
    "Product consumer groups",
    "Releasing IP from IPX to UCM",
    "Scripts created by Nik",
    "UCM: Set up a project & Roles needed for accessing EIP through IFS Portal",
    "Useful commands in IPX",
    "Goto for External IP",
    "Product Naming History",
    "Creation of AGS entitlements",
    "Automatic IP uploads",
    "ARM IP Download - New CLI (command-line interface)",
    "Faceless Accounts and Groups",
    "Changing Wiki Access permissions",
    "Disclosure",
    "Power BI Dashboards",
    "EIP Sharepoint Libraries: Public & Private",
    "old goto/externalIP.team",
    "DMS",
    "DMS TEAM PAGE",
    "Delegate Storage",
    "Update the DMS Banner",
    "Yammer Communications",
    "Creating a DMS User Survey",
    "DMS Wizard",
    "DMS Training",
    "EDIT - EDA IP Disclosure to Competitor Status",
    "EDA Agreement Contacts",
    "Flow Step Descriptions - EDIT",
    "Synopsys Competitor List - November 2021",
    "EDIT 2.0 API & Services",
    "EDIT 2.0 Plans",
    "Changes to Flow Steps",
    "Cadence As IP Supplier",
    "Siemens As IP Supplier",
    "Synopsys As IP Supplier",
    "EDIT 2.0 Testing Overview",
    "EDIT 1.0 - EDA IP Disclosure Tracker Future Enhancements",
    "EDIT Communications",
    "Miscellaneous Audit Page Requirements -",
    "Ticket Analysis",
    "Ticket Analysis Deployment Status Page",
    "API and Services",
    "Enhancement Requests for Ticket Analysis",
    "Synopsys Install Base: production licensing, past & present",
    "Enabling Suppliers in CWOS",
    "IPX Scripting for EIP Team and consumers",
    "Knowledge Transfer related recordings",
    "External IP",
    "Learn about EIP Ecosystem",
    "External IP Stages",
    "EIP Definitions",
    "EIP Contacts",
    "EIP Owner's Council",
    "EIP Swimlanes",
    "Enhancement Topics",
    "EIP ChatBot",
    "Procedure to Update Chatbot with WIKI Data",
    "Process for licensing EIP provided through a DP (design package ) from TEG",
    "Wellnomics",
    "How to add others to a submitted IT Ticket under it.intel.com",
    "simple - How-to add a person to a PDL or grant access rights to Team Wiki",
    "Vendor and IP consumption reports",
    "IP Licensing/Consumption report",
    "Semiconductor News & Background",
    "New EIP OPS Member for Licensing /Access Granting",
    "Product requirements",
    "Vendor Audit Report",
    "AI Support",

    "Request Access to DMS via AGS",
    "General Flow/Quick Overview",
    "General Information",
    "Project Description",
    "Design DA`s -Project Descriptions",
    "EDA / CW disclosures (A.K.A. 'Design Disclosures')",
    "IFS - Project Description",
    "TD, MSO, GSC - Project Description Statements",
    "Extend Expiration Date",
    "Roomed Projects",
    "Process / Design Collateral",
    "Intel IP",
    "Unix Groups - Protecting IP",
    "BKMs - unix group organization to protect Intel products",
    "Unix Content Dashboard",
    "Disclosing Unix Groups",
    "Design Disclosure IP Description",
    "SPO/TEAMS - Site creation and maintenance guide",
    "Third Party IP",
    "Disclosing External IP: Fundamentals",
    "Carbon Discrepancies - ensuring the disclosure matches the licensed Bill of Materials",
    "EDA IP Disclosures - IP Supplier or Recipient",
    "EDIT - Eda ip DIsclosure Tracker",
    "Step Zero - confirmation from the Recipient Project Lead that the Rep list and transmittal form are correct",
    "Cadence-Specific Instructions (IP Supplier or Recipient)",
    "Siemens-Specific Instructions (IP Supplier or Recipient)",
    "Synopsys-Specific Instructions (IP Supplier or Recipient)",
    "ARM IP",
    "CEVA IP",
    "Samsung IP",
    "TSMC IP",
    "Forms",
    "Intel & Recipients Company Reps",
    "Add/Deactivate Intel Reps",
    "Add/Deactivate Recipient Company Reps",
    "Adding multiple Recipient Company reps:",
    "Export Compliance",
    "Disclosure Addendum (DA)",
    "Companies without auto-DA",
    "Create your M-RUNDA DA document",
    "Umbrella Disclosure Addendum (UDA)",
    "Single Use RUNDA development ... instead of M-RUNDA / DA",
    "Approvals",
    "Requesting Approvals",
    "Requesting IPPO Approval or 'dms_review' Approval",
    "Add approver to approval table",
    "Comments",
    "Attachment",
    "Support Section",
    "Revise Existing Tickets",
    "How-To: Close Ticket/DA",
    "Close Ticket/Da IP never shared",
    "Closed Ticket/DA IP Shared",
    "How to Items",
    "VP Guidance",
    "How-To: Create a Query/Report",
    "Pre-Formatted Search - Special Focus on Ticket Reuse",
    "Copying DA tickets",
    "Ticket Analysis",
    "DocuSign for DA signature",
    "Final steps to 'Executed' (DA fully approved)",
    "Submit not possible - DMS messages",
    "Stale Tickets / Stalled Tickets",
    "Vendor name change due to acquisition",
    "DA Revision - Approval logic",
    "What is Intel Top Secret Intellectual Property (ITS IP)?",
    "DMS Chatbot",
    "FAQ - Frequently Asked Questions"
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

def append_to_jsonl_file(file_path, new_item):
    try:
        with open(file_path, 'a') as file:
            file.write(json.dumps(new_item) + '\n')
        print("Item successfully appended!")
    except Exception as e:
        print(f"An error occurred: {e}")

file_path = 'wiki/wiki_docs.json'

def run_retreiver():
    count = 1
    total = len(topics)
    
    for x in topics:
        print("Retreiving topic "+str(count))
        resp = retrieve_documents(x)

        # print(resp['top_k_results']['response'])
        
        append_to_jsonl_file(file_path, resp['top_k_results']['response'])
        
        if(count%10==0):
            print("------------------"+str(count)+"/"+str(total)+" complete")
        count+=1
        
run_retreiver()