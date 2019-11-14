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
import base64
from flask import request , jsonify, json , Response 
from flask_cors import CORS
from flask_restful import Resource, Api, abort ,  reqparse
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from bson import json_util
from main import db , app 
from bson.json_util import dumps, ObjectId
import PIL.Image

class References(Resource):
    def get(self,group_id):
        references = db.stash.find_one(
            {'group_id':ObjectId(group_id)},
            {
                '_id':False,
                'references':True,
            }
        )
        if references is None:
            return []
        return Response(
            json_util.dumps(references['references']),
            mimetype='application/json'
        )
    
    def post(self,group_id):
        reference = request.json
        reference['_id'] = ObjectId()
        reference.pop('room',None)
        db.stash.update_one(
            {'group_id':ObjectId(group_id)},
            {'$addToSet':{
                'references':reference
            }}
        ,upsert=True
        )

class PublicReferences(Resource):
    def get(self,group_id):
        references = db.stash.find_one(
            {
                '$and':[
                    {'group_id':ObjectId(group_id)},
                    {'references.publicity':1}
                ]
            },
            {
                '_id':False,
                'references.$':True
            }
        
        )
        if references is None:
            return []
        return Response(
            json_util.dumps(references['references']),
            mimetype='application/json'
        )
        

class Notes(Resource):
    def get(self,group_id):
        print(group_id)
        notes = db.stash.find_one(
            {
                'group_id':ObjectId(group_id),
            },
            {
                '_id':False,
                'notes':True,
            }
        )
        print(notes)
        return Response(
            json_util.dumps(notes),
            mimetype='application/json'
        )