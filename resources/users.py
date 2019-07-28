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
from flask_restful import Resource, Api, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson import json_util
from app import db , app 
from bson.json_util import dumps, ObjectId

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

    return '.' in filename and \
        filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS 

def fileExtension(filename):
    return filename.rsplit('.',1)[1].lower()

class ProfileImage(Resource):
    def post(self):
        userId = request.form['_id']
        file = request.files['file']
        if file and allowed_file(file.filename):
            path = app.root_path+app.config['UPLOAD_FOLDER']+userId
            if os.path.exists(path) is False:
                os.mkdir(path)
            file.save(os.path.join(path,"profile."+fileExtension(file.filename)))
            return {"message":"Profile Picture Updated"},200
        return {"message":"Oops something is wrong"}
    
    def get(self):
        pass

        

class Profile(Resource):
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        user = db.users.find_one(
            {'_id': ObjectId(current_user)},{'_id':1,'profile':1,'joined_group':1,'email':1}
        )
        return Response(
            json_util.dumps(user),
            mimetype='application/json'
        )

    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        contact_no = request.json['contact_no']
        programme_code = request.json['programme_code']
        db.users.update_one({'email':current_user},{'$set':{'profile':{'contact_no':contact_no,'programme_code':programme_code}}})


class Inbox(Resource):
    @jwt_required
    def get(self,filtered):
        #TODO : FILTERED WORD NEED TO BE SANITIZED WITH INJECTION or Something
        current_user = get_jwt_identity()
        inbox = db.users.find_one({'_id': ObjectId(current_user)},{filtered:1})
        return Response(
            json_util.dumps(inbox),
            mimetype='application/json'
        )
    
class ReplyInvitationInbox(Resource):
    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        answer = request.json['answer']
        group_id = request.json['group_id']
        print(group_id)
        #TODO: BETTER QUERIES
        db.users.update_one({
            '$and':[
                {'_id':ObjectId(current_user)},
                {'inbox.group_invitation.group_id':ObjectId(group_id)}
            ]
        },{'$set':{'inbox.group_invitation.$.accept':answer}})
        #TODO : NEED TO LEARN OPTIMIZED QUERIES BRAH
        if answer == "accept":
            db.users.update_one({'_id':ObjectId(current_user)},{'$push':{'joined_group':group_id}},upsert=True)
            db.groupworks.update_one({'_id':ObjectId(group_id)},{'$push':{'members':current_user}},upsert=True)
    

        