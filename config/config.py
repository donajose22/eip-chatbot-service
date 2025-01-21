import os
from dotenv import load_dotenv

load_dotenv()

dev_config = {
    "auth_url": "https://apis-internal.intel.com/v1/auth/token",
    "apigee": {
        "token_url_internal": "https://apis-internal.intel.com/v1/auth/token",
        "token_url": "https://apis.intel.com/v1/auth/token",
        "client_id": "fc4d18f6-8074-48dc-b97e-7f3807754764",
        "client_secret": os.environ["APIGEE_CLIENT_SECRET_DEV"],
    },
    "proxies": {
        "http": "http://proxy-dmz.intel.com:912",
        "https": "http://proxy-dmz.intel.com:912",
        "no_proxy": "localhost,*.intel.com"
    },
    "proxy_url": "http://proxy-dmz.intel.com:912",
    "embed_url": "https://apis-internal.intel.com/generativeaiembedding/v1/embed",
    "retriever_url" : "https://apis.intel.com/gai/data-pipeline/v1/retrieve-details/retrieve",

    "genai_client_id": "d36a38f9-f7ff-4052-9660-9d1dd493c297",
    "genai_secret": os.environ["GENAI_API_SECRET_DEV"],

    "chat_db_url": os.environ["USER_CHAT_MONGO_DB_CONNECTION_URL"],
    "chat_collection_name": "user_chat_details",
    "chat_db_port": 7194,
    
    "prompt_templates_db_url": os.environ["PROMPT_TEMPLATES_MONGO_DB_CONNECTION_URL"],
    "prompt_templates_collection_name": "chatbot_prompts",
    "prompt_templates_db_port": 7194,

    "eda_ip_tracker_host":"maria4197-lb-fm-in.iglb.intel.com",
    "eda_ip_tracker_port":3307,
    "eda_ip_tracker_username":"eda_ip_tracker_so",
    "eda_ip_tracker_password":os.environ["EDA_IP_TRACKER_DB_PASSWORD_PROD"],
    "eda_ip_tracker_database":"eda_ip_tracker",
    
    "database_schema_mysql": {
      "host": "maria3147-lb-ir-in.dbaas.intel.com",
      "port": 3307,
      "username": "Database_schema_so",
      "password": os.environ["DATABASE_SCHEMA_DB_PASSWORD"],
      "database": "Database_schema",
    },

    "eipteam_contract_id": "de7170a9-f3b4-442d-98ff-b9490058f48d",
    "rdse_contract_id": "ebaa280a-0a23-45c7-a09d-ceb2becc620b",
    "disclosures_contract_id": "15e14062-81af-4204-9e34-4133197b0c2d",

    "user_email": "dona.jose@intel.com",
    "eip_chatbot_email": "eipchatbot@intel.com",
    "eip_chatbot_emaild": "dona.jose@intel.com",
    "eip_chatbot_password": os.environ["EIP_CHATBOT_EMAIL_PASSWORD"],
    "receiver_emails": [
        "dona.jose@intel.com",
        "geetha.d@intel.com"
    ],

    "ssl": {
      "ca": 'IntelSHA256RootCA-base64.crt',
    }    
}

prod_config = {
    
}

environment = os.getenv("APP_ENV") or "development"
global_config = prod_config if environment == "production" else dev_config


'''
production: {
    username: 'eda_ip_tracker_so',
    password: process.env.SQL_PASSWORD_PROD,
    database: 'eda_ip_tracker',
    host: 'maria4197-lb-fm-in.iglb.intel.com',
    port: 3307,
    dialect: 'mysql',
    ssl: {
      ca: 'IntelSHA256RootCA-base64.crt',
    },
    dialectOptions: {
      ssl: {
        require: true,
        rejectUnauthorized: false,
      },
    },
    timezone: '-08:00',
    pool: {
      max: 30,
    },
    logging: false,
  },

'''