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
from main import mongodb_connect  
from bson.json_util import dumps, ObjectId
import PIL.Image

datetimestring = str(datetime.datetime.now())

def insert_active_user_per_week():
    data = mongodb_connect().users.aggregate([
        {'$project':{
            'current_week':{'$subtract':['$last_logined',7*24*60*60000]}
        }},
        {'$count':'current_week'}
    ])

    data = list(data)[0]

    data = mongodb_connect().stats_active_user.insert_one(
        {
            '_id':ObjectId(),
            'inserted_date':datetimestring,
            'count': data['current_week']
        }
    )
