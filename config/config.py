import os
from dotenv import load_dotenv

load_dotenv()

dev_config = {
    "environment": os.environ["APPENV"],
    "app_secret_key": os.environ["APP_SECRET_KEY"],
    "auth_url": "https://apis-internal.intel.com/v1/auth/token",
    "apigee": {
        "token_url": "https://apis.intel.com/v1/auth/token",
        "client_id": "77f7a012-d329-4563-9586-2aa4ffdf81ca",
        "client_secret": os.environ["APIGEE_CLIENT_SECRET"],
    },
    
    "azure_client_id": "79f5373a-d47c-455f-b728-d2b23345cb3e",
    "azure_client_secret": os.environ["AZURE_APP_CLIENT_SECRET_DEV"],
    
    "data_pipeline_client_id": "d36a38f9-f7ff-4052-9660-9d1dd493c297",
    "data_pipeline_secret": os.environ["DATA_PIPELINE_API_SECRET"],
    
    "jira_api_server_url": "https://jira.devtools.intel.com/rest/api/2/search",

    "obo": {
      "token_url": "https://apis-sandbox.intel.com/v1/auth/obo/token"
    },
    
    "proxies": {
        "http": "http://proxy-dmz.intel.com:912",
        "https": "http://proxy-dmz.intel.com:912",
        "no_proxy": "localhost,*.intel.com"
    },
    
    "embed_url": "https://apis-internal.intel.com/generativeaiembedding/v1/embed",
    "retriever_url" : "https://apis.intel.com/gai/data-pipeline/v1/retrieve-details/retrieve",
    
    "hsdes": {
      "hsdes_username": "sys_syseipsync",
      "hsdes_pwd": os.environ["HSDES_TOKEN"],
    },
    
    "redis_consts": {
        "url": "10-108-83-136.dbaas.intel.com",
        "pwd": os.environ["REDIS_PASSWORD_DEV"],
        "port": 6380,
    },
    
    "chat_db": {
      "url": os.environ["EIP_CHATBOT_MONGO_DB_CONNECTION_URL_DEV"],
      "db_name": "EIP_Chatbot_Prompts",
      "collection_name": "user_chat_details",
      "port": 7194
    },
    
    "prompt_templates_db": {
      "url": os.environ["EIP_CHATBOT_MONGO_DB_CONNECTION_URL_DEV"],
      "db_name": "EIP_Chatbot_Prompts",
      "collection_name": "chatbot_prompts",
      "port": 7194
    },
    
    "database_schema_mysql": {
      "host": "maria3147-lb-ir-in.dbaas.intel.com",
      "port": 3307,
      "username": "Database_schema_so",
      "password": os.environ["DATABASE_SCHEMA_DB_PASSWORD_DEV"],
      "database": "Database_schema",
    },

    "eda_ip_tracker_host":"maria4197-lb-fm-in.iglb.intel.com",
    "eda_ip_tracker_port":3307,
    "eda_ip_tracker_username":"eda_ip_tracker_so",
    "eda_ip_tracker_password":os.environ["EDA_IP_TRACKER_DB_PASSWORD_PROD"],
    "eda_ip_tracker_database":"eda_ip_tracker",

    "eipteam_contract_id": "de7170a9-f3b4-442d-98ff-b9490058f48d",
    "rdse_contract_id": "ebaa280a-0a23-45c7-a09d-ceb2becc620b",
    "user_email": "eipchatbot@intel.com",

    "eip_chatbot_email": "eipchatbot@intel.com",
    "eip_chatbot_username": "grp_eipchatbot",
    "eip_chatbot_password": os.environ["EIP_CHATBOT_EMAIL_PASSWORD"],
    "receiver_emails": [
        "dona.jose@intel.com",
        # "geetha.d@intel.com"
    ],

    "ssl": {
      "ca": 'IntelSHA256RootCA-base64.crt',
    }    
}

