from flask import render_template, redirect, url_for, request
from flask_login import login_user, logout_user, current_user
from urllib.parse import urlsplit
import sqlalchemy as sa
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegisterForm
from app.models import User

@bp.route('/login', methods=["GET", "POST"])
def login():
  if current_user.is_authenticated:
    return redirect(url_for('main.index'))
  form = LoginForm()
  if form.validate_on_submit():
      user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
      if user is None or not user.check_password(form.password.data):
        return redirect(url_for('auth.login'))
      login_user(user, remember=form.remember_me.data)
      next_page = request.args.get('next')
      if not next_page or urlsplit(next_page).netloc != '':
        next_page = url_for('main.index')
      return redirect(next_page)
  return render_template('auth/login.jinja2', title='Sign In', form=form)

@bp.route('/logout')
def logout():
  logout_user()
  return redirect(url_for('main.index'))