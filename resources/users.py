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
from datetime import datetime
from .timeline import calculate_assignment_score
import PIL.Image

def convert_string_to_datetime(datetimestring):
    date_format = "%Y-%m-%d %H:%M:%S.%f"

    return datetime.strptime(datetimestring,date_format)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

    return '.' in filename and \
        filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS 

def fileExtension(filename):
    return filename.rsplit('.',1)[1].lower()

def if_admin(current_user):
    user = db.users.find_one({
        'emai':current_user,
    })
    if user['role'] == 0 :
        return True
    else:
        return False



class Users(Resource):
    @jwt_required
    def get(self): 
        data = db.users.find({},{'_id':True,'profile':True,'active_group':True,'email':True,'role':True,'created_date':True})
        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )

        
        

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
            {'email': current_user},{'_id':True,'profile':True,'active_group':True,'email':True,'role':True,'created_date':True}
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


class ActiveGroupworks(Resource):
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

        if db.groupworks.find(
            {
                '_id':ObjectId(group_id),
                'members.email':current_user    
            }
        ).count() == 0:

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



def calculatePeerReviewScore(data,current_user,assignment_id):
        score = db.peer_review.aggregate(
            [
                {
                    '$match': {
                        '$and': 
                        [
                            {'assignment_id': ObjectId(assignment_id)}
                        ],
                }, },
                {
                    '$project': {
                        'reviews': {
                            '$filter': {
                                'input': '$reviews',
                                'as': 'review',
                                'cond': {'$eq': ['$$review.reviewee', current_user]}
                            }
                        }
                    }
                },
            ],
        )
        score = list(score)
        for reviews in score[0]['reviews']:
            data['score']['counts'] = data['score']['counts']+1
            for answer in reviews['answers']:
                if str(answer['question_id']) in data['score']:
                    data['score'][str(answer['question_id'])] = data['score'][str(answer['question_id'])] + (answer['answer_index']+1)
                else:
                    data['score'][str(answer['question_id'])] = (answer['answer_index']+1)




def calculateTaskState(data,current_user,assignment_id):
    tasks = db.tasks.find_one({'assignment_id':assignment_id},{'_id':False,'tasks':True})
    task_assigned = 0
    task_submitted_before_due_date = 0
    task_subbmited_after_due_date = 0
    if len(tasks) != 0: 
        for task in tasks['tasks']:
            if task['assign_to'] == current_user:
                task_assigned = task_assigned + 1
                if 'accepted_date' in task:
                    if task['accepted_date'] is not None:
                        due_date = convert_string_to_datetime(task['due_date'])
                        accepted_date = convert_string_to_datetime( task['accepted_date'])
                        diff = due_date - accepted_date
                        if diff.days > 0:
                            task_submitted_before_due_date = task_submitted_before_due_date + 1
                        else:
                            task_subbmited_after_due_date= task_subbmited_after_due_date + 1
                
                

    data['task_assigned'] = data['task_assigned'] + task_assigned
    data['task_submitted_before_due_date'] = data['task_submitted_before_due_date'] + task_submitted_before_due_date
    data['task_subbmited_after_due_date'] = data['task_subbmited_after_due_date'] + task_subbmited_after_due_date



class GenerateAllTimeUserStats(Resource):
    @jwt_required
    def get(self):
        #TODO Desperate time come retarded solution [obviously cpu intensive]
        current_user = get_jwt_identity()
        data = {}
        data['score'] = {}
        data['score']['counts'] = 0
        data['task_assigned'] = 0
        data['task_submitted_before_due_date'] = 0
        data['task_subbmited_after_due_date'] = 0
        data['assignment_lead'] = 0
        data['accumulate_contribution_score'] = 0

        groupworks_joined = db.groupworks.find(
            {'members.email':current_user}
        )

        groupworks_joined = list(groupworks_joined)

        data['groupworks_joined'] = len(groupworks_joined)

        for groupworks in groupworks_joined:
            for assignment in groupworks['assignments']:
                calculateTaskState(data,current_user,assignment['_id'])
                calculatePeerReviewScore(data,current_user,assignment['_id'])
                data['accumulate_contribution_score'] = data['accumulate_contribution_score'] + calculate_assignment_score(current_user,groupworks['_id'],assignment['_id'])['score']
                if assignment['leader'] == current_user:
                    data['assignment_lead'] = data['assignment_lead']+1
        
        print(data)
        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )
 
        





    

class SearchUser(Resource):
    def put(self):
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


class UserAssignments(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        data = db.groupworks.aggregate([
            {'$match':{
                'members.email':current_user,
            }},
            {
                '$project':{
                    '_id':True,
                    'name':True,
                    'assignments':{
                        '$ifNull':['$assignments',[]]
                    }
                }
            }
        ])

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
                'name':True,
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
                'name':True,
                'assignments':True,
                'tasks':'$tasks.tasks',
            }},
            {'$unwind':'$tasks'},
            {'$match':{
                '$and':[
                    {'tasks.assign_to':current_user},
                    {'tasks.status':{
                        '$in':[0,1]
                    }}
                ]
            }},
            {'$group':{
                '_id':{
                    '_id':'$_id',
                    'assignment_id':'$assignments._id'
                },
                'group_name':{'$first':'$name'},
                'title':{'$first':'$assignments.title'},
                'due_date': {'$first':'$assignments.due_date'},
                'tasks':{'$push':'$tasks'}
            }},
            {'$project':{
                '_id':False,
                'group_name':'$group_name',
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

class Role(Resource):
    @jwt_required
    def put(self):
        current_user = get_jwt_identity()
        role = request.json['role']
        
        db.users.update_one(
            {'email':current_user},
            {'$set':{
                'role':role,
            }}
        )

        