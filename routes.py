

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
from flask_restx import Api, Resource, fields, reqparse
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask import Flask, request
from models import Users, Chats
from pymongo import MongoClient
import jwt 
from config import BaseConfig
from bson import json_util
from bson.objectid import ObjectId

client =MongoClient("mongodb+srv://kris:Baltimore10@test.ltopuuj.mongodb.net/?retryWrites=true&w=majority")
db = client["test"]

users = db['users']


rest_api = Api(version="1.0", title="Users API")


"""
    Flask-Restx models for api request and response data
"""

signup_model = rest_api.model('SignUpModel', {"username": fields.String(required=True, min_length=2, max_length=32),
                                              "email": fields.String(required=True, min_length=4, max_length=64),
                                              "password": fields.String(required=True, min_length=4, max_length=16)
                                              })

login_model = rest_api.model('LoginModel', {"email": fields.String(required=True, min_length=4, max_length=64),
                                            "password": fields.String(required=True, min_length=4, max_length=16)
                                            })

user_edit_model = rest_api.model('UserEditModel', {"userID": fields.String(required=True, min_length=1, max_length=32),
                                                   "username": fields.String(required=True, min_length=2, max_length=32),
                                                   "email": fields.String(required=True, min_length=4, max_length=64)
                                                   })


"""
    Flask-Restx routes
"""


@rest_api.route('/api/users/register')
class Register(Resource):
    """
       Creates a new user by taking 'signup_model' input
    """

    @rest_api.expect(signup_model, validate=True)
    def post(self):

        req_data = request.get_json()

        _username = req_data.get("username")
        _email = req_data.get("email")
        _password = req_data.get("password")

        user_exists = db.users.find_one({"email": _email})
        if user_exists:
            return {"success": False,
                    "msg": "Email already taken"}, 400

        new_user = {
            "username": _username,
            "email": _email,
            "password": generate_password_hash(_password)
        }

        db.users.insert_one(new_user)

        return {"success": True,
                "userID": str(new_user["_id"]),
                "msg": "The user was successfully registered"}, 200




@rest_api.route('/api/users/login')
class Login(Resource):

    @rest_api.expect(login_model, validate=True)
    def post(self):

        req_data = request.get_json()

        print('RESPONSE')
        print(req_data)

        _email = req_data.get("email")
        _password = req_data.get("password")

        user_exists = users.find_one({"email": _email})

        if not user_exists:
            return {"success": False,
                    "msg": "This email does not exist."}, 400

        if not check_password_hash(user_exists['password'], _password):
            return {"success": False,
                    "msg": "Wrong credentials."}, 400

        # create access token uwing JWT
        token = jwt.encode({'email': _email, 'exp': datetime.utcnow() + timedelta(minutes=30)}, BaseConfig.SECRET_KEY)

        users.update_one({"_id": ObjectId(user_exists['_id'])}, {"$set": {"jwt_auth_active": True}})

       
       
        user_dict = {
         "username": user_exists.get("username"),
        "email": user_exists.get("email"),
        "password": user_exists.get("password"),
        "jwt_auth_active": True,
        "date_joined": user_exists.get("date_joined"),
        "chats": user_exists.get("chats"),
        "user_id": str(user_exists['_id'])
         }

        return {"success": True, "token": token, "user": user_dict}, 200
       

        # user_dict_json = json_util.dumps(user_dict)
        # return user_dict_json, 200



@rest_api.route('/api/users/logout')
class LogoutUser(Resource):
    """
       Logs out User using 'logout_model' input
    """

    # @token_required
    def post(self, current_user):

        _jwt_token = request.headers["authorization"]

        jwt_block = JWTTokenBlocklist(jwt_token=_jwt_token, created_at=datetime.now(timezone.utc))
        jwt_block.save()

        current_user.set_jwt_auth_active(False)
        current_user.save()

        return {"success": True}, 200







