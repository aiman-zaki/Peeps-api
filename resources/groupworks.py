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
from flask_restful import Resource, Api, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson import json_util
from main import db , app 
from bson.json_util import dumps, ObjectId


class GroupWork(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        data = db.users.find_one(
            {'email': current_user},{'_id':0,'active_group':1}
        )        
        groups = db.groupworks.find({'_id':{'$in': data['active_group']}})
        jsonList = []
        if groups is None:
            for group in groups:
                jsonList.append(group)        
            return Response(
                json_util.dumps(jsonList),
                mimetype='application/json',

            )
        else:
            return Response(
                (
                    {"message":"No Data Recorded"}
                ),
                mimetype='application/json'
            )


    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        name = request.json['name']
        description = request.json['description']
        course = request.json['course']
        invitation_list = request.json['members']
        _id = db.groupworks.insert_one({
            'creator':current_user,
            'name':name,
            'description':description,
            'course':course,
            'invitation_list':invitation_list
        })
        db.users.update_many({'email': {'$in': invitation_list}}, {'$push': {'inbox.group_invitation': {'inviter':current_user,'group_id':_id.inserted_id,'accept':False}}},upsert=True)
        return Response(
            status=200
        )
      

class ActiveGroupWorkDetails(Resource):
    def put(self):
        #current_user = get_jwt_identity()
        active_group_list = request.json['active_group']
        active_group_list = [ObjectId(data) for data in active_group_list]
        data = db.groupworks.find({'_id':{'$in':active_group_list}})

        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )

class Stash(Resource):
    def put(self):
        group_id = ObjectId(request.json['group_id'])
        stash = db.groupworks.find({'_id':group_id},{'stash':1})
        return Response(
            json_util.dumps(stash),
            mimetype='application/json'
        )




