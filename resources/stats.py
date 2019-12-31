from pymongo import MongoClient, ReturnDocument,InsertOne, DeleteMany, ReplaceOne, UpdateOne
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, decode_token, create_refresh_token, jwt_refresh_token_required,
    set_access_cookies, set_refresh_cookies
)
import re
import datetime
import os
import functools
from flask import request, jsonify, json, Response
from flask_cors import CORS
from flask_restful import Resource, Api, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson import json_util
from main import db, app
from bson.json_util import dumps, ObjectId




class UsersActivePerWeek(Resource):
    def get(self):
        data = db.users.aggregate([
            {'$project':{
                'last_logined':{'$subtract':['$last_logined',7*24*60*60000]}
            }},
            {'$count':'last_logined'}
        ])


        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )


