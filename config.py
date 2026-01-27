import os
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
  # DB Config
  SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
  SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
  # APScheduler Config
  SCHEDULER_API_ENABLED = True
  SCHEDULER_JOBSTORES = {
    'default': SQLAlchemyJobStore(
      url=SQLALCHEMY_DATABASE_URI
    )
  }
  # Temperature History Config
  DATA_FILE = os.path.join(basedir, 'temperature_history.csv')
  MAX_DAYS = 7
  # Temperature Email Alert Config
  MAIL_SERVER = ''
  MAIL_PORT = 587
  MAIL_USE_TLS = True
  MAIL_USE_SSL = False
  MAIL_USERNAME = ''
  MAIL_PASSWORD = ''
  MAIL_DEFAULT_SENDER = ''
  RECIPIENTS = []
  TEMPERATURE_LIMIT = 78
  ALERT_COOLDOWN = 3600
  ALERT_FILE = os.path.join(basedir, 'alert_state.json')

