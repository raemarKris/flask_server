from __future__ import print_function
from config import *

import tiktoken
import pinecone
import uuid
import sys
import logging

from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
from flask import request

from handle_file import handle_file
from answer_question import get_answer_from_files
from conversation import get_answer
from bson import ObjectId
from routes import rest_api
from models import db
from flask_migrate import Migrate
from models import Users, Chats
from datetime import datetime
from pymongo import MongoClient
import json

client = MongoClient("mongodb+srv://kris:Baltimore10@test.ltopuuj.mongodb.net/?retryWrites=true&w=majority")
db = client["test"]

users_collection = db["users"]
chats_collection = db["chats"]
messages_collection = db["messages"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def load_pinecone_index() -> pinecone.Index:
    """
    Load index from Pinecone, raise error if the index can't be found.
    """
    pinecone.init(
        api_key=PINECONE_API_KEY,
        environment=PINECONE_ENV,
    )
    index_name = PINECONE_INDEX
    if not index_name in pinecone.list_indexes():
        print(pinecone.list_indexes())
        raise KeyError(f"Index '{index_name}' does not exist.")
    index = pinecone.Index(index_name)

    return index

BASE_DIR = os.path.abspath(os.path.dirname(__file__))




def create_app():
    pinecone_index = load_pinecone_index()
    tokenizer = tiktoken.get_encoding("gpt2")
    session_id = str(uuid.uuid4().hex)
    app = Flask(__name__)
    app.pinecone_index = pinecone_index
    app.tokenizer = tokenizer
    app.session_id = session_id
    app.config.from_object('config.BaseConfig')
    app.config["JWT_SECRET_KEY"] = "super-secret"
    # app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')
    # db.create_all()
    # db.init_app(app)
   
    rest_api.init_app(app)
    # log session id
    logging.info(f"session_id: {session_id}")
    app.config["file_text_dict"] = {}
    CORS(app, supports_credentials=True)

    return app

app = create_app()




@app.route(f"/process_file", methods=["POST"])
@cross_origin(supports_credentials=True)
def process_file():
    try:
        file = request.files['file']
        logging.info(str(file))
        handle_file(
            file, app.session_id, app.pinecone_index, app.tokenizer)
        return jsonify({"success": True})
    except Exception as e:
        logging.error(str(e))
        return jsonify({"success": False})

@app.route(f"/answer_question", methods=["POST"])
@cross_origin(supports_credentials=True)
def answer_question():
    try:
        params = request.get_json()
        question = params["question"]

        answer_question_response = get_answer_from_files(
            question, app.session_id, app.pinecone_index)
        logging.info(f"answer_question_response: {answer_question_response}")
        print( "answer_question_response:", answer_question_response)
        return answer_question_response
    except Exception as e:
        return str(e)



@app.route(f'/legalai_conversation', methods=['POST'])
def legalai_conversation():
        params = request.get_json()
        question = params["question"]
        answer_question = get_answer(question)
        logging.info(f"answer_question_response: {answer_question}")

        return answer_question


@app.route('/api/chats', methods=['POST'])

def create_chat():
    print(request.get_json())
    data = request.get_json()
    user_id = data.get('userId')
    chat_id = data.get('chatId')

    # check if the user exists
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    print('USER')
    print(user)
    if user is None:
        print('NO USER ID')
        return jsonify({'error': 'User not found'}), 404

    # create a new chat for the user
    print('USER ID')
    print(user_id)
    chat = {
        "user_id": user_id,
        "chat_id": chat_id,
        "created_at": datetime.utcnow()
    }
    chats_collection.insert_one(chat)

    return jsonify({'success': True, 'chatId': chat_id}), 201

    # return {"success": True, "token": token, "user": user_dict}, 200



# create a new message for a chat
@app.route('/api/messages', methods=['POST'])
def create_message():
    print(request.get_json())

    data = request.get_json()

    message_text = data.get('message_text')
    sender = data.get('sender')
    chat_id = data.get('chat_id')
    user_id = data.get('user_id')

    chat = chats_collection.find_one({"chat_id": chat_id})

    print('Chat')
    print(chat)

    if chat is None:
        return jsonify({'error': 'Chat not found'}), 404

    
    message = {
        'user_id': user_id,
        'message' :message_text,
        'sender':sender,
        "chat_id": chat_id,
        "created_at": datetime.utcnow()
    }
    messages_collection.insert_one(message)


    return jsonify({'success': True}), 201




@app.route('/api/get_messages')
def get_messages():
    user_id = request.args.get('user_id')

    messages = messages_collection.find({"user_id": user_id})

    if messages is None:
        return jsonify({'error': 'Chat not found'}), 404

    messages_list = []

    for message in messages:
        message['_id'] = str(message['_id'])

        message_dict = {
            "chat_id": message.get("chat_id"),
            "message": message.get("message"),
            "sender": message.get("sender"),
            "id": str(message['_id'])
        }

        messages_list.append(message_dict)
    print(messages_list)
    return jsonify({"success": True,  "messages": messages_list}), 200





@app.route("/healthcheck", methods=["GET"])
@cross_origin(supports_credentials=True)
def healthcheck():
    return "OK"

if __name__ == "__main__":
    app.run(debug=True, port=SERVER_PORT, threaded=True)