prod_config = {
    "environment": os.environ["APPENV"],
    "app_secret_key": os.environ["APP_SECRET_KEY"],
    "auth_url": "https://apis.intel.com/v1/auth/token",
    "apigee": {
        "token_url": "https://apis.intel.com/v1/auth/token",
        "client_id": "77f7a012-d329-4563-9586-2aa4ffdf81ca",
        "client_secret": os.environ["APIGEE_CLIENT_SECRET"],
    },
    
    "azure_client_id": "0e30d0c7-349c-4d58-a0be-2f3f73bdd665",
    "azure_client_secret": os.environ["AZURE_APP_CLIENT_SECRET_PROD"],
    
    "data_pipeline_client_id": "d36a38f9-f7ff-4052-9660-9d1dd493c297",
    "data_pipeline_secret": os.environ["DATA_PIPELINE_API_SECRET"],
    
    "jira_api_server_url": "https://jira.devtools.intel.com/rest/api/2/search",

    "obo": {
      "token_url": "https://apis-sandbox.intel.com/v1/auth/obo/token"
    },
    
    "proxies": {
        "http": "http://proxy-dmz.intel.com:912",
        "https": "http://proxy-dmz.intel.com:912",
        "no_proxy": "localhost,*.intel.com"
    },
    
    "embed_url": "https://apis-internal.intel.com/generativeaiembedding/v1/embed",
    "retriever_url" : "https://apis.intel.com/gai/data-pipeline/v1/retrieve-details/retrieve",
    
    "hsdes": {
      "hsdes_username": "sys_syseipsync",
      "hsdes_pwd": os.environ["HSDES_TOKEN"],
    },
    
    "redis_consts": {
        "url": "10-108-211-120.dbaas.intel.com",
        "pwd": os.environ["REDIS_PASSWORD_PROD"],
        "port": 6380,
    },
  
    "chat_db": {
      "url": os.environ["EIP_CHATBOT_CONNECTION_URL_PROD"],
      "db_name": "EIP_Chatbot_Prod",
      "collection_name": "user_chat_details",
      "port": 7071
    },
    
    "prompt_templates_db": {
      "url": os.environ["EIP_CHATBOT_CONNECTION_URL_PROD"],
      "db_name": "EIP_Chatbot_Prod",
      "collection_name": "chatbot_prompts",
      "port": 7071
    },
    
    "database_schema_mysql": {
      "host": "maria3278-lb-pg-in.iglb.intel.com",
      "port": 3307,
      "username": "EIP_Chatbot_Database_ro",
      "password": os.environ["DATABASE_SCHEMA_DB_PASSWORD_PROD"],
      "database": "EIP_Chatbot_Database_Schema",
    },

    "eda_ip_tracker_host":"maria4197-lb-fm-in.iglb.intel.com",
    "eda_ip_tracker_port":3307,
    "eda_ip_tracker_username":"eda_ip_tracker_so",
    "eda_ip_tracker_password":os.environ["EDA_IP_TRACKER_DB_PASSWORD_PROD"],
    "eda_ip_tracker_database":"eda_ip_tracker",

    "eipteam_contract_id": "de7170a9-f3b4-442d-98ff-b9490058f48d",
    "rdse_contract_id": "ebaa280a-0a23-45c7-a09d-ceb2becc620b",
    "user_email": "eipchatbot@intel.com",

    "eip_chatbot_email": "eipchatbot@intel.com",
    "eip_chatbot_username": "grp_eipchatbot",
    "eip_chatbot_password": os.environ["EIP_CHATBOT_EMAIL_PASSWORD"],
    "receiver_emails": [
        "dona.jose@intel.com",
        # "geetha.d@intel.com"
    ],

    "ssl": {
      "ca": 'IntelSHA256RootCA-base64.crt',
    }    
}

environment = os.getenv("APPENV") or "development"
print(environment)
global_config = prod_config if environment == "production" else dev_config

