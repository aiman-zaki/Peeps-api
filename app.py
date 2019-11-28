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

from main import app, jwt , api , socketio
from resources import auth,users,groupworks,assignments,inbox,stash,groupwork_socket,forum,timeline,question,supervisor,courses
from resources_v2 import groupworksv2 , assignmentsv2


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
    

#Peeps API

#Authtentication API

api.add_resource(auth.Activate, '/api/auth/activate')
api.add_resource(auth.ActivateURL, '/api/auth/confirm/<token>')
api.add_resource(auth.Login, '/api/auth/login')
api.add_resource(auth.TokenRefresh, '/api/auth/refresh')
api.add_resource(auth.Register, '/api/auth/register')
#Users API
api.add_resource(users.SearchUser,'/api/users/search')

#User API
api.add_resource(inbox.ReplyInvitationInbox, '/api/user/inbox/reply_invitation')
api.add_resource(inbox.GroupInvitationInbox, '/api/user/inbox/group_invitation')
api.add_resource(users.Profile, '/api/user/profile')
api.add_resource(users.ProfileImage, '/api/user/upload')
api.add_resource(users.UserAssignmentsAndTasks,'/api/user/tasks')
api.add_resource(users.Role,'/api/user/role')
api.add_resource(users.ActiveGroupworks, '/api/user/groupworks')
api.add_resource(users.UserAssignments,'/api/user/assignments')

#Groupworks API
api.add_resource(groupworksv2.Groupworks, '/api/groupworks')
api.add_resource(groupworksv2.GroupworksSearch, '/api/groupworks/search')
#Requires Group Id 
api.add_resource(groupworksv2.GroupworkProfileImage, '/api/groupworks/<group_id>/picture')
api.add_resource(groupworksv2.Groupwork, '/api/groupworks/<group_id>')
api.add_resource(groupworksv2.Members, '/api/groupworks/<group_id>/members')
api.add_resource(groupworksv2.Roles, '/api/groupworks/<group_id>/roles')
api.add_resource(stash.Notes,'/api/groupworks/<group_id>/notes')
api.add_resource(groupworksv2.Requests,'/api/groupworks/<group_id>/requests')
api.add_resource(assignments.Assignments, '/api/groupworks/<group_id>/assignments')
api.add_resource(assignments.AssignmentDelete, '/api/groupworks/<group_id>/assignments/delete')
api.add_resource(assignments.AssignmentStatus, '/api/groupworks/<group_id>/assignments/status')
api.add_resource(timeline.Timeline,'/api/groupworks/<group_id>/timelines')
api.add_resource(stash.References,'/api/groupworks/<group_id>/references')
api.add_resource(assignments.AssignmentsUserPoint, '/api/groupworks/<group_id>/assignments/point')
api.add_resource(stash.PublicReferences,'/api/groupworks/<group_id>/references/public')

#Requires GroupId and Assignment Id 
api.add_resource(assignments.Assignment, '/api/groupworks/<assignment_id>')
api.add_resource(assignments.Tasks,'/api/groupworks/<assignment_id>/tasks')
api.add_resource(assignments.PeerReview,'/api/groupworks/<assignment_id>/peer-review')

api.add_resource(assignments.TaskStatus,'/api/groupworks/<assignment_id>/tasks/status')
api.add_resource(assignments.TaskAssignTo, '/api/groupworks/<assignment_id>/tasks/requests')
api.add_resource(assignments.Task, '/api/groupworks/<assignment_id>/<task_id>/task')

 
#Forum API
api.add_resource(forum.Forum, '/api/forums/<course>')
api.add_resource(forum.Discussion ,'/api/forums/<course>/<discussion>')
api.add_resource(forum.Markers,'/api/forums/<course>/markers')

#Peers Review
api.add_resource(question.Questions, '/api/questions')
api.add_resource(question.InitQuestions, '/api/questions/init')

#Supervisor
api.add_resource(courses.SupervisorCourse,'/api/supervisor/courses')
api.add_resource(supervisor.SuperviseGroupworks, '/api/supervisor/groupworks')
api.add_resource(courses.SupervisorGroupworkTemplate,'/api/supervisor/<code>/templates')

#course
api.add_resource(courses.SearchSupervisorGroupworkTemplate, '/api/courses/<code>/<supervisor>')
api.add_resource(courses.Courses, '/api/courses')
api.add_resource(courses.Course,'/api/courses/<code>')

#Socket-IO Namespace
socketio.on_namespace(groupwork_socket.GroupChat('/group_chat'))
socketio.on_namespace(groupwork_socket.Timeline('/timeline'))
socketio.on_namespace(groupwork_socket.Collaborate('/collaborate'))
 
if __name__ == "__main__":
    socketio.run(app,port=5000,host="0.0.0.0")