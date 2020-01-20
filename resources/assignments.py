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
    return counter['seq']


class Assignments(Resource):
    @jwt_required
    def get(self, group_id):
        current_user = get_jwt_identity()
        
        data = db.groupworks.find_one(
            {
                '_id': ObjectId(group_id)
            },
            {
                '_id': False,
                'assignments': True,
            }
        )
        return Response(
            json_util.dumps(data['assignments']),
            mimetype='application/json'
        )
        

    def post(self, group_id):
        try:
            _id = ObjectId()
            assignment = request.json
            db.groupworks.update_one(
                {'_id': ObjectId(group_id)},
                {'$push': {
                    'assignments': {
                        '_id': _id,
                        'title': assignment['title'],
                        'description': assignment['description'],
                        'leader': assignment['leader'],
                        'total_marks': assignment['total_marks'],
                        'created_date': assignment['created_date'],
                        'due_date': assignment['due_date'],
                        'status':assignment['status'],
                        'accepted_date':None,

                    }
                }},
                upsert=True
            )
            #Initial Task Collection
            db.tasks.insert_one(
                {'group_id': ObjectId(group_id), 'assignment_id': _id})

            members = db.groupworks.find_one(
                {'_id':ObjectId(group_id)},
                {'_id':False,'members':True}
            )
            reviews = []
            for member in members['members']:
                reviews.append({
                    'reviewer':member['email'],
                    'reviewed':[

                    ]
                })
            
            

            #Initial PeersReview Collection
            db.peer_review.insert_one(
                {
                    '_id':ObjectId(),
                    'assignment_id':_id,
                    'reviews':reviews
                }
            )
        except:
            abort(400,message='Some problem occur. please try again')

        return {"message": "Assignment Created"}, 200


       

    def put(self,group_id):
        data = request.json
        data['_id'] = ObjectId(data['_id'])
        db.groupworks.update_one({
            '_id':ObjectId(group_id),
            'assignments._id':data['_id']
        },{
            '$set': {
                "assignments.$.title": data['title'],
                "assignments.$.description": data['description'],
                "assignments.$.leader": data['leader'],
                "assignments.$.total_marks": data['total_marks'],
                "assignments.$.start_date": data['start_date'],
                "assignments.$.due_date": data['due_date'],
                "assignments.$.status": data['status'],
                "assignments.$.approval": data['approval']
            }
        })

#Read All assignments in a groupwork and all user points
class AssignmentsUserPoint(Resource):
    def get(self, group_id):
        pass


class Assignment(Resource):

    def get(self, assignment_id):

        data = db.assignments.find_one(
            {'_id': ObjectId(assignment_id)},
        )

        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )

    def put(self):
        #current_user = get_jwt_identity()
        group_id = request.json['group_id']
        assignment_id = request.json['assignment_id']

        data = db.assignments.aggregate(
            [
                {'$match': {
                    '$and': [
                        {'group_id': ObjectId(group_id)},
                        {'assignments._id': ObjectId(assignment_id)}
                    ],
                }, },
                {
                    '$project': {

                        'assignment': {
                            '$filter': {
                                'input': '$assignments',
                                'as': 'assignment',
                                'cond': {'$eq': ['$$assignment._id', ObjectId(assignment_id)]}
                            }
                        }
                    }
                },
                {'$unwind': '$assignment'},
                {'$replaceRoot': {'newRoot': '$assignment'}}


            ],

        )

        json = json_util.dumps(data)

        return Response(
            json,
            mimetype='application/json'
        )


class AssignmentDelete(Resource):
    def put(self, group_id):
        assingment_id = request.json['assignment_id']
        db.groupworks.update_one(
            {'_id': ObjectId(group_id)},
            {'$pull': {
                'assignments': {
                    '_id': ObjectId(assingment_id)
                }
            }}
        )

        db.peer_review.delete_one(
            {'assignment_id':ObjectId(assingment_id)}
        )

class AssignmentStatus(Resource):
    @jwt_required
    def put(self,group_id):
        current_user = get_jwt_identity()
        status = request.json['status']
        assignment_id = request.json['assignment_id']
        assignment_link = request.json['assignment_link']
        db.groupworks.update_one(
            {
                '_id':ObjectId(group_id),
                'assignments._id':ObjectId(assignment_id),
            },
            {
                '$set':{
                    'assignments.$.status':status,
                    'assignments.$.assignment_link':assignment_link,
                    'assignments.$.submitted_date':datetimestring
                }
            },upsert=True
        )

        supervisor = db.groupworks.find_one(
            {'_id':ObjectId(group_id)},
            {'_id':False,'supervisor':True}
        )

        db.notify.update_one({
            'email':supervisor['supervisor']
        },{
            '$addToSet':{
                'supervisor_notify': {
                    '_id':ObjectId(),
                    'title':'Assignment Submitted!',
                    'body':'A student submit your assignment at'+datetimestring,
                    'notified':False,
                }
            }
        },upsert=True)
        
        

