from pymongo import MongoClient

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity,decode_token,create_refresh_token,jwt_refresh_token_required
)
import re
import datetime 
import functools
from flask import Flask,jsonify,request,json,render_template
from flask_cors import CORS
from flask_restful import Resource, Api, abort
from flask_mail import Mail, Message

from flask_socketio import SocketIO, emit,ConnectionRefusedError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.serving import run_simple
import config

from app import app, jwt , socketio, api
from resources import auth,icress,users,groupworks


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
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404


@socketio.on('connect')
@jwt_required
def connect():
    print("Client Connected")


@socketio.on('disconnect')
def disconnect():
    print("Client Disconnected")



api.add_resource(groupworks.GroupWork, '/api/groupworks/joined_group')
api.add_resource(auth.Register, '/api/auth/register')
api.add_resource(auth.Activate, '/api/auth/activate')
api.add_resource(auth.ActivateURL, '/api/auth/confirm/<token>')
api.add_resource(auth.Login, '/api/auth/login')
api.add_resource(auth.TokenRefresh, '/api/auth/refresh')
api.add_resource(users.Profile, '/api/users/profile')
api.add_resource(users.ProfileImage, '/api/users/upload')
api.add_resource(icress.Faculty,'/api/icress/faculty')
api.add_resource(icress.Course,'/api/icress/<faculty>/course')
api.add_resource(icress.Timetable,'/api/icress/<faculty>/<course>/timetable')


if __name__ == "__main__":
    socketio.run(app,port=5000,host="0.0.0.0")