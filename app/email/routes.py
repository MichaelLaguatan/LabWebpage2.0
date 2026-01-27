from flask import redirect, url_for, current_app
from flask_mail import Message
from threading import Thread
from app import mail
from app.email import bp

@bp.route('/send_alert/<current_temp>', methods=['PUT'])
def send_alert(current_temp):
  msg = Message(
    subject=f'Temperature Alert: {current_temp}°F',
    recipients=current_app.config['RECIPIENTS'],
    body=f'Temperature has exceeded {current_app.config['TEMPERATURE_LIMIT']}°F. Current temperature: {current_temp}°F'
  )
  Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
  return '', 204

def send_async_email(app, msg):
  with app.app_context():
    mail.send(msg)
