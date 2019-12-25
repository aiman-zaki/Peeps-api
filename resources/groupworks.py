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

datetimestring = str(datetime.datetime.now())

def count_task_seq():
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
    return counter['seq']

def post_task_init(groupwork_id,assignment_id):

    members = db.groupworks.find_one(
        {'_id':groupwork_id},
        {'_id':False,'members':True}
    )
    reviews = []
    points = []
    for member in members['members']:
        reviews.append({
            'reviewer':member['email'],
            'reviewed':[

            ]
        })
        points.append({
            'member':member['email'],
            'points':50
        })
    

    #Initial PeersReview Collection
    db.peer_review.insert_one(
        {
            '_id':ObjectId(),
            'assignment_id':assignment_id,
            'points':points,
            'reviews':reviews
        }
    )

    #Initial Timeline
    db.timelines.update_one(
        {
            'group_id':groupwork_id,
        },{
            '$addToSet':{
                'contributions':{
                    'assignment_id':assignment_id
                }
            }
        },upsert=True
    )


def get_template(course,template_id):
    data = db.courses.aggregate([
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
                                {'$eq':['$$template._id',template_id],},
                                
                            ]    
                        }
                    }
                }
            }
        }
    ])

    return data

def generate_assignments_template(group_id,assignment_id,assignment_template):
    db.groupworks.update_one({
        '_id':group_id,
    },{
        '$addToSet':{
            'assignments':{
                '_id': assignment_id,
                'template_id':assignment_template['_id'],
                'title': assignment_template['title'],
                'description': assignment_template['description'],
                'leader': None,
                'total_marks': assignment_template['total_marks'],
                'created_date': datetimestring,
                'start_date':assignment_template['start_date'],
                'due_date': assignment_template['due_date'],
                'status': 1,
                'approval':2,
            }
        }
    })

def generate_tasks_template(group_id,assignment_id,tasks_template):
    tasks = list()
    for task in tasks_template:
        tasks.append({
            "_id":ObjectId(),
            "creator":"by template",
            "assign_to":"",
            "task":task['title'],
            "description":task['description'],
            "created_date":datetimestring,
            "assign_date":None,
            "due_date":None,
            "last_update":datetimestring,
            "priority":0,
            "status":0,
            "seq": count_task_seq(),
            "template_id":task['_id']
        })
    
    db.tasks.insert_one(
        {
            'group_id':group_id,
            'assignment_id':assignment_id,
            'tasks':tasks,
        }
    )

    


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def fileExtension(filename):
    return filename.rsplit('.', 1)[1].lower()


class GroupworksSearch(Resource):
    def put(self):
        search = request.json
        print(request.json)
        data = db.groupworks.find(
            {
                'course': {'$regex': search}
            },
        )
        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )


