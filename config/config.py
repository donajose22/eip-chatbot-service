import os
from dotenv import load_dotenv

load_dotenv()

dev_config = {
    "cert_path": "certificate_chain.pem",
    "auth_url": "https://apis-internal.intel.com/v1/auth/token",
    "apigee": {
        "token_url_internal": "https://apis-internal.intel.com/v1/auth/token",
        "token_url": "https://apis.intel.com/v1/auth/token",
        "genai_client_id": "d36a38f9-f7ff-4052-9660-9d1dd493c297",
        "client_id": "fc4d18f6-8074-48dc-b97e-7f3807754764",
        "client_secret": os.environ["APIGEE_CLIENT_SECRET_DEV"],
    },
    "proxies": {
        "http": "http://proxy-dmz.intel.com:912",
        "https": "http://proxy-dmz.intel.com:912",
        "no_proxy": "localhost,*.intel.com"
    },
    "proxy_us": {
        "http": "http://proxy-us.intel.com:912",
        "https": "http://proxy-us.intel.com:912",
    },
    "proxy_url": "http://proxy-dmz.intel.com:912",
    "embed_url": "https://apis-internal.intel.com/generativeaiembedding/v1/embed",
    "retriever_url" : "https://apis.intel.com/gai/data-pipeline/v1/retrieve-details/retrieve",
    "dms_chat_db_url": "mongodb://DMS_chat_so:vC60n0dRp6z6322@d1ir1mon021.ger.corp.intel.com:7194,d2ir1mon021.ger.corp.intel.com:7194,d3ir1mon021.ger.corp.intel.com:7194/DMS_chat?ssl=true&replicaSet=mongo7194",
    "dms_chat_collection_name": "user_chat_details",
    "dms_chat_db_port": 7194,
    # "wiki_docs_db_url": "mongodb://DMS_wiki_docs_so:7OsW2W41xC4P104@d1ir1mon021.ger.corp.intel.com:7194,d2ir1mon021.ger.corp.intel.com:7194,d3ir1mon021.ger.corp.intel.com:7194/DMS_wiki_docs?ssl=true&replicaSet=mongo7194",
    # "wiki_docs_db_port": 7194,
    # "wiki_docs_collection_name": "docs_embeddings",
    "eipteam_contract_id": "de7170a9-f3b4-442d-98ff-b9490058f48d",
    # "rdse_contract": '{\"app_id\": \"47f665f0-9809-4d0e-960a-c74d4036a131\", \"global\": {\"customer_type\": \"pipeline\"}, \"crawlers\": [{\"source\": \"wiki\", \"contacts\": [\"dona.jose@intel.com\"], \"pipeline\": {\"chunk\": {\"kwargs\": {\"chunk_size\": 512, \"chunk_overlap\": 48, \"tokenizer_model\": \"gpt-4o\"}, \"module\": \"llam_tiktoken\"}, \"index\": {\"kwargs\": {\"truncate_table\": \"No\", \"embedding_model\": \"text-embedding-ada-002\", \"embedding_provider\": \"forge\"}, \"module\": \"llam_vector_pg\"}, \"setup\": {\"kwargs\": {}, \"module\": \"default\"}, \"extract\": {\"kwargs\": {\"auto\": \"true\"}, \"module\": \"simple_reader\"}, \"complete\": {\"kwargs\": {}, \"module\": \"default\"}, \"preprocess\": {\"kwargs\": {\"clean_only\": \"true\"}, \"module\": \"clean_and_lem\"}, \"postprocess\": {\"kwargs\": {\"top_keywords\": 3}, \"module\": \"default\"}}, \"resources\": [{\"url\": \"https://wiki.ith.intel.com/display/eipteam\"}], \"credential\": {\"system_id\": \"sys_crawlwiki\"}, \"data_classification_level\": \"Intel Confidential\"}], \"business_id\": \"12256147\"}',
    "rdse_contract_id": "ebaa280a-0a23-45c7-a09d-ceb2becc620b",
    
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
      ca: '../IntelSHA256RootCA-base64.crt',
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