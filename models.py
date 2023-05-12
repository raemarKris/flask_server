from bson import ObjectId
from bson.json_util import dumps, default
import pymongo
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
client = pymongo.MongoClient("mongodb+srv://kris:Baltimore10@test.ltopuuj.mongodb.net/?retryWrites=true&w=majority")
db = client["test"]

class Users:
    def __init__(self, username, email=None, password=None, jwt_auth_active=False, date_joined=None, chats=None):
        self.username = username
        self.email = email
        self.password = password
        self.jwt_auth_active = jwt_auth_active
        self.date_joined = date_joined if date_joined is not None else datetime.utcnow()
        self.chats = chats if chats is not None else []

  
    def get_by_email(email):
        return db.users.find_one({'email': email})


    def get_by_id(user_id):
        return db.users.find_one({'_id': ObjectId(user_id)})

    def save(self):
        db.users.insert_one(self.to_dict())

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def update_email(self, new_email):
        self.email = new_email
        db.users.update_one({"username": self.username}, {"$set": {"email": self.email}})

    def update_username(self, new_username):
        old_username = self.username
        self.username = new_username
        db.users.update_one({"username": old_username}, {"$set": {"username": self.username}})

    def check_jwt_auth_active(self):
        return self.jwt_auth_active

    def set_jwt_auth_active(self, set_status):
        self.jwt_auth_active = set_status
        db.users.update_one({"username": self.username}, {"$set": {"jwt_auth_active": self.jwt_auth_active}})

    @staticmethod
    def get_by_username(username):
        user_dict = db.users.find_one({"username": username})
        if user_dict:
            return Users(**user_dict)
        else:
            return None

    
    def to_dict(self):
        user_dict = {
         "username": self.username,
        "email": self.email,
        "password": self.password,
        "jwt_auth_active": self.jwt_auth_active,
        "date_joined": self.date_joined,
        "chats": self.chats
     }
        print(user_dict)
        if '_id' in user_dict:
            user_dict['_id'] = str(user_dict['_id'])
        return user_dict
   


class Chats:
    def __init__(self, user_id, messages=None):
        self.user_id = user_id
        self.messages = messages if messages is not None else []

    def save(self):
        db.chats.insert_one(self.to_dict())

    def to_dict(self):
        chat_dict = {
            "user_id": self.user_id,
            "messages": self.messages
        }
        return chat_dict


class Messages:
    def __init__(self, chat_id, message, sender):
        self.chat_id = chat_id
        self.message = message
        self.sender = sender

    def save(self):
        db.messages.insert_one(self.to_dict())

    def to_dict(self):
        message_dict = {
            "chat_id": self.chat_id,
            "message": self.message,
            "sender": self.sender,
            "user_id": self.user_id
        }
        return message_dict




jwt_blocklist_collection = db["jwt_token_blocklist"]


class JWTTokenBlocklist:

    def __init__(self, jwt_token, created_at=None):
        self.jwt_token = jwt_token
        self.created_at = created_at or datetime.utcnow()

    def save(self):
        jwt_blocklist_collection.insert_one({
            "jwt_token": self.jwt_token,
            "created_at": self.created_at
        })

    @staticmethod
    def get_by_token(jwt_token):
        token_blocklist = jwt_blocklist_collection.find_one({"jwt_token": jwt_token})
        if token_blocklist:
            return JWTTokenBlocklist(
                jwt_token=token_blocklist["jwt_token"],
                created_at=token_blocklist["created_at"]
            )
        else:
            return None

    def __repr__(self):
        return f"Expired Token: {self.jwt_token}"
