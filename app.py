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
from resources import users,icress

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.serving import run_simple
import config

app = Flask(__name__,static_url_path='',static_folder='web/static',template_folder='web/templates')
app.config.from_object('config')
api = Api(app)
CORS(app)
mail = Mail(app)
jwt = JWTManager(app)

app.config['PROPAGATE_EXCEPTIONS'] = True


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



api.add_resource(users.Register, '/api/register')
api.add_resource(users.Activate, '/api/activate')
api.add_resource(users.ActivateURL, '/api/confirm/<token>')
api.add_resource(users.Login, '/api/login')
api.add_resource(users.TokenRefresh, '/api/refresh')
api.add_resource(icress.Faculty,'/api/icress/faculty')
api.add_resource(icress.Course,'/api/icress/<faculty>/course')
api.add_resource(icress.Timetable,'/api/icress/<faculty>/<course>/timetable')


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0',port='5000')