from pymongo import MongoClient
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity,decode_token,create_refresh_token,jwt_refresh_token_required,
    set_access_cookies,set_refresh_cookies
)
import re
import datetime
import functools
from flask import request , jsonify, json
from flask_cors import CORS
from flask_restful import Resource, Api, abort
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import config
from main import db , mail
from bson.json_util import dumps, ObjectId
class Register(Resource):
    def post(self):
        print(request.json)
        email = request.json['email']
        password = request.json['password']
        if not re.match(r'^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$', email):
            abort(400, message='email is not valid')
        if len(password) < 6:
            abort(400,message="password is too short")
        if db.users.find({'email': email}).count() != 0:
            if db.users.find_one({'email': email})['active'] == True:
                abort(400, message='email is alread used.')
        else:
            #TODO: Mandatory Field
            user_id = db.users.insert_one({
                'email': email, 
                'password':generate_password_hash(password), 
                'active':False,
                'profile':{
                    'fname':'',
                    'lname':'',
                    'contactNo':'',
                    'programmeCode':'',
                },
                'role':2,
                'active_group':[],
                })
            #Initial Inbox 
            db.inbox.insert_one({
                '_id': ObjectId(),
                'user_id' :user_id.inserted_id
            })




        access_token = create_access_token(identity=email)
        message = 'Hello\n Thank You for Registering to our Website, Here Your Activation Code \n <a href="http:127.0.0.1:5000/v1/confirm/'+access_token+'"/>'
        msg = Message(recipients=[email],
                        body=message,
                        subject='Acitivation Code')
        #mail.send(msg)
        return {'email':email}

class Activate(Resource):
    def put(self):
        activation_code = request.json['activation_code']
        try:
            decoded = decode_token(activation_code)
        except:
           return {'message':'Something went wrong'},500
        email = decoded['email']
        db.users.update({'email':email}, {'$set':{'active':True}})

class ActivateURL(Resource):
    def get(self,token):
        activation_code = token
        try:
            decoded = decode_token(activation_code)
        except:
           return {'message':'Something went wrong'},500
        print(decoded)
        current_user = get_jwt_identity()
        db.users.update({'email':current_user}, {'$set':{'active':True}})


class Login(Resource):
    def post(self):
        email = request.json['email']
        password = request.json['password']
        print(email)
        if db.users.find({'email':email}).count() == 0:
            abort(400,message = 'User is not found')

        user = db.users.find_one({'email':email})
        if not check_password_hash(user['password'],password):
            abort(400,message="Password is incorrect")
        #if user['active'] is False:
        #    abort(400,message="Account is inactive")
        access_token = create_access_token(email)
        refresh_token = create_refresh_token(email)
        data = {'access_token':access_token,'refresh_token':refresh_token}
        return jsonify(data)

class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(current_user)
        return {
            'access_token':access_token
        }


