from pymongo import MongoClient, ReturnDocument
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


class Assignments(Resource):
    # @jwt_required
    def get(self, group_id):
        data = db.groupworks.find_one(
            {
                '_id': ObjectId(group_id)
            },
            {
                '_id': False,
                'assignments': True,
            }
        )

        if 'assignments' not in data:
            data = {}
            data['assignments'] = []

            

        return Response(
            json_util.dumps(data['assignments']),
            mimetype='application/json'
        )

    def post(self,group_id):
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

                }
            }},
            upsert=True
        )
        db.tasks.insert_one({'assignment_id': _id})
        


class Assignment(Resource):

    def get(self,assignment_id):
        
        data = db.assignments.find_one(
            {'_id':ObjectId(assignment_id)},
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
    def put(self,group_id):
        assingment_id = request.json['assignment_id']
        db.groupworks.update_one(
            {'_id':ObjectId(group_id)},
            {'$pull':{
                'assignments':{
                    '_id':ObjectId(assingment_id)
                }
            }}
        )



class Tasks(Resource):
    @jwt_required
    def get(self, assignment_id):
        print(assignment_id)
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
        print(task)
        task['_id'] = ObjectId()
        task['seq'] = counter['seq']
        print(task)
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
    def put(self,assignment_id,task_id):
        
        task = request.json
        
        db.tasks.update_one(
        {
            'assignment_id':ObjectId(assignment_id),
            'tasks._id':ObjectId(task_id)
        },
        {
            '$set':{
                'tasks.$':{
                    '_id':ObjectId(task['_id']),
                    'creator':task['creator'],
                    'assign_to':task['assign_to'],
                    'task':task['task'],
                    'description':task['description'],
                    'created_date':task['created_date'],
                    'due_date':task['due_date'],
                    'assign_date':task['assign_date'],
                    'last_updated':task['last_updated'],
                    'priority':task['priority'],
                    'status':task['status'],
                    'seq':task['seq']
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

class TaskStatus(Resource):
    def put(self,assignment_id):
        tasks = request.json['tasks']
        for task in tasks:
            print(task)
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
