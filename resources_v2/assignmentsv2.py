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

        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )
    

    @jwt_required
    def post(self,group_id):
        _id = ObjectId()
        current_user = get_jwt_identity()
        assignment = request.json['assignment']
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
        


class Tasks(Resource):

    @jwt_required
    def get(self, assignment_id):
        print(assignment_id)
        tasks = db.tasks.find_one(
            {'assignment_id': ObjectId(assignment_id)},
            {'_id': False, 'tasks': True}
        )

        return Response(
            json_util.dumps(tasks),
            mimetype='application/json'
        )

    @jwt_required
    def post(self, assignment_id):
    
        group_id = request.json['group_id']

        counter = db.counter.find_one_and_update(
            {'counter': 'task'},
            {
                '$inc': {
                    'seq': 1
                }
            },
            return_document=ReturnDocument.AFTER
        )
   
        task = request.json['task']
        task['_id'] = ObjectId()
        task['seq'] = counter['seq']
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
    def post(self):
        pass

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
    def put(self, assignment_id):
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
