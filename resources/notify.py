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



class SupervisorNotified(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
   
        data = db.notify.aggregate(
            [
                {
                    '$match': {
                        'email':current_user
                }, },
                {
                    '$project': {
                        'supervisor_notify': {
                            '$filter': {
                                'input': '$supervisor_notify',
                                'as': 'notify',
                                'cond': {'$eq': ['$$notify.notified', False]}
                            }
                        }
                    }
                },
            ],
        )

        db.notify.update_one(
            {'email':current_user},
            {
                '$set':{
                    'supervisor_notify.$[].notified':True
                }
            }
        )

        data = (list(data)[0])['supervisor_notify']

        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )