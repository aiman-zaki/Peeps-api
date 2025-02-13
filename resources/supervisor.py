from pymongo import MongoClient
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity,decode_token,create_refresh_token,jwt_refresh_token_required,
    set_access_cookies,set_refresh_cookies
)
import re
import datetime
import os
import functools
from flask import request , jsonify, json , Response
from flask_cors import CORS
from flask_restful import Resource, Api, abort,reqparse
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from bson import json_util
from main import db , app 
from bson.json_util import dumps, ObjectId


class SuperviseGroupworks(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        role = db.users.find_one({
            'email':current_user,
        },{
            '_id':False,'role':True,
        })
        
        if role['role'] == 2:
            abort(400,message = 'User is not a supervsior')

        supervised = db.groupworks.find(
            {'supervisor':current_user}
        )

        if supervised is None:
            return []
        return Response(
            json_util.dumps(supervised),
            mimetype='application/json'
        )
        
class GroupworkAnnouncements(Resource):
    @jwt_required
    def get(self,group_id):
        data = db.groupworks.find_one({'_id':ObjectId(group_id)},{'_id':False,'supervisor_messages':True})
        return Response(
            json_util.dumps(data['supervisor_messages']),
            mimetype='application/json'
        )

    @jwt_required
    def post(self,group_id):
        data = request.json['data']
        data['_id'] = ObjectId()
        data['email'] = get_jwt_identity()
        group_id = request.json['group_id']
        db.groupworks.update_one({'_id':ObjectId(group_id)},{'$addToSet':{
            'supervisor_messages':data
        }},upsert=True)


class CreateGroupworkAnnouncement(Resource):
    @jwt_required
    def post(self):
        print("asasa")
        print(request.json)
        data = request.json['data']
        data['_id'] = ObjectId()
        data['email'] = get_jwt_identity()
        group_id = request.json['group_id']
        db.groupworks.update_one({'_id':ObjectId(group_id)},{'$addToset':{
            'supervisor_messages':data
        }},upsert=True)