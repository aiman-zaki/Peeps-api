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
import PIL.Image


class Forum(Resource):
    def get(self,course):

        dicussions = db.collaborate.find_one(
            {'course':course},
            {'_id':False,'discussions':True}
        )

        return Response(
            json_util.dumps(dicussions),
            mimetype='application/json'

        )
    @jwt_required
    def post(self,course):
        current_user = get_jwt_identity()
        discussion = request.json
        discussion['_id'] = ObjectId()
        discussion['by'] = current_user
        db.collaborate.update_one(
            {'course':course},
            {'$addToSet':{
                'discussions':discussion
            }},
            upsert=True
        )


class Discussion(Resource):
    @jwt_required
    def get(self,course,discussion):
        discussion = db.collaborate.find_one(
            {'course':course,'discussions._id':ObjectId(discussion)},
            {'_id':False,'discussions.$':True}
        )
        if 'discussions' not in discussion:
            discussion['discussions'] = []
            
        return Response(
            json_util.dumps(discussion['discussions'][0]),
            mimetype='application/json'
        )
    @jwt_required
    def post(self,course,discussion):
        current_user = get_jwt_identity()
        reply = request.json
        reply['_id'] = ObjectId()
        reply['by'] = current_user
        db.collaborate.update_one(
            {'course':course,'discussions._id':ObjectId(discussion)},
            {'$addToSet':{
                'discussions.$.replies':reply
            }}
        )

    @jwt_required
    def put(self,course,discussion):
        reply = request.json
        print(reply)
        db.collaborate.update_one(
            {'course':course,'discussions._id':ObjectId(discussion)},
            {'$pull':{
                'discussions.$.replies': {
                    '_id':ObjectId(reply['_id'])
                }
            }}
        )


class Markers(Resource):
    def get(self,course):
        markers = db.collaborate.find_one(
            {'course':course},
            {'_id':False,'markers':True}
        )

        if markers is None:
            markers = {}

        if 'markers' not in markers:
            markers['markers'] = []
        
        return Response(
            json_util.dumps(markers['markers']),
            mimetype='application/json'
        )

    def post(self,course):
        marker = request.json
        marker['_id'] = ObjectId()
        print(marker)
        if db.collaborate.find(
            {
                '$and':[
                    {'course':course},
                    {'markers.email':marker['email']}
                ]
            }
        ).count() == 0 : 
            db.collaborate.update_one(
                {'course':course},
                {'$addToSet':{
                    'markers':marker
                }},upsert=True   
            )
        else: 
            #TODO : temp 
            db.collaborate.update_one(
                {'course':course},
                {'$pull':{
                    'markers':{
                        'email':marker['email']
                    }
                }}
            )
            db.collaborate.update_one(
                {'course':course},
                {'$addToSet':{
                    'markers':marker
                }},upsert=True   
            )

        