class Groupworks(Resource):
    def get(self):
        pass

    @jwt_required
    def post(self):
        _id = ObjectId()
        current_user = get_jwt_identity()
        groupwork = request.json
        groupwork['_id'] = _id
        groupwork['creator'] = current_user
        groupwork['assignments'] = []
        if groupwork['template_id'] is not None:
            try:
                groupwork['template_id'] = ObjectId(groupwork['template_id'])
            except:
                abort(400,message = 'Template not follow format')

        invitation_list = groupwork['invitation_list']
        db.groupworks.insert_one(document=groupwork)
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
                            '$push': {'active_group': _id}}, upsert=True)
        # Update the group invitation list
        db.inbox.update_many(
            {
                'user_id': {'$in': invitation_list}
            },
            {
                '$addToSet': {
                    'active_group_invitation': {
                        'inviter': current_user,
                        'group_id': _id,
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

        db.groupworks.update_one({'_id': _id}, {
                                 '$push': {'members': member}})
        # Iniital Assignment Collection
        db.timelines.insert_one(
            {'_id':ObjectId(),
            'group_id':_id,
            'contributions':[]
            }
        )

        #if template_id is not null, generate assignment and tasks
        '''
            TODO: better implementation?
            this function will generate assignment and tasks based on tempalte_id 
        '''

        if groupwork['template_id'] is not None:
            
            template = get_template(groupwork['course'],groupwork['template_id'])
            template = list(template)
            template = template[0]['template']
            for assignment in template[0]['assignments']:
                assignment_id = ObjectId()
                generate_assignments_template(_id,assignment_id,assignment)
                generate_tasks_template(_id,assignment_id,assignment['tasks'])
                post_task_init(_id,assignment_id)
                

def checkTemplateRevision(groupwork):
    data = db.courses.aggregate([
        {
            '$match':{
                'code':groupwork['course'],
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
                                {'$eq':['$$template._id',groupwork['template_id']],},
                                
                            ]    
                        }
                    }
                }
            }
        }
    ])
    template = list(data)[0]['template'][0]
    if template['revision'] != groupwork['revision']:
        #update assignment first
        for assignment in template['assignments']:
            #check if assignment exists

            assignment_id = db.groupworks.find_one_and_update({
                '_id':groupwork['_id'],
                'assignments.template_id':assignment['_id']
            },{
                '$set':{
                    'assignments.$.title':assignment['title'],
                    'assignments.$.description':assignment['description'],
                    'assignments.$.total_marks':assignment['total_marks'],
                    'assignments.$.start_date':assignment['start_date'],
                    'assignments.$.due_date':assignment['due_date'],
                    
                }
            },{
                '_id':False,
                'assignments.$':True
            })
            """
            If Supervisor add new assignment in the template, automtic create new
            """

            if assignment_id is None:
                assignment_id = ObjectId()
                generate_assignments_template(groupwork['_id'],assignment_id,assignment)
                generate_tasks_template(groupwork['_id'],assignment_id,assignment['tasks'])
                post_task_init(groupwork['_id'],assignment_id)
            
            else:
                assignment_id = (assignment_id['assignments'][0]['_id'])
                for task in assignment['tasks']:
                    db.tasks.update_one({
                        'group_id':groupwork['_id'],
                        'assignment_id':ObjectId(assignment_id),
                        'tasks.template_id':task['_id']
                    },{
                        '$set':{
                            'tasks.$.task':task['title'],
                            'tasks.$.description':task['description'],
                            'tasks.$.difficulty':task['difficulty'],
                        }
                    })
                db.groupworks.update_one({
                    '_id':groupwork['_id'],
                },{
                    '$set':{
                        'revision':template['revision'],
                    }
                })
    else:
        print(False)

    

class Groupwork(Resource):
    def get(self, group_id):
        '''
        check if template revision is matching
        '''
        group = db.groupworks.find_one(
            {'_id': ObjectId(group_id)}
        )
        return Response(
            json_util.dumps(group)
        )

    @jwt_required
    def put(self, group_id):
        current_user = get_jwt_identity()
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


class GroupworkTemplateRevision(Resource):
    def post(self,group_id):
        group = db.groupworks.find_one(
            {'_id': ObjectId(group_id)
        })
        checkTemplateRevision(group)
        return {'message':"update sucessfully"}
class GroupworkProfileImage(Resource):

    def post(self, group_id):
        parse = reqparse.RequestParser()
        parse.add_argument('image', type=FileStorage, location='files')
        args = parse.parse_args()
        imageFile = (args['image'])
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

class Complaints(Resource):
    def get(self,group_id):
        db.groupworks.find_one({
            '_id':ObjectId(group_id)
        },{

        })

    def post(self,group_id):
        data = request.json
        data['_id'] = ObjectId()
        data['assignment_id'] = ObjectId(data['assignment_id'])

        db.groupworks.update_one({
            '_id':ObjectId(group_id)
        },{
            '$addToSet':{
                'complaints':data
            }
        },upsert=True)

        return {'message':'Complaints Submiited'}

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

