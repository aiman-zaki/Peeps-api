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
from resources import auth,users,groupworks,assignments
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
@app.route('/static/groupworks/<group_id>/profile/image')
def group_profile(group_id): 
    imagePath = app.root_path+app.config['UPLOAD_GROUPWORK_FOLDER']+group_id+'/profile.jpg'
    print(imagePath)
 
    return send_file(imagePath,mimetype='image/jpeg')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404

@socketio.on('connect')
def connect():
    print("Connected to /")

api.add_resource(groupworks.GroupWork, '/api/groupworks/groupwork')
api.add_resource(groupworks.GroupworkProfileImage, '/api/groupworks/profile/image')
api.add_resource(groupworks.ActiveGroupWorkDetails, '/api/groupworks/groupwork/detail')
api.add_resource(groupworks.Stash, '/api/groupworks/stash')
api.add_resource(groupworks.Members, '/api/groupworks/<group_id>/members')
api.add_resource(auth.Register, '/api/users/user')
api.add_resource(auth.Activate, '/api/auth/activate')
api.add_resource(auth.ActivateURL, '/api/auth/confirm/<token>')
api.add_resource(auth.Login, '/api/auth/login')
api.add_resource(auth.TokenRefresh, '/api/auth/refresh')

api.add_resource(users.ReplyInvitationInbox, '/api/users/inbox/replyinvitation')
api.add_resource(users.GroupInvitationInbox, '/api/users/inbox/groupinvitation')
api.add_resource(users.Profile, '/api/users/profile')
api.add_resource(users.ProfileImage, '/api/users/upload')

api.add_resource(assignments.Assignments, '/api/assignments/')
api.add_resource(assignments.Assignment, '/api/assignments/assignment')

api.add_resource(assignments.AddTask,'/api/assignments/task/add')
api.add_resource(assignments.UpdateTask, '/api/assignments/<assignment_id>/<task_id>/task')
api.add_resource(assignments.UpdateTaskStatus,'/api/assignments/task/status')

api.add_resource(users.SearchUser,'/api/users/search')
socketio.on_namespace(GroupChat('/group_chat'))

if __name__ == "__main__":
    socketio.run(app,port=5000,host="0.0.0.0")