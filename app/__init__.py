from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from flask_mail import Mail

login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please login to view this page.'
db = SQLAlchemy()
migrate = Migrate()
scheduler = APScheduler()
mail = Mail()

def create_app(config_class=Config):
  app = Flask(__name__)
  app.config.from_object(config_class)
  db.init_app(app)
  migrate.init_app(app, db)
  login.init_app(app)
  scheduler.init_app(app)
  mail.init_app(app)

  from app.auth import bp as auth_bp
  app.register_blueprint(auth_bp, url_prefix='/auth')

  from app.main import bp as main_bp
  app.register_blueprint(main_bp)

  from app.api import bp as api_bp
  app.register_blueprint(api_bp, url_prefix='/api')

  from app.email import bp as email_bp
  app.register_blueprint(email_bp, url_prefix='/email')

  from app.api.jobs import register_jobs
  register_jobs(scheduler)
  scheduler.start()
  
  return app

from app import models