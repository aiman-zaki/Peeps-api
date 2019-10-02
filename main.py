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

from flask_socketio import SocketIO, emit,ConnectionRefusedError,Namespace
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.serving import run_simple
import config
from bson import ObjectId
app = Flask(__name__,static_url_path='',static_folder='web/static',template_folder='web/templates')
app.config.from_object('config')
api = Api(app)
CORS(app)
mail = Mail(app)
jwt = JWTManager(app)
socketio = SocketIO(app)
app.config['PROPAGATE_EXCEPTIONS'] = True
client = MongoClient("mongodb://%s:%s@localhost:27017/" % ("admin","password"))
db = client.api
socketio = SocketIO(app)
