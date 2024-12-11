from flask import Flask
from flask_cors import CORS
from flask_talisman import Talisman
from langchain_sdk.Langchain_sdk import LangChainCustom 
import config
from config.config import global_config
import json

app = Flask(__name__)
CORS(app)
Talisman(app,force_https=False)

@app.route('/')
def hello_world():
    return "hello world"

#--------------------------
from routes.generate import igenerate
#--------------------------
app.register_blueprint(igenerate, url_prefix='/')
#--------------------------

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
                            # system_prompt=prompt
                            
    return llm

def save_model(model_json, file_path='llm/model.json'):
    with open(file_path, 'w') as f:
        json.dump(model_json, f, indent=4)

import jsonpickle

if __name__ == '__main__':
    model = generate_model()
    encoded_model = jsonpickle.encode(model)
    model_json = {
        "llm": encoded_model
    }
    save_model(model_json)

    app.run(debug=True, host='0.0.0.0', port=5000)