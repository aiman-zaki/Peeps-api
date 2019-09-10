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
from PIL import Image
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

    return '.' in filename and \
        filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS 

def fileExtension(filename):
    return filename.rsplit('.',1)[1].lower()

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
                imageFile = imageFile.convert('RGB') 
            imageFile.save(os.path.join(path,"profile.jpg"))
            return {"message":"Profile Picture Updated"},200
        return {"message":"Oops something is wrong"}
     
    def get(self):
        pass

class GroupWork(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        data = db.users.find_one(
            {'email': current_user},{'_id':0,'active_group':1}
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
    def post(self):
        current_user = get_jwt_identity()
        name = request.json['name']
        description = request.json['description']
        course = request.json['course']
        invitation_list = [] if request.json['members'] == None else request.json['members']
        try:
            _id = db.groupworks.insert_one({
            'creator':current_user,
            'name':name,
            'description':description,
            'course':course,
            'invitation_list':invitation_list
            })
            #Push new groupwork to user active_group
            db.users.update_one({'email':current_user},{'$push':{'active_group':_id.inserted_id}},upsert=True)
            #Update the group invitation list
            db.users.update_many({'email': {'$in': invitation_list}}, {'$push': {'inbox.group_invitation': {'inviter':current_user,'group_id':_id.inserted_id,'accept':False}}},upsert=True)
            #Update groupwork members 
            db.groupworks.update_one({'_id':_id.inserted_id},{'$push':{'members':current_user}})
            #Iniital Assignment Collection
            db.assignments.insert({'group_id':_id.inserted_id})
        except:
            abort(400,message='Something went wrong')
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
            {
                '$lookup':{
                    'from':'users',
                    'localField': 'members',
                    'foreignField': 'email',
                    'as':'users'
                }
            },
            {'$unwind':'$users'},
            {
                '$project':{
                    '_id':0,
                    'email':'$users.email',
                    'fname':'$users.profile.fname',
                    'lname':'$users.profile.lname',
                    'contactNo':'$users.profile.contactNo',
                    'programmeCode':'$users.profile.programmeCode'

                }
            }
        ])



  
        return Response(
            json_util.dumps(members),
            mimetype='application/json'
        )


