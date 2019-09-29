from pymongo import MongoClient , ReturnDocument,InsertOne, DeleteMany, ReplaceOne, UpdateOne
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity,decode_token,create_refresh_token,jwt_refresh_token_required,
    set_access_cookies,set_refresh_cookies
)
import re
import datetime
import os
import functools
import base64
from flask import request , jsonify, json , Response 
from flask_cors import CORS
from flask_restful import Resource, Api, abort ,  reqparse
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from bson import json_util
from main import db , app 
from bson.json_util import dumps, ObjectId
import PIL.Image


class GroupInvitationInbox(Resource):
    @jwt_required
    def get(self):
        #TODO : BETTER QUERY
        current_user = get_jwt_identity()
        user_id = db.users.find_one(
            {'email':current_user},
            {'_id':True}
        )

        groupInvitationList = db.inbox.aggregate([
            {'$match':
                {'user_id':user_id['_id']}
            },
            {'$unwind':'$active_group_invitation'},
            {
                '$lookup':{
                    'from': 'groupworks',
                    'localField': 'active_group_invitation.group_id',
                    'foreignField': '_id',
                    'as': 'g',

                },
                
            },
            {'$unwind':'$g'},
            {'$project':{
                'invitation':'$active_group_invitation',
                '_id':0,
                'group._id':'$g._id',
                'group.name':'$g.name',
                'group.creator':'$g.creator',
                'group.description':'$g.description',
                'group.course':'$g.course',
                'group.members':'$g.members',
                
                }},
           
        ])
        return Response(
            json_util.dumps(groupInvitationList),
            mimetype='application/json'
        )
    
class ReplyInvitationInbox(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        user_id = db.users.find_one(
            {'email':current_user},
            {'_id':True}
        )

        answer = request.json['answer']
        group_id = ObjectId(request.json['group_id'])

        filter = {'$and':[
                    {'user_id':user_id['_id']},
                    {'active_group_invitation.group_id':(group_id)}
                ]}   
        data = db.inbox.find_one_and_update(
            filter,
            {'$set':
                {'active_group_invitation.$.answer':answer}
            },
            projection={
                '_id':False,
                'active_group_invitation': {
                    '$elemMatch':{
                        'group_id':(group_id)
                    }
                }
            },
            return_document=ReturnDocument.AFTER
        )

        result = db.inbox.bulk_write([
            UpdateOne({'user_id':user_id['_id']},
                {'$pull':{
                    'active_group_invitation': {
                   
                            'group_id':(group_id)
                        
                    }
                }}
            ),
            UpdateOne({'user_id':user_id['_id']},
                {'$push':{
                    'archive_group_invitation':data['active_group_invitation'][0]
                }}
            )
        ]),

        #if true , update Users.active_group and Groupwork.members
        if answer == True:
            member = {
                'email':current_user,
                'role': 0
            }

            db.users.update_one({'_id':user_id['_id']},{'$push':{'active_group':group_id}},upsert=True)
            db.groupworks.bulk_write([
                UpdateOne({'_id':(group_id)},{'$push':{'members':member}},upsert=True),
                UpdateOne({'_id':(group_id)},{'$pull':{'invitation_list':current_user}})
            ]),
       
