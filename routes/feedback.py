from flask import Blueprint,request, jsonify
from bson.objectid import ObjectId
from src.mongoDbConnection import mongoDbConnection
from src.sendEmail import send_email
from config.config import global_config
import datetime
import json

config = global_config

ifeedback= Blueprint('ifeedback', __name__)

def update_db(chat_id, feedback):
    config = global_config
    connection_string = config["chat_db_url"]
    db_name = config["chat_db_name"]
    collection_name = config["chat_collection_name"]
    resp=None
    try:
        mongoClient = mongoDbConnection(connection_string, db_name, collection_name)
        _id = {
            "_id": ObjectId(chat_id),
        }
        record = {
            "feedback": feedback, 
        }
        resp = mongoClient.updateDetails(_id, record)
        return resp
    except Exception as e:
        print("Error:feedback:update_db: "+str(e))
        raise e

def send_error_email(error, question):
    print("*******************SENDING EMAIL**********************************")
    sender_email = config["eip_chatbot_email"]
    sender_password = config["eip_chatbot_password"]
    receiver_emails = config["receiver_emails"]
    subject = "ERROR IN EIP CHATBOT SERVICE FEEDBACK"
    body = str(error)+"\nChat id: "+question
    send_email(sender_email, sender_password, receiver_emails, subject, body)

@ifeedback.route("/feedback",methods=["POST"])
def get_feedback():
    print("**************************FEEDBACK******************************")
    data = request.get_json()  # Get the JSON data from the request
    chat_id = data['chat_id']
    feedback = data['feedback']
    print(data)

    # Update Feedback in Database
    print("*********UPDATING FEEDBACK IN DB*************************************")
    try:
        update_db(chat_id, feedback)
    except Exception as e:
        print("ERROR:feedback:get_feedback: "+str(e))
        send_error_email(str(e), chat_id)
        jsonify({'status': 'failed'})

    return jsonify({'status': 'success'})
    