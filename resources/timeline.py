from pymongo import MongoClient, ReturnDocument, InsertOne, DeleteMany, ReplaceOne, UpdateOne
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, decode_token, create_refresh_token, jwt_refresh_token_required,
    set_access_cookies, set_refresh_cookies
)
import re
import datetime
import os
import functools
import base64
from flask import request, jsonify, json, Response
from flask_cors import CORS
from flask_restful import Resource, Api, abort,  reqparse
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from bson import json_util
from main import db, app
from bson.json_util import dumps, ObjectId
import PIL.Image


class Timeline(Resource):
    def get(self,group_id):
        data = db.timelines.find_one(
            {'group_id':ObjectId(group_id)},
            {'_id:':False,'contributions':{'$slice':-10}},
            
        )
        if 'contributions' not in data:
            print("test")
            data['contributions'] = []
        return Response(
            json_util.dumps(data['contributions']),
            mimetype="application/json"
        )

    def post(self,group_id):
        data = request.json
        data.pop('room',None)
        db.timelines.update_one(
            {'group_id':ObjectId(group_id)},
            {'$addToSet': {
                'contributions': data
            }}
            ,upsert=True
        )

class TimelineCount(Resource):
    def get(self,group_id,count):
        pass
