from pymongo import MongoClient

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity,decode_token,create_refresh_token,jwt_refresh_token_required
)
import re
import datetime 
import functools
from flask import Flask,jsonify,request,json,render_template,send_file
from flask_cors import CORS
from flask_restful import Resource, Api, abort
from flask_mail import Mail, Message

from flask_socketio import SocketIO, emit,ConnectionRefusedError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.serving import run_simple
import config

from main import app, jwt , api
from resources import auth,users,groupworks,assignments,inbox,stash
from socket_io import socketio , GroupChat


@jwt.expired_token_loader
def expired_token_callback(expired_token):
    token_type = expired_token['type']
    return jsonify({
        'status':401,
        'sub_status':42,
        'msg': 'The {} token has expired'.format(token_type)
    }),401

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/client')
def testsocketio():
    return render_template('test-socketio.html')

@app.route('/static/logo')
def logo():
    imagePath = app.root_path+"/web/static/images/logo.png"
    return send_file(imagePath,mimetype='image/png')

#TODO : Im lazy will implement better solution
@app.route('/static/users/<user_id>/profile/image')
def user_profile(user_id):
    try :
        imagePath = app.root_path+app.config['UPLOAD_USERS_FOLDER']+user_id+'/profile.jpg'
        return send_file(imagePath,mimetype='image/jpeg')
    except:
        imagePath = app.root_path+"/web/static/images/logo.png"
        return send_file(imagePath,mimetype='image/png')

@app.route('/static/groupworks/<group_id>/profile/image')
def group_profile(group_id): 
    try:
        imagePath = app.root_path+app.config['UPLOAD_GROUPWORK_FOLDER']+group_id+'/profile.jpg' 
        return send_file(imagePath,mimetype='image/jpeg')
    except:
        imagePath = app.root_path+"/web/static/images/logo.png"
        return send_file(imagePath,mimetype='image/png')
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404

@socketio.on('connect')
def connect():
    print("Connected to /")

api.add_resource(groupworks.Groupwork, '/api/groupworks/groupwork')
api.add_resource(groupworks.GroupworkProfileImage, '/api/groupworks/profile/image')

api.add_resource(groupworks.Stash, '/api/groupworks/stash')

api.add_resource(groupworks.Members, '/api/groupworks/<group_id>/members')
api.add_resource(groupworks.Roles, '/api/groupworks/<group_id>/roles')
api.add_resource(stash.Notes,'/api/groupworks/<group_id>/notes')
api.add_resource(assignments.Assignments, '/api/groupworks/<group_id>/assignments')
api.add_resource(assignments.Assignment, '/api/groupworks/groupwork/assignment')

api.add_resource(assignments.Tasks,'/api/groupworks/groupwork/<assignment_id>/tasks')
api.add_resource(assignments.UpdateTask, '/api/groupworks/groupwork/<assignment_id>/<task_id>/task')
api.add_resource(assignments.UpdateTaskStatus,'/api/groupworks/groupwork/<assignment_id>/task/status')


api.add_resource(auth.Register, '/api/users/user')
api.add_resource(users.Groupworks, '/api/users/user/groupworks')
api.add_resource(groupworks.ActiveGroupWorkDetails, '/api/groupworks/groupwork/detail')

api.add_resource(auth.Activate, '/api/auth/activate')
api.add_resource(auth.ActivateURL, '/api/auth/confirm/<token>')
api.add_resource(auth.Login, '/api/auth/login')
api.add_resource(auth.TokenRefresh, '/api/auth/refresh')
api.add_resource(groupworks.TestQuery, '/api/test')
api.add_resource(inbox.ReplyInvitationInbox, '/api/users/inbox/replyinvitation')
api.add_resource(inbox.GroupInvitationInbox, '/api/users/inbox/groupinvitation')
api.add_resource(users.Profile, '/api/users/user/profile')
api.add_resource(users.ProfileImage, '/api/users/user/upload')




api.add_resource(users.SearchUser,'/api/users/search')
socketio.on_namespace(GroupChat('/group_chat'))

if __name__ == "__main__":
    socketio.run(app,port=5000,host="0.0.0.0")