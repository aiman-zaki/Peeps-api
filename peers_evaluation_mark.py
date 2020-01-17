"""
    PEERS EVALUATION MARK SCHEME
"""
from pymongo import MongoClient, ReturnDocument, InsertOne, DeleteMany, ReplaceOne, UpdateOne
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, decode_token, create_refresh_token, jwt_refresh_token_required,
    set_access_cookies, set_refresh_cookies
)
import re
import datetime
import os
 
from flask import request, jsonify, json, Response
from flask_cors import CORS
from flask_restful import Resource, Api, abort,  reqparse
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from bson import json_util
from main import db, app
from bson.json_util import dumps, ObjectId
from datetime import datetime

current_user = "aiman@gmail.com"
group_id = "5e1dc91a3cabb4a2982967f3"
assignment_id = "5e1e6d5c632a8069b727784c"

def convert(datetime_str):
    datetime_str = datetime_str.split('.')[0]
    datetime_object = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    return datetime_object

"""
    ASSIGNMENT's LEADERSHIP PEERS MARKING SCHEME
    [STUFF][M]
    [create new task][+1]
    [reviewing user task][+1]
    [deny user done request with appropriate reasons[users will determine eith appropriate or not]][+2]
    [deny user done request without reasons][-1]
    [distribute task equally within team member][+2]
    [distribute task uneqully within team member][-2]
    [assignment done within duedate with lecturer confirmation][+5]
    [assignment done pass duedate][-5]
"""

def create_action(data):
    return 5

def receive_action(data):
    return 4

def update_action(data):
    return 3

def delete_action(data):
    return 1

def request_action(data):
    return 2

def accept_action(data):
    return 1

def deny_action(data):
    return 5


def calculate_assignment_leader_mark(current_user,group_id,assignment_id):
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

    #looop loop like dumb dumb

    score = 0.00

    for contribution in data['contribution']:
        if(contribution['what'] ==  0):
            score = score + create_action(contribution['what'])
        elif(contribution['what'] ==  1):
            score = score + receive_action(contribution['what'])
        elif(contribution['what'] ==  2):
            score = score + update_action(contribution['what'])
        elif(contribution['what'] ==  3):
            score = score + delete_action(contribution['what'])
        elif(contribution['what'] ==  4):
            score = score + request_action(contribution['what'])
        elif(contribution['what'] ==  5):
            score = score + accept_action(contribution['what'])
        elif(contribution['what'] ==  6):
            score = score + deny_action(contribution['what'])
            
    

    return {'score':score}

print(json_util.dumps(calculate_assignment_leader_mark(current_user,group_id,assignment_id)))

"""
    USERS PEERS MARKING SCHEME
    [STUFF][M]
    [from do to ongoing][+1]
    [from ongoing to do][-1]
    [assist other task][+1]
    [task assigned][+1 * task weightage]
    [done task within duedate with approval by leader][+2]
    [done task pass duedate][-2 * task weightage]
"""
