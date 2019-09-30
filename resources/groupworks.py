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

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

    return '.' in filename and \
        filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS 

def fileExtension(filename):
    return filename.rsplit('.',1)[1].lower()

class TestQuery(Resource):
    def get(self):

        invitation_list = [] if request.json['members'] == None else request.json['members']

        query = db.users.aggregate([
            {
                '$match':{
                    'email': {
                        '$in':invitation_list
                    }
                }
            },
            {
                '$group':{
                    '_id': None,
                    'invitation_list':{
                        '$push':'$_id'
                    }
                }
            },
            {
                '$project':{
                    'id':True,
                    'invitation_list':True
                }
            },
           

            
        ])

        invitation_list = [data for data in query]

        print(invitation_list[0]['invitation_list'])
        

        return Response(
            json_util.dumps(invitation_list[0]),
            mimetype='application/json'
        )


class GroupworkProfileImage(Resource):
    def post(self):
        parse = reqparse.RequestParser()
        parse.add_argument('image',type=FileStorage, location='files')
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
            imageFile.save(os.path.join(path,"profile.jpg"))
            return {"message":"Profile Picture Updated"},200
        return {"message":"Oops something is wrong"}
     
    def get(self):
        pass

class Groupwork(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        data = db.users.find_one(
            {'email': current_user},{'_id':False,'active_group':True}
        )        
        groups = db.groupworks.find({'_id':{'$in': data['active_group']}})
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
                    {"message":"No Data Recorded"}
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
            {'_id':ObjectId(group_id)},
            {
                '$set':{
                    'supervisor':supervisor,
                    'description':description,
                    'course':course,
                }
            }
        )
        except:

            abort(400,message="Something Wrong")
        

        


    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        name = request.json['name']
        description = request.json['description']
        course = request.json['course']
        invitation_list = [] if request.json['members'] == None else request.json['members']
        _id = db.groupworks.insert_one({
            'creator':current_user,
            'name':name,
            'description':description,
            'course':course,
            'invitation_list':invitation_list
        })
        #Fetch all available users in invitationList
        query = db.users.aggregate([
        {
            '$match':{
                'email': {
                    '$in':invitation_list
                }
            }
        },
        {
            '$group':{
                '_id': None,
                'invitation_list':{
                    '$push':'$_id'
                }
            }
        },
        {
            '$project':{
                'id':True,
                'invitation_list':True
            }
        },])

        invitation_list = [data for data in query]
    
        invitation_list = [] if not invitation_list  else invitation_list[0]['invitation_list']
        print(invitation_list)
        #Push new groupwork to creator active_group
        db.users.update_one({'email':current_user},{'$push':{'active_group':_id.inserted_id}},upsert=True)
        #Update the group invitation list
        db.inbox.update_many(
            {
                'user_id': {'$in':invitation_list}
            },
            {
                '$push': {
                    'active_group_invitation':{
                        'inviter':current_user,
                        'group_id':_id.inserted_id,
                        'answer':None,
                    }
                }
            },
            upsert=True
        )
        #Update groupwork members 
        #role = 0 : admin
        member = {
            'email':current_user,
            'role': 0
        }

        db.groupworks.update_one({'_id':_id.inserted_id},{'$push':{'members':member}})
        #Iniital Assignment Collection
    
        return Response(
            status=200
        )
      

class ActiveGroupWorkDetails(Resource):
    def put(self):
        #current_user = get_jwt_identity()
        active_group_list = request.json['active_group']
        active_group_list = [ObjectId(data['$oid']) for data in active_group_list]
        data = db.groupworks.find({'_id':{'$in':active_group_list}})
    
        return Response(
            json_util.dumps(data),
            mimetype='application/json'
        )

class Stash(Resource):
    def put(self):
        group_id = ObjectId(request.json['group_id'])
        stash = db.groupworks.find({'_id':group_id},{'stash':1})
        return Response(
            json_util.dumps(stash),
            mimetype='application/json'
        )


class Members(Resource):
    def get(self,group_id):
        members = db.groupworks.aggregate([
            {'$match':{'_id':ObjectId(group_id)}},
            {'$unwind': '$members'},
            {
                '$lookup':{
                    'from':'users',
                    'localField': 'members.email',
                    'foreignField': 'email',
                    'as':'users'
                }
            },

            {'$unwind':'$users'},
            {
            '$project':{
                '_id': '$users._id',
                'email':'$users.email',
                'fname':'$users.profile.fname',
                'lname':'$users.profile.lname',
                'contactNo':'$users.profile.contactNo',
                'programmeCode':'$users.profile.programmeCode',
                'role':'$members.role'
                

            }
        }
        ])
        return Response(
            json_util.dumps(members),
            mimetype='application/json'
        )

    def put(self,group_id):
        email = request.json['email']
        db.groupworks.update_one(
            {'_id':ObjectId(group_id),},
            {'$pull':{
                'members': {
                    'email':email
                }
            }}
        )
        #Remove from users active group
        db.users.update_one(
            {'email':email},
            {'$pull':{
                'active_group': ObjectId(group_id)
            }}
        )
        return Response(
            {
                json_util.dumps({'messages':{'Sucessfully Delete'}})
            },
            mimetype='application/json'
        )

    @jwt_required
    def post(self,group_id):
        #TODO Optimize Queries
        current_user = get_jwt_identity()
        email = request.json['email']
        if db.groupworks.find({
            '$or':[
                {'$and':[
                    {'_id':ObjectId(group_id)},
                    {'invitation_list':email}
                ]},
                {'$and':[
                    {'_id':ObjectId(group_id)},
                    {'members.email':email}
                ]}
            ]
        }).count() == 0 :
            db.groupworks.update_one({
                    '_id':ObjectId(group_id),
                },
                {'$push':{
                    'invitation_list':email,
                }}
            )

            db.users.update_one(
                {'email':email},
                {
                    '$push': {
                        'active_group_invitation':{
                            'inviter':current_user,
                            'group_id':ObjectId(group_id),
                            'answer':None,
                        }
                    }
                }
            )
        else:
            abort(400,message='User currently a member or in invitation List')
        


class Roles(Resource):
    def get(self,group_id):
        pass

    @jwt_required
    def put(self,group_id):

        member_email = request.json['email']
        role = request.json['role']

        db.groupworks.update_one(
            {'$and':[
                {'_id':ObjectId(group_id)},
                {'members.email':member_email}
            ]},
            {'$set':{
                'members.$.role':role

            }}
        )

        