class Tasks(Resource):
    @jwt_required
    def get(self, assignment_id):
        tasks = db.tasks.find_one(
            {'assignment_id': ObjectId(assignment_id)},
            {'_id': False, 'tasks': True}
        )

        if 'tasks' in tasks:
            return Response(
                json_util.dumps(tasks['tasks']),
                mimetype='application/json'
            )
        else:
            return Response(
                json_util.dumps([]),
                mimetype='application/json'
            )

    @jwt_required
    def post(self, assignment_id):
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

        task = request.json
        task['_id'] = ObjectId()
        task['accepted_date'] = None
        task['seq'] = countTaskSeq()
        db.tasks.update_one(
            {
                'assignment_id': ObjectId(assignment_id),
            },
            {
                '$addToSet': {'tasks': task}

            }, upsert=True)

        return Response(
            json_util.dumps({
                'message': 'message'
            }),
            mimetype='application/json'
        )


class Task(Resource):
    def put(self, assignment_id, task_id):

        task = request.json

        db.tasks.update_one(
            {
                'assignment_id': ObjectId(assignment_id),
                'tasks._id': ObjectId(task_id)
            },
            {
                '$set': {
                    'tasks.$': {
                        '_id': ObjectId(task['_id']),
                        'creator': task['creator'],
                        'assign_to': task['assign_to'],
                        'task': task['task'],
                        'description': task['description'],
                        'created_date': task['created_date'],
                        'due_date': task['due_date'],
                        'assign_date': task['assign_date'],
                        'last_updated': task['last_updated'],
                        'priority': task['priority'],
                        'status': task['status'],
                        'seq': task['seq']
                    }
                }
            })

    def delete(self, assignment_id, task_id):
        try:
            db.tasks.update_one({
                'assignment_id': ObjectId(assignment_id),

            },
                {
                '$pull': {
                    'tasks': {
                        '_id': ObjectId(task_id)
                    }
                }
            })
        except:
            abort(400, message="Cannot Delete")

        return Response(

        )

# Used to update task status , delete from old array and push to new

class TaskItems(Resource):
    def get(self,assignment_id,task_id):
        data = db.tasks.find_one({
            'assignment_id':ObjectId(assignment_id),
            'tasks._id':ObjectId(task_id)
        },{
            '_id':False,
            'tasks.$.items':True
        })
        if 'items' in data['tasks'][0]:
            return Response(
                json_util.dumps(data['tasks'][0]['items']),
                mimetype='application/jon'
            )
        else:
            return []

    def post(self,assignment_id,task_id):
        data = request.json
        data['_id'] = ObjectId()
        db.tasks.update_one({
            'assignment_id':ObjectId(assignment_id),
            'tasks._id':ObjectId(task_id)
        },{
            '$addToSet':{
                'tasks.$.items':data,
            }
        },upsert=True)

class TaskReviews(Resource):
    def get(self,assignment_id,task_id):
        data = db.tasks.find_one({
            'assignment_id':ObjectId(assignment_id),
            'tasks._id':ObjectId(task_id)
        },{
            '_id':False,
            'tasks.$':True
        })
        if 'reviews' in data['tasks'][0]:
            return Response(
                json_util.dumps(data['tasks'][0]['reviews']),
                mimetype='application/json'
            )
        else:
            return []

    def post(self,assignment_id,task_id):
        data = request.json
        data['_id'] = ObjectId()
        db.tasks.update_one({
            'assignment_id':ObjectId(assignment_id),
            'tasks._id':ObjectId(task_id)
        },{
            '$addToSet':{
                'tasks.$.reviews':data,
            }
        },upsert=True)

        return {'message':'suggestion submitted'}


class TaskReviewsApproval(Resource):
    def put(self,assignment_id,task_id):
        data = request.json
        index = db.tasks.aggregate([
            {
            '$match': {
                'assignment_id': ObjectId(assignment_id)
            }
        }, 
        {
            '$project': {
                'index': {
                    '$indexOfArray': ['$tasks._id',ObjectId(task_id)]
                }
            }
        }])
        index = (list(index))[0]
        db.tasks.update_one({
            'assignment_id':ObjectId(assignment_id),
            'tasks.'+str(index['index'])+'.reviews._id':ObjectId(data['_id'])
        },{
            '$set':{
                'tasks.'+str(index['index'])+'.reviews.$.approval': data['approval']
            }
        })

class TaskSubmittedDate(Resource):
    def put(self,assignment_id,task_id):
        datetimestring = str(datetime.datetime.now())
        data = request.json
        db.tasks.update_one({
            'assignment_id':ObjectId(assignment_id),
            'tasks._id':ObjectId(task_id)
        },{
            '$set':{
                'tasks.$.accepted_date': datetimestring,
                'tasks.$.status':3,
            }
        },upsert=True)


