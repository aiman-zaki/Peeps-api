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
import PIL.Image

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

    return '.' in filename and \
        filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS 

def fileExtension(filename):
    return filename.rsplit('.',1)[1].lower()

class ProfileImage(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        parse = reqparse.RequestParser()
        parse.add_argument('image',type=FileStorage, location='files')
        parse.add_argument('user_id')
        args = parse.parse_args()
        imageFile = (args['image'])
        user_id = args['user_id']
        print(fileExtension(imageFile.filename))
        if imageFile and allowed_file(imageFile.filename):
            path = app.root_path+app.config['UPLOAD_USERS_FOLDER']+user_id
            if os.path.exists(path) is False:
                os.mkdir(path)
            #if fileExtension(imageFile.filename) is not 'jpg':
                #imageFile = imageFile.convert('RGB') 
            imageFile.save(os.path.join(path,"profile.jpg"))
            return {"message":"Profile Picture Updated"},200
        return {"message":"Oops something is wrong"}
    
    def get(self):
        pass

        
class Profile(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = db.users.find_one(
            {'email': current_user},{'_id':1,'profile':1,'active_group':1,'email':1}
        )
        return Response(
            json_util.dumps(user),
            mimetype='application/json'
        )

    @jwt_required
    def put(self):
        current_user = get_jwt_identity()
        fname = request.json['fname']
        lname = request.json['lname']
        contact_no = request.json['contact_no']
        programme_code = request.json['programme_code']
        db.users.update_one(
            {'email':current_user},
            {'$set':
                {'profile':{
                    'fname':fname,
                    'lname':lname,
                    'contact_no':contact_no,
                    'programme_code':programme_code,
                }}
            }
        )

    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        contact_no = request.json['contact_no']
        programme_code = request.json['programme_code']
        db.users.update_one(
            {'email':current_user},
            {'$set':
                {'profile':{
                    'contact_no':contact_no,
                    'programme_code':programme_code}}})


class Groupworks(Resource):
    @jwt_required
    def get(self):
        current_user  = get_jwt_identity()
        
        active_group_list = db.users.find_one(
            {'email':current_user},
            {'_id':False,'active_group':True}
        )
        data = db.groupworks.find({'_id':{'$in':active_group_list['active_group']}})
        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )

    @jwt_required
    def put(self):
        current_user = get_jwt_identity()
        group_id = request.json["group_id"]
        request_date = request.json["request_date"]

        user_id = db.users.find_one(
            {'email':current_user},
            {'_id':True},
        )
        db.inbox.update_one(
            {
                'user_id':user_id['_id']
            },
            {
            '$addToSet':{
                'active_group_requests': {
                        'group_id':ObjectId(group_id),
                        'created_date':request_date,
                    }
                }
            },
            upsert=True
        ),
        db.groupworks.update_one(
            {
                '_id':ObjectId(group_id)
            },
            {
                '$addToSet':{
                    'requests':{
                        'email':current_user,
                        'created_date':request_date,
                    }
                }
            },
            upsert=True
        )


    

class SearchUser(Resource):
    def post(self):
        search = request.json['search']
        print(search)
        data = db.users.find(
            {
                'email': {'$regex':search}
            },
            {
                'email':1,
                'profile':1
            }
        )

        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )

class UserAssignmentsAndTasks(Resource):
    @jwt_required
    def get(self): 
        current_user = get_jwt_identity()
        data = db.groupworks.aggregate([
            {'$match':{
                'members.email':current_user,
            }},
            {'$project':{
                '_id':True,
                'assignments':True,
            }},
            {'$unwind':'$assignments'},
            {'$lookup':{
                'from': 'tasks',
                'localField': 'assignments._id',
                'foreignField': 'assignment_id',
                'as': 'tasks',
                },
            },
            {'$unwind':'$tasks'},
            {'$project':{
                'assignments':True,
                'tasks':'$tasks.tasks',
            }},
            {'$unwind':'$tasks'},
            {'$match':{
                'tasks.assign_to':current_user,
            }},
            {'$group':{
                '_id':{
                    '_id':'$_id',
                    'assignment_id':'$assignments._id'
                },
                
                'title':{'$first':'$assignments.title'},
                'due_date': {'$first':'$assignments.due_date'},
                'tasks':{'$push':'$tasks'}
            }},
            {'$project':{
                '_id':False,
                'group_id':'$_id._id',
                'assignment_id':'$_id.assignment_id',
                'assignment_title':'$title',
                'assignment_due_data':'$due_data',
                'tasks':'$tasks',
            }}
        ])

        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )