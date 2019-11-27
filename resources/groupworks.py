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
import datetime

def countTaskSeq():
    counter = db.counter.find_one_and_update(
        {'counter': 'task'},
        {
            '$inc': {
                'seq': 1
            }
        },
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return counter['counter']

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def fileExtension(filename):
    return filename.rsplit('.', 1)[1].lower()


class BaseGroupworks(Resource):
    @jwt_required
    def put(self):

        search = request.json['search']

        data = db.groupworks.find(
            {
                'course': {'$regex': search}
            },
        )

        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )


class GroupworkProfileImage(Resource):
    def post(self):
        parse = reqparse.RequestParser()
        parse.add_argument('image', type=FileStorage, location='files')
        parse.add_argument('group_id')
        args = parse.parse_args()
        imageFile = (args['image'])
        group_id = args['group_id']

        if imageFile and allowed_file(imageFile.filename):
            path = app.root_path+app.config['UPLOAD_GROUPWORK_FOLDER']+group_id
            if os.path.exists(path) is False:
                os.mkdir(path)
            if fileExtension(imageFile.filename) is not 'jpg':
                imageFile = PIL.Image.open(imageFile)
                imageFile = imageFile.convert('RGB')
            imageFile.save(os.path.join(path, "profile.jpg"))
            return {"message": "Profile Picture Updated"}, 200
        return {"message": "Oops something is wrong"}

    def get(self):
        pass


