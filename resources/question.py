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
from main import db , app ,mongodb_connect
from bson.json_util import dumps, ObjectId

INIT_QUESTIONS = [
    {
        '_id':ObjectId(),
        'question':'Participation',
        'answers':[
            {
                '_id':ObjectId(),
                'answer': "Group member did not participate, wasted time, or worked on unrelated material"
            },
            {
                '_id':ObjectId(),
                'answer': "Group member participated but wasted time regularly or was rarely on task"
            },
            {
                '_id':ObjectId(),
                'answer': "Group member participated most of the time and was on task most of the time"
            },
            {
                '_id':ObjectId(),
                'answer': "Group member participated fully and was always on task in class"

            }
        ]
     },
       {
        '_id':ObjectId(),
        'question':'Leadership',
        'answers':[
            {
                '_id':ObjectId(),
                'answer': "Group member did not assume leadership or assumed it in a nonproductive manner"
            },
            {
                '_id':ObjectId(),
                'answer': "Group member usually allowed others to assume leadership, alternatively, or often dominated the group"
            },
            {
                '_id':ObjectId(),
                'answer': "Group member sometimes assumed leadership in an appropriate way."
            },
            {
                '_id':ObjectId(),
                'answer': "Group member assumed leadership in an appropriate way when necessary by helping the group stay on track, encouraging group participation, posing solutions to problems, and having a positive attitude."

            }
        ]
     },
       {
        '_id':ObjectId(),
        'question':'Listening',
        'answers':[
            {
                '_id':ObjectId(),
                'answer': "Group member did not listen to others and often interrupted them"
            },
            {
                '_id':ObjectId(),
                'answer': "Group member sometimes did not listen to others’ ideas"
            },
            {
                '_id':ObjectId(),
                'answer': "Group member usually listened to others’ ideas"
            },
            {
                '_id':ObjectId(),
                'answer': "Group member listened carefully to others’ ideas"

            }
        ]
        },
       {
        '_id':ObjectId(),
        'question':'Feedback',
        'answers':[
            {
                '_id':ObjectId(),
                'answer': "Group member did not offer constructive or useful feedback"
            },
            {
                '_id':ObjectId(),
                'answer': "Group member occasionally offered constructive feedback, but sometimes the comments were inappropriate or not useful"
            },
            {
                '_id':ObjectId(),
                'answer': "Group member offered constructive feedback when appropriate."
            },
            {
                '_id':ObjectId(),
                'answer': "Group member offered detailed, constructive feedback when appropriate"
            }
        ]
    },
    {
    '_id':ObjectId(),
    'question':'Cooperation',
    'answers':[
        {
            '_id':ObjectId(),
            'answer': "Group member often treated others disrespectfully or did not share the workload fairly"
        },
        {
            '_id':ObjectId(),
            'answer': "Group member sometimes treated others disrespectfully or did not share the workload fairly"
        },
        {
            '_id':ObjectId(),
            'answer': "Group member usually treated others respectfully and shared the workload fairly"
        },
        {
            '_id':ObjectId(),
            'answer': "Group member treated others respectfully and shared the workload fairly"

        }
    ]
    },
    {
    '_id':ObjectId(),
    'question':'Time Management',
    'answers':[
        {
            '_id':ObjectId(),
            'answer': "Group member did not complete most of the assigned tasks on time and often forced the group to make last-minute adjustments and changes to accommodate missing work."
        },
        {
            '_id':ObjectId(),
            'answer': "Group member often did not complete assigned tasks on time, and held up completion of project work."
        },
        {
            '_id':ObjectId(),
            'answer': "Group member usually completed assigned tasks on time and did not hold up progress on the projects because of incomplete work"
        },
        {
            '_id':ObjectId(),
            'answer': "Group member completed assigned tasks on time."

        }
    ]
},
       
]

    

class InitQuestions(Resource):
    def get(self):
        mongodb_connect().questions.insert_many(INIT_QUESTIONS)

class Questions(Resource):
    def get(self):
        question = db.questions.find()
        print(question)
        return Response(
            json_util.dumps(question),
            mimetype='application/json'
        )

    def post(self):
        pass
        

