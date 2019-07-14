import urllib.request
import requests
from bs4 import BeautifulSoup
import re
import api.icress.core as icress
import api.icress.config as config

LOGIN_URL =  'https://i-learn.uitm.edu.my/v3/users/loginForm/1'
PROFILE_URL = 'https://i-learn.uitm.edu.my/v3/users/profile'


loginInfo = {'data[User][username]': config.USERNAME , 'data[User][password]' : config.PASSWORD }

def loginUrl():
    req = urllib.request.urlopen(LOGIN_URL)
    html = BeautifulSoup(req,'html.parser')
    return html

def istudent():
    session = requests.session()
    session.post(url=LOGIN_URL, data=loginInfo)
    url = session.get(url=PROFILE_URL)
    html = BeautifulSoup(url.content, 'html.parser')
    print(html)
    text = re.findall("('[A-Z]{3}[0-9]{3}','[0-9]{7}','\w{9}','\w{6}')",str(html))
    registeredCourse = []
    for data in text:
        dataDictionary = {}
        data = data.replace("'","")
        dataArray = data.split(',')
        dataDictionary['course'] = dataArray[0]
        dataDictionary['class'] = dataArray[2]
        registeredCourse.append(dataDictionary)
    print(registeredCourse)
    return registeredCourse

def main():
    # registeredCourses = istudent(username,password)
    # timetablelist = []
    # for faculty in faculties:
    #     for course in registeredCourses:
    #         timetable = icress.fetchTimeTable(faculty,course)
    #         if(timetable is not None):
    #             if(timetable[0] == course['class']):
    #                 timetablelist.append(timetable)
    

    # return timetablelist
    pass
        
                    
                



