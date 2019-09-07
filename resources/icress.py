from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity,decode_token,create_refresh_token,jwt_refresh_token_required
)

from resources.core import fetchFaculties,fetchCourse,fetchTimeTable

from flask import Flask,jsonify,request,json
from flask_restful import Resource, Api, abort

class Faculty(Resource):
    def get(self):
        return jsonify(fetchFaculties())

class Course(Resource):
    def get(self,faculty):
        return jsonify(fetchCourse(faculty))

class Timetable(Resource):
    def get(self,faculty,course):
        return jsonify(fetchTimeTable(faculty,course))