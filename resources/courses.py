from pymongo import MongoClient, ReturnDocument, InsertOne, DeleteMany, ReplaceOne, UpdateOne
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


class Courses(Resource):
    def get(self):
        pass
    def post(self):
        data = request.json 
        db.courses.insert_one(data)

class Course(Resource):
    def get(self,code):
        course = db.courses.find_one(
            {'code':code}
        )

        return Response(
            list(course),
            mimetype='application/json'
        )

class SupervisorCourse(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        course = db.users.find_one({
            'email':current_user,
        },{
            '_id':False,
            'courses':True
        })
        if 'courses' in course:
            course = db.courses.find({
                'code':{'$in':course['courses']}
            })
            return Response(
                json_util.dumps(course),
                mimetype='application/json'
            )
        return []

    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        code = request.json
        if db.courses.find({
            'code':code
        }).count() > 0:
            db.users.update_one({
            'email':current_user
            },{
                '$addToSet':{
                    'courses': code
                }
            })
        else:
            abort(400,message="no course")

    @jwt_required
    def put(self):
        current_user = get_jwt_identity()
        code = request.json
        db.users.update_one({
            'email':current_user
        },{
            '$pull':{
                'courses':code
            }
        })
#api for user to find
class SearchSupervisorGroupworkTemplate(Resource):
    @jwt_required
    def get(self,supervisor,code):
        data = db.courses.find_one({
            'code':code,
            'templates.supervisor':supervisor
        })

        return Response(
            list(data),
            mimetype='application/json'
        )


#api for supervisor
class SupervisorGroupworkTemplate(Resource):
    @jwt_required
    def get(self,code):
        current_user = get_jwt_identity()
        data = db.courses.find_one(
            {
                'code':code,
                'templates.supervisor':current_user
            },{
                '_id':False,
                'templates.$':True
            }
          
        )

        if data is not None:
            if len(data) > 0:    
                return Response(
                    json_util.dumps(data['templates'][0]['template']),
                    mimetype='application/json'
                )


        return []

    @jwt_required
    def post(self,code):
        current_user = get_jwt_identity()
        data = request.json
        data['_id'] = ObjectId()
        for assignments in data['assignments']:
            if assignments['_id'] is "":
                assignments['_id'] = ObjectId()
            else:
                assignments['_id'] = ObjectId(assignments['_id'])
            for task in assignments['tasks']:
                if task['_id'] is "":
                    task['_id'] = ObjectId()
                else:
                    task['_id'] = ObjectId(task['_id'])
                     
        if db.courses.find(
            {'code':code,'templates.supervisor':current_user}
        ).count() > 0:
            db.courses.update_one({
                'code':code,
                'templates.supervisor':current_user
            },
            {
                '$addToSet':{
                    'templates.$.template':data
                }
            },upsert=True)
        else:
            db.courses.update_one({
                'code':code,
            },{
                '$addToSet':{
                    'templates':{
                        'supervisor':current_user,
                        'template':[data]
                    }
                }
            })

    @jwt_required
    def put(self,code):
        current_user = get_jwt_identity()
        data = request.json
        
        data['_id'] = ObjectId(data['_id'])
        for assignments in data['assignments']:
            if assignments['_id'] is "":
                assignments['_id'] = ObjectId()
            else:
                assignments['_id'] = ObjectId(assignments['_id'])
            for task in assignments['tasks']:
                if task['_id'] is "":
                    task['_id'] = ObjectId()
                else:
                    task['_id'] = ObjectId(task['_id'])



        db.courses.update_one(
            {'code':code,'templates.supervisor':current_user},
            {'$pull':{'templates.$.template':{
                    '_id':data['_id']
                }}}
        )

        db.courses.update_one(
            {'code':code,'templates.supervisor':current_user},
            {'$addToSet':{
                'templates.$.template':data
            }}
        )



