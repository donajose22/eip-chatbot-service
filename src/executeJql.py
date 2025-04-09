import requests
import urllib3
import json
from requests.auth import HTTPBasicAuth
from config.config import global_config


config = global_config

def execute_jql_query(query):
    print("Inside execut_jql_query function")
    # Create a custom SSL context
    ssl_context = urllib3.util.ssl_.create_urllib3_context()
    ssl_context.set_ciphers('TLSv1.2')

    # Create a custom HTTPS adapter
    class TLSAdapter(requests.adapters.HTTPAdapter):
        def init_poolmanager(self, *args, **kwargs):
            kwargs['ssl_context'] = ssl_context
            return super().init_poolmanager(*args, **kwargs)

    # Create a session and mount the adapter
    session = requests.Session()
    session.mount('https://', TLSAdapter())
    
    jiraUrl = config['jira_api_server_url']+f'?jql={query}'
    username = config['eip_chatbot_username']
    password = config["eip_chatbot_password"]

    response = requests.get(
        jiraUrl,
        auth=HTTPBasicAuth(username, password),
        verify=False
    )
    
    print(response.status_code)
    if(response.status_code == 200 or response.status_code == 400):
        query_results = json.loads(response.text)
        return response.status_code, query_results
    else:
        raise Exception