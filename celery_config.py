import datetime
from background_script import stats
from celery import Celery
from celery.schedules import crontab
from main import app


class Config:
    timezone = 'Asia/Kuala_Lumpur'
    celery_result_backend = 'mongodb'
    celery_mongodb_backend_settings = {
        'host':'localhost',
        'port':27017,
        'database':'celery',
        'taskmeta_collection':'celery_taskmeta',

    }
    celery_broker_url = "mongodb://%s:%s@localhost:27017/" % ("admin","password")

    #celery_broker_url = 'redis://localhost:6379/0'
    #celery_result_backend = 'redis://localhost:6379/0'
    beat_schedule = {
        'send-email-notifications': {
            'task': 'celery_config.active_user_week',
            'schedule': 
                crontab(minute='59',
                    hour='15', day_of_week='sun') ,
        },
    }
    worker_hijack_root_logger = False


celery = Celery(app,broker=Config.celery_broker_url)
celery.config_from_object(Config)


@celery.on_after_configure.connect
def setup_periodic_tasks(sender,**kwargs):
    pass

@celery.task
def active_user_week():
    print('-----active_user_week------')
    stats.insert_active_user_per_week()
    print('---done-----')
    


