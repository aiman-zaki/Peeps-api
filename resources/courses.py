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

        '''template = db.courses.aggregate([
            {
                '$match':{
                    'code':code,
            }},
            {'$unwind':'$templates'},
            {
                '$project':{
                    '_id':False,
                    'template':{
                        '$filter':{
                            'input':'$templates.template',
                            'as':'template',
                            'cond':{
                                '$and':[
                                    {'$eq':['$$template._id',ObjectId(template_id)],},
                                    
                                ]    
                            }
                        }
                    }
                }
            }
       
        ])
        template = list(template)[0]['template']'''

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



