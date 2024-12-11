import jsonpickle
import json

def load_model(file_path='llm/model.json'):
    with open(file_path, 'r') as f:
        json_data = json.load(f)
    encoded_model = json_data["llm"]
    model = jsonpickle.decode(encoded_model)
    return model

def save_model(model_json, file_path='llm/model.json'):
    with open(file_path, 'w') as f:
        json.dump(model_json, f, indent=4)