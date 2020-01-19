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

datetimestring = str(datetime.datetime.now())


class Bulletin(Resource):
    @jwt_required
    def get(self):
        data = db.bulletin_board.find()

        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )

    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        data = request.json
        data['_id'] = ObjectId()
        data['email'] = current_user
        db.bulletin_board.insert_one(data)

        return {'message':'data inserted'},200

    @jwt_required
    def put(self):
        data = request.json
        db.bulletin_board.delete_one({'_id':ObjectId(data['_id'])})
        return {'message':'data deleted'},200


