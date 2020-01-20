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
from datetime import datetime

from bson.json_util import dumps, ObjectId
import PIL.Image

def convert_string_to_datetime(datetimestring):
    date_format = "%Y-%m-%d %H:%M:%S.%f"

    return datetime.strptime(datetimestring,date_format)

def create_action(data):
    #Material
    if data['where'] == 5:
        return 1
    
    #Suggestion
    if data['where'] == 4:
        return 1
    return 1


def receive_action(data):
    return 4

def update_action(data):
    print(data['why'])
    #task
    if data['where'] == 2:
        #do to ongoing
        if "todo" in data['why']  and "ongoing" in data['how']:
            print("oi")
            return 1
        if "ongoing" in data['why'] and "todo" in data['how']:
            return -1
        if "done" in data['how']:
            print("DONE")
            task = db.tasks.find_one({
                'assignment_id':ObjectId(data['assignment_id']),
                'tasks._id':ObjectId(data['task_id'])
            },{
                '_id':False,'tasks.$':True
            })

            if task is not None:
                #check if task is accepted by leader
                task = task['tasks'][0]
                if task['accepted_date'] is not None:

                    accepted_date = convert_string_to_datetime(task['accepted_date'])
                    due_date = convert_string_to_datetime(task['due_date'])
                    diff = due_date - accepted_date
                    if diff.days > 0:
                        return 4
                    else:
                        return 1

            print(task)




    return 0

    

def delete_action(data):
    return 0

def request_action(data):
    #task
    if data['where'] == 2:
        return 1

    return 0

def accept_action(data):
    if data['where'] == 2:
        return 1
    return 1

def deny_action(data):
    return 5

def calculate_assignment_score(current_user,group_id,assignment_id):
    data = db.timelines.aggregate([
        {
        '$match':{
            'group_id':ObjectId(group_id),
            },
        },
        {
        '$project':{
            'contribution':{
                '$filter':{
                    'input':'$contributions',
                    'as':'contribute',
                    'cond':{
                        '$and':[
                            {'$eq':['$$contribute.assignment_id',ObjectId(assignment_id)],},
                            
                        ]    
                    }
                }
            },
            '_id':False
            }
        },
        {'$project':{
            'contribution':{
                '$filter':{
                    'input':'$contribution',
                    'as':'data',
                    'cond':{
                        '$and':[
                            {'$eq':['$$data.who',current_user],},
                            
                        ]    
                    }
                }
            },
            '_id':False
            }}
        ])

    data = list(data)[0]

    score = 0.00

    for contribution in data['contribution']:
        if(contribution['what'] ==  0):
            score = score + create_action(contribution)
        elif(contribution['what'] ==  1):
            score = score + receive_action(contribution)
        elif(contribution['what'] ==  2):
            score = score + update_action(contribution)
        elif(contribution['what'] ==  3):
            score = score + delete_action(contribution)
        elif(contribution['what'] ==  4):
            score = score + request_action(contribution)
        elif(contribution['what'] ==  5):
            score = score + accept_action(contribution)
        elif(contribution['what'] ==  6):
            score = score + deny_action(contribution)
            

    return {'score':score, 'contributions': data['contribution']}



class Timeline(Resource):
    def get(self,group_id):

        data = db.timelines.find_one(
            {'group_id':ObjectId(group_id)},
            {'_id:':False,'contributions':{'$slice':-10}},
            
        )

        return Response(
            json_util.dumps(data['contributions']),
            mimetype="application/json"
        )

    def post(self,group_id):
        data = request.json
        data['assignment_id'] = ObjectId(data['assignment_id'])
        data['task_id'] = ObjectId(data['task_id'])
        data.pop('room',None)
        db.timelines.update_one(
            {'group_id':ObjectId(group_id)},
            {'$addToSet':{
                'contributions':data
            }},upsert=True
        )

class AssignmentTimeline(Resource): 
    @jwt_required
    def get(self,group_id,assignment_id):
        current_user = get_jwt_identity()
        data = db.timelines.aggregate(
        [
            {'$match': 
                {'group_id': ObjectId(group_id)},
            },
            {
                '$project': {

                    'contributions': {
                        '$filter': {
                            'input': '$contributions',
                            'as': 'contribution',
                            'cond': {'$eq': ['$$contribution.assignment_id', ObjectId(assignment_id)]}
                        }
                    }
                }
            },
            {'$unwind': '$contributions'},
            {'$replaceRoot': {'newRoot': '$contributions'}}


            ],
        )

        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )

class AssignmentUserOnyScore(Resource):
    @jwt_required
    def get(self,group_id,assignment_id):
        current_user = get_jwt_identity()
        data = calculate_assignment_score(current_user,group_id,assignment_id)
        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )

        
    
        
class TimelineCount(Resource):
    def get(self,group_id,count):
        pass



