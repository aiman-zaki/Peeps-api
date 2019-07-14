import urllib.request
import api.icress.autofetch 
import pymongo
from bs4 import BeautifulSoup
from werkzeug.contrib.cache import SimpleCache

import logging 
logging.basicConfig(level=logging.DEBUG)


BASE_URL = "http://icress.uitm.edu.my/jadual/jadual/jadual.asp"
COURSE_URL = "http://icress.uitm.edu.my/jadual/"
cache = SimpleCache()

def initRequest():
    req = urllib.request.urlopen(BASE_URL)   
    return req 


def base_url():
    html = BeautifulSoup(initRequest(),'html.parser')
    return html

def fetchAllFaculty():
    facCache = cache.get('faculties')
    if facCache is None:
        print("loading fresh faculties data")
        facultyList=[]
        html= base_url()
        for faculty in html.find_all('option'):
            facultyDict={}
            facultyDict['code'] = faculty.get('value')[0:2]
            facultyDict['value'] = faculty.get('value')[3:]
            #facultyDict[faculty.get('value')[0:2]] = faculty.get('value')[3:]
            facultyList.append(facultyDict)
        facCache = facultyList
        cache.set('faculties',facCache,timeout=5*60)
        return facCache
    else:
        print("cached faculties data")
        return facCache

def fetchFaculties():
    facCache = cache.get('faculties')
    if facCache is None:
        facultyList = []
        html = base_url()
        for faculty in html.find_all('option'):
            facultyList.append(faculty.get('value'))
        facCache = facultyList
        cache.set('faculties',facCache,timeout=5*60)
        return facCache
    else:
        print("cached faculties data")
        return facCache


def fetchCourse(userFaculty):
    coursesCache = cache.get(userFaculty)
    if coursesCache is None: 
        coursesList = []
        try:
            req = urllib.request.urlopen(COURSE_URL+userFaculty+"/"+userFaculty+".html")
            html = BeautifulSoup(req.read(),'html.parser')
            a = html.find_all('a')
            for course in a:
                courseDict = {}
                courseDict['course'] = course.string
                coursesList.append(courseDict)
            coursesCache = coursesList
            #cache.set(userFaculty,coursesCache,timeout=5*60)
       
        except urllib.error.HTTPError as e:
            logging.error('HTTPError = ' + str(e.code))
        except urllib.error.URLError as e:
            logging.error('URLError = ' + str(e.reason))
        except Exception:
            import traceback
            logging.error('generic exception: ' + traceback.format_exc())
        return coursesCache
    else:
        print("from cache")
        return coursesCache

def timeFormat24(t):
    if t[-2:] == 'am':
        if(t[2]== ':'):
            return(t[:-2])
        else:
            return('0'+t[:-2])
    else:
        try:
            nt = int(t[:2])
            if(nt==12):
                return (str(nt)+t[2:5])
            else:
                return(str(nt+12)+t[2:5])
        except:
            return(str(int(t[:1])+12)+t[1:4])

def fetchTimeTable(faculty,userCourse):
    ttList = []
    try:
        req = urllib.request.urlopen(COURSE_URL+faculty+"/"+userCourse+".html")
        html = BeautifulSoup(req.read(),'html.parser')
        table = html.find('table')
        rows = table.findAll('tr')
        for row in rows[1:]:
            dcol = []
            cols = row.find_all('td')
            time = 0 
            for col in cols:
                try:
                    stripText = col.string.replace('\r\n','')
                except:
                    stripText = col.string
                if(time==1 or time==2):
                    stripText = timeFormat24(stripText)
                dcol.append(stripText)
                time += 1
            ttList.append(dcol)
    except urllib.error.HTTPError as e:
        logging.error('HTTPError = ' + str(e.code))
    except urllib.error.URLError as e:
        logging.error('URLError = ' + str(e.reason))
    except Exception:
        import traceback
        logging.error('generic exception: ' + traceback.format_exc())
    
    return ttList