class Groupworks(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        data = db.users.find_one(
            {'email': current_user}, {'_id': False, 'active_group': True}
        )
        groups = db.groupworks.find({'_id': {'$in': data['active_group']}})
        jsonList = []
        if groups is None:
            for group in groups:
                jsonList.append(group)
            return Response(
                json_util.dumps(jsonList),
                mimetype='application/json',

            )
        else:
            return Response(
                (
                    {"message": "No Data Recorded"}
                ),
                mimetype='application/json'
            )

    @jwt_required
    def put(self):
        current_user = get_jwt_identity()
        group_id = request.json['group_id']
        supervisor = request.json['supervisor']
        description = request.json['description']
        course = request.json['course']

        try:
            db.groupworks.update_one(
                {'_id': ObjectId(group_id)},
                {
                    '$set': {
                        'supervisor': supervisor,
                        'description': description,
                        'course': course,
                    }
                }
            )
        except:

            abort(400, message="Something Wrong")

    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        name = request.json['name']
        description = request.json['description']
        course = request.json['course']
        template_id = request.json['template_id']
        invitation_list = [] if request.json['members'] == None else request.json['members']
        _id = db.groupworks.insert_one({
            'creator': current_user,
            'name': name,
            'description': description,
            'course': course,
            'invitation_list': invitation_list,
            'template_id': ObjectId(template_id),
        })
        # Fetch all available users in invitationList
        query = db.users.aggregate([
            {
                '$match': {
                    'email': {
                        '$in': invitation_list
                    }
                }
            },
            {
                '$group': {
                    '_id': None,
                    'invitation_list': {
                        '$push': '$_id'
                    }
                }
            },
            {
                '$project': {
                    'id': True,
                    'invitation_list': True
                }
            }, ])

        invitation_list = [data for data in query]

        invitation_list = [] if not invitation_list else invitation_list[0]['invitation_list']
        # Push new groupwork to creator active_group
        db.users.update_one({'email': current_user}, {
                            '$push': {'active_group': _id.inserted_id}}, upsert=True)
        # Update the group invitation list
        db.inbox.update_many(
            {
                'user_id': {'$in': invitation_list}
            },
            {
                '$addToSet': {
                    'active_group_invitation': {
                        'inviter': current_user,
                        'group_id': _id.inserted_id,
                        'answer': None,
                    }
                }
            },
        )
        # Update groupwork members
        # role = 0 : admin
        member = {
            'email': current_user,
            'role': 0
        }
        

        db.groupworks.update_one({'_id': _id.inserted_id}, {
                                 '$push': {'members': member}})

        db.timelines.insert_one(
            {
                '_id':ObjectId(),
                'group_id':_id,
                'contributions':[]
            }
        )

        #if template_id is not null, generate assignment and tasks
        '''
            TODO: better implementation?
            this function will generate assignment and tasks based on tempalte_id 
        '''
        template_id = "5ddd52b37fb2c11b69c905c0"
        if template_id is not None:
            print("test")
            template = db.courses.aggregate([
                {
                    '$match':{
                        'code':course,
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
            template = list(template)[0]['template']
            for assignment in template['assignments']:
                assignment_id = ObjectId()
                db.groupworks.update_one({
                    '_id':_id,
                },{
                    '$addToSet':{
                        'assignments':{
                            '_id': assignment_id,
                            'title': assignment['title'],
                            'description': assignment['description'],
                            'leader': '',
                            'total_marks': assignment['total_marks'],
                            'created_date': datetime.datetime.now(),
                            'due_date': assignment['due_date'],
                            'status': 1
                        }
                    }
                })
                tasks = list()
                for task in assignment['tasks']:
                    tasks.append({
                        "_id":ObjectId(),
                        "creator":"by template",
                        "assign_to":"",
                        "task":task['title'],
                        "description":task['description'],
                        "created_date":datetime.datetime.now(),
                        "assign_date":"",
                        "due_date":"",
                        "last_update":datetime.datetime.now(),
                        "priority":0,
                        "status":3,
                        "seq": countTaskSeq()
                    })

                


        return Response(
            status=200
        )


class ActiveGroupWorkDetails(Resource):
    def put(self):
        #current_user = get_jwt_identity()
        active_group_list = request.json['active_group']
        active_group_list = [ObjectId(data['$oid'])
                             for data in active_group_list]
        data = db.groupworks.find({'_id': {'$in': active_group_list}})

        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )


class Stash(Resource):
    def put(self):
        group_id = ObjectId(request.json['group_id'])
        stash = db.groupworks.find({'_id': group_id}, {'stash': 1})
        return Response(
            json_util.dumps(stash),
            mimetype='application/json'
        )


class Members(Resource):
    def get(self, group_id):
        members = db.groupworks.aggregate([
            {'$match': {'_id': ObjectId(group_id)}},
            {'$unwind': '$members'},
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'members.email',
                    'foreignField': 'email',
                    'as': 'users'
                }
            },

            {'$unwind': '$users'},
            {
                '$project': {
                    '_id': '$users._id',
                    'email': '$users.email',
                    'fname': '$users.profile.fname',
                    'lname': '$users.profile.lname',
                    'contactNo': '$users.profile.contactNo',
                    'programmeCode': '$users.profile.programmeCode',
                    'role': '$members.role'


                }
            }
        ])
        return Response(
            json_util.dumps(members),
            mimetype='application/json'
        )

    def put(self, group_id):
        email = request.json['email']
        db.groupworks.update_one(
            {'_id': ObjectId(group_id), },
            {'$pull': {
                'members': {
                    'email': email
                }
            }}
        )
        # Remove from users active group
        db.users.update_one(
            {'email': email},
            {'$pull': {
                'active_group': ObjectId(group_id)
            }}
        )
        return Response(
            {
                json_util.dumps({'messages': {'Sucessfully Delete'}})
            },
            mimetype='application/json'
        )

    @jwt_required
    def post(self, group_id):
        # TODO Optimize Queries
        current_user = get_jwt_identity()
        email = request.json['email']
        if db.groupworks.find({
            '$or': [
                {'$and': [
                    {'_id': ObjectId(group_id)},
                    {'invitation_list': email}
                ]},
                {'$and': [
                    {'_id': ObjectId(group_id)},
                    {'members.email': email}
                ]}
            ]
        }).count() == 0:
            db.groupworks.update_one({
                '_id': ObjectId(group_id),
            },
                {'$addToSet': {
                    'invitation_list': email,
                }}
            )

            _id = db.users.find_one({
                'email': email
            }, {
                '_id': True
            })

            db.inbox.update_one(
                {'user_id': _id['_id']},
                {
                    '$push': {
                        'active_group_invitation': {
                            'inviter': current_user,
                            'group_id': ObjectId(group_id),
                            'answer': None,
                        }
                    }
                }
            )
        else:
            abort(400, message='User currently a member or in invitation List')


class Roles(Resource):
    def get(self, group_id):
        pass

    @jwt_required
    def put(self, group_id):

        member_email = request.json['email']
        role = request.json['role']

        db.groupworks.update_one(
            {'$and': [
                {'_id': ObjectId(group_id)},
                {'members.email': member_email}
            ]},
            {'$set': {
                'members.$.role': role

            }}
        )


class Requests(Resource):
    def get(self, group_id):

        data = db.groupworks.find_one(
            {'_id': ObjectId(group_id)},
            {'requests': True, '_id': False}
        )

        return Response(
            json_util.dumps(data),
            mimetype="application/json",
        )

    def put(self, group_id):

        email = request.json['email']
        answer = request.json['answer']

        if answer is True:
            db.groupworks.bulk_write([
                UpdateOne(
                    {'_id': ObjectId(group_id)},
                    {'$pull': {
                        'requests': {
                            'email': email
                        }
                    }
                    }),
                UpdateOne(
                    {'_id': ObjectId(group_id)},
                    {'$addToSet': {
                        'members': {
                            'email': email,
                            'role': 1,
                        }
                    }}
                )
            ])

            db.users.update_one({
                'email': email,
            }, {
                '$addToSet': {
                    'active_group': ObjectId(group_id)
                }
            })

            user_id = db.users.find_one({
                'email': email
            }, {
                '_id': True,
            })

            db.inbox.update_one({
                'user_id': user_id['_id'],

            }, {
                '$pull': {
                    'active_group_requests': {
                        'group_id': group_id,
                    }
                }
            })
