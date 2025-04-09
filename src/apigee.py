import requests
import time
import requests_oauthlib
import msal
from config.config import global_config

def get_apigee_access_token():
    config = global_config
    data = {
        'grant_type': 'client_credentials'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    token_url=config["apigee"]["token_url"]
    proxies=config["proxies"]
    client_id=config["apigee"]["client_id"]
    client_secret =config["apigee"]["client_secret"]

    try:
        response = requests.post(
            token_url,
            data=data,
            headers=headers,
            auth=(client_id, client_secret),
            proxies=proxies,
        )
        response.raise_for_status()
        response_json = response.json()
        access_token_expires_on = int(response_json.get('expires_in')) + time.time() - 60
        access_token = response_json.get('access_token')

        return access_token
    except requests.exceptions.RequestException as e:
        print(f"Failed to get access token: {e}")
        raise

def get_apigee_access_token_implicit():
    config = global_config
    
    client_id=config["azure_client_id"]
    client_secret =config["azure_client_secret"]

    auth_url = "https://login.microsoftonline.com/46c98d88-e344-4ed4-8496-4ed7712e255d/oauth2/v2.0/authorize"
    redirect_uri = "https://eip-chatbot.apps1-fm-int.icloud.intel.com/"
    token_url = config["apigee"]["token_url"]
    scope = "api://79f5373a-d47c-455f-b728-d2b23345cb3e/eip_chatbot"
    proxies=config["proxies"]
    
    data = {
        'grant_type': 'implicit',
        'scope': scope
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        response = requests.post(
            auth_url,
            data=data,
            headers=headers,
            auth=(client_id, client_secret),
            proxies=proxies
        )
        response.raise_for_status()
        # print(response.content)
        # response_json = response.json()
        # access_token_expires_on = int(response_json.get('expires_in')) + time.time() - 60
        # access_token = response_json.get('access_token')

        # return access_token
    except requests.exceptions.RequestException as e:
        print(f"Failed to get access token: {e}")
        raise
    
    authority="https://login.microsoftonline.com/46c98d88-e344-4ed4-8496-4ed7712e255d"
    app = msal.ConfidentialClientApplication(
    client_id,
    authority=authority,
    client_credential=client_secret,
    # redirect_uri=redirect_uri
    )
    
    
    # Acquire a token
    scope = ['https://graph.microsoft.com/.default']
    result = app.acquire_token_for_client(scopes=scope)

    if 'access_token' in result:
        print('Access token acquired:', result['access_token'])
    else:
        print('Error acquiring token:', result.get('error_description'))

   
    return result['access_token']