class TaskStatus(Resource):
    def put(self, assignment_id):
        tasks = request.json['tasks']
        for task in tasks:
            db.tasks.update_one(
                {

                    'assignment_id': ObjectId(assignment_id),
                    'tasks._id': ObjectId(task['id'])

                },
                {
                    '$set': {
                        'tasks.$.status': task['status']
                    }
                },
            )


class TaskAssignTo(Resource): 
    def get(self,assignment_id):

        #TODO : will use aggreate but not now
        requests = db.tasks.find_one(
            {'assignment_id':ObjectId(assignment_id)},
            {
                '_id':False,'requests':True
            }
        )

        if 'requests' not in requests:
            return []

        requests = requests['requests']
        requests_tasks = list()

        for request in requests:
            requests_tasks.append(request['task_id'])

        #TODO HOW THE F
        tasks = list()
        for request in requests_tasks:
            tasks.append(
                db.tasks.find_one(
                    {
                        'assignment_id':ObjectId(assignment_id),
                        'tasks._id':request,},
                    {
                        '_id':False,'tasks.$':True,
                    })['tasks'][0]
            )

        #TODO : dumb dumb buat worked
        i = 0
        if tasks is not None:

            for request in requests:
                request['task'] = tasks[i]
                i = i+1
            return Response(
                json_util.dumps(requests),
                mimetype='application/json'
            )
        return []


    #User request to change ownership
    @jwt_required
    def post(self,assignment_id):
        _id = ObjectId()
        current_user = get_jwt_identity()
        task = request.json
        task['_id'] = _id
        task['requester'] = current_user
        task['task_id'] = ObjectId(task['task_id'])
        db.tasks.update_one(
            {'assignment_id':ObjectId(assignment_id)},
            {
                '$addToSet':{
                    'requests': task
                }
            }
        )

    @jwt_required
    def put(self,assignment_id):
        req = request.json
        
        db.tasks.update_one(
            {
                'assignment_id':ObjectId(assignment_id),
                'tasks._id':ObjectId(req['task_id'])
            },
            {
                '$set':{
                    'tasks.$.assign_to':req['requester'],
                    'tasks.$.due_date':req['due_date']
                }
            }
        )
        
        db.tasks.update_one(
            {
                'assignment_id':ObjectId(assignment_id),
                'requests._id':ObjectId(req['_id']),
            },
            {
                '$set':{
                    'requests.$.approval':req['approval'],
                   
                }
            }
        )

class PeerReview(Resource):
    @jwt_required
    def get(self, assignment_id):
        current_user = get_jwt_identity()
        '''data = db.peer_review.find_one(
            {'assignment_id':ObjectId(assignment_id),'reviews.reviewer': current_user},
            {'_id':False,'reviews.$':True}
        )
        if data is not None:
            return Response(
                json_util.dumps(data['reviews'][0]),
                mimetype='application/json'
            )
        else:
            return Response(
                json_util.dumps({'reviewer':current_user,'reviewed':[]}),
                mimetype='application/json'
            )'''

        return []
        
    @jwt_required
    def post(self, assignment_id):
        current_user = get_jwt_identity()
        answer = request.json
        for i in answer['answers']:
            i['question_id'] = ObjectId(i['question_id'])

        if db.peer_review.find(
            {
                '$and':[
                    {'assignment_id':ObjectId(assignment_id),},
                    {'reviews.reviewee':answer['reviewee']},
                    {'reviews.reviewer':current_user}
                ]
            }
        ).count()== 0:
            db.peer_review.update_one(
                {'assignment_id': ObjectId(assignment_id)},
                {'$addToSet': {
                    'reviews': answer
                }}, upsert=True,
            )
        else:
            print("already reviewd")
        

        db.peer_review.update_one(
            {'assignment_id':ObjectId(assignment_id)},
            {'$addToSet':{
                'reviews':answer
            }}
        )


class PeerReviewScoreAssignment(Resource):
    @jwt_required
    def get(self,assignment_id):
        current_user = get_jwt_identity()
        data = db.peer_review.aggregate(
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

        data = list(data)

        total_marks = {}
        total_marks['counts'] = 0
        for reviews in data[0]['reviews']:
            total_marks['counts'] = total_marks['counts']+1
            for answer in reviews['answers']:
                if str(answer['question_id']) in total_marks:
                    total_marks[str(answer['question_id'])] = total_marks[str(answer['question_id'])] + (answer['answer_index']+1)
                else:
                    total_marks[str(answer['question_id'])] = (answer['answer_index']+1)

        return Response(
            json_util.dumps(total_marks),
            mimetype='application/json'
        )


