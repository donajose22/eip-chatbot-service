from flask import Flask, session
from flask_session import Session
from flask_cors import CORS
from flask_talisman import Talisman
from langchain_sdk.Langchain_sdk import LangChainCustom 
from config.config import global_config
import redis
import json
import jsonpickle

config = global_config

app = Flask(__name__)
app.secret_key = config['app_secret_key']
CORS(app)
Talisman(app,force_https=False)

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.StrictRedis(host=config['redis_consts']['url'], 
                                                port=config['redis_consts']['port'], 
                                                db=0, 
                                                password=config['redis_consts']['pwd'],
                                                ssl=True,
                                                ssl_ca_certs="IntelSHA256RootCA-base64.crt")
Session(app)

@app.route('/')
def hello_world():
    return "hello world"

#--------------------------
from routes.generate import igenerate
from routes.feedback import ifeedback
from routes.loadPrompts import iloadprompts
from routes.fetchTopics import ifetchtopics
#--------------------------
app.register_blueprint(igenerate, url_prefix='/')
app.register_blueprint(ifeedback, url_prefix='/')
app.register_blueprint(iloadprompts, url_prefix='/')
app.register_blueprint(ifetchtopics, url_prefix='/')
#--------------------------

def generate_model(prompt = None):
    client_id = global_config["data_pipeline_client_id"]
    client_secret = global_config["data_pipeline_secret"]
    # client_id = global_config["apigee"]["client_id"]
    # client_secret = global_config["apigee"]["client_secret"]

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

def save_model(model_json, file_path='llm/model.json'):
    with open(file_path, 'w') as f:
        json.dump(model_json, f, indent=4)

if __name__ == '__main__':
    model = generate_model()
    encoded_model = jsonpickle.encode(model)
    model_json = {
        "llm": encoded_model
    }
    save_model(model_json)
    print("Model created and saved.")

    app.run(debug=True, host='0.0.0.0', port=5000)