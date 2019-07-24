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
from app import db , app 
from bson.json_util import dumps, ObjectId


class GroupWork(Resource):
    #list of joined groupwork
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        data = db.users.find_one(
            {'_id': ObjectId(current_user)},{'_id':0,'joined_group':1}
        )        

        groups = db.groupworks.find({'tag':{'$in': data['joined_group']}})
        jsonList = []
        for group in groups:
            jsonList.append(group)
        print(jsonList)
        return Response(
            json_util.dumps(jsonList),
            mimetype='application/json',

        )

           

    
    @jwt_required
    def post(self):
        #current_user = get_jwt_identity()
       # _groupid = db.groupworks.insert()
       pass