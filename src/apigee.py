import requests
import time
from config.config import global_config

def get_access_token():
    config = global_config
    data = {
        'grant_type': 'client_credentials'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    auth_url=config["apigee"]["token_url"]
    proxies=config["proxies"]
    client_id=config["apigee"]["client_id"]
    client_secret =config["apigee"]["client_secret"]

    try:
        response = requests.post(
            auth_url,
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

