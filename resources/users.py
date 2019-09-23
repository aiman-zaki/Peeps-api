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
import PIL.Image

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

    return '.' in filename and \
        filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS 

def fileExtension(filename):
    return filename.rsplit('.',1)[1].lower()

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
            {'email': current_user},{'_id':1,'profile':1,'active_group':1,'email':1}
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


class GroupInvitationInbox(Resource):
    @jwt_required
    def get(self):
        #TODO : BETTER QUERY
        current_user = get_jwt_identity()
        groupInvitationList = db.users.aggregate([
            {'$unwind':'$inbox.group_invitation'},
            {
                '$lookup':{
                    'from': 'groupworks',
                    'localField': 'inbox.group_invitation.group_id',
                    'foreignField': '_id',
                    'as': 'g',

                },
                
            },
            {'$unwind':'$g'},
            {
                '$match':
                    {'email':(current_user)}
            },
            {'$project':{
                'invitation':'$inbox.group_invitation',
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
        answer = request.json['answer']
        group_id = request.json['group_id']
        #TODO: BETTER QUERIES
        db.users.update_one({
            '$and':[
                {'email':(current_user)},
                {'inbox.group_invitation.group_id':ObjectId(group_id)}
            ]
        },{'$set':{'inbox.group_invitation.$.answer':answer}})
        #TODO : NEED TO LEARN OPTIMIZED QUERIES BRAH
        if answer == True:
            db.users.update_one({'email':(current_user)},{'$push':{'active_group':group_id}},upsert=True)
            db.groupworks.update_one({'_id':ObjectId(group_id)},{'$push':{'members':current_user}},upsert=True)
    

class SearchUser(Resource):
    def post(self):
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

        