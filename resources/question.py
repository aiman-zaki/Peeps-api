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

questions = [
    {'question':'Is this guy real legit'},
    {'question':'Are you sure he is legit'}
]

class InitQuestions(Resource):
    def get(self):
        db.questions.insert_one(questions)

class Questions(Resource):
    def get(self):
        question = db.questions.find()
        print(question)
        return Response(
            json_util.dumps(question),
            mimetype='application/json'
        )

    def post(self):
        pass
        

