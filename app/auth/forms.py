from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, EqualTo
import sqlalchemy as sa
from app import db
from app.models import User

class LoginForm(FlaskForm):
  username = StringField('Username', validators=[DataRequired(message='Please input a username')])
  password = PasswordField('Password', validators=[DataRequired(message='Please input a password')])
  remember_me = BooleanField('Remember Me')
  submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
  username = StringField('Username', validators=[DataRequired(message='Please input a username')])
  password = PasswordField('Password', validators=[DataRequired(message='Please input a password')])
  password2 = PasswordField('Repeat Password', validators=[DataRequired(message='Please repeat your password'), EqualTo('password')])
  submit = SubmitField('Register')

  def validate_username(self, username):
    user = db.session.scalar(sa.select(User).where(User.username == username.data))
    if user is not None:
      raise ValidationError('Please use a different username.')