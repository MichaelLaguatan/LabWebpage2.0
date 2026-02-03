from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, BooleanField, FieldList, FormField, HiddenField, SubmitField
from wtforms.validators import DataRequired, ValidationError, IPAddress, Optional, Regexp
import sqlalchemy as sa
from app import db
from app.models import Rack, Server

class IPForm(FlaskForm):
  class Meta:
    csrf = False
  category = SelectField('Category', choices=[('OOBM', 'OOBM'), ('MANAGEMENT', 'Management')], default='MANAGEMENT')
  ip_name = StringField('IP Label')
  ip = StringField('IP Address', validators=[Optional(), IPAddress(message='Please enter a valid IP address')])
  deleted = HiddenField(default='0')

class ServerForm(FlaskForm):
  name = StringField('Server Name', validators=[DataRequired('Please input a name for the server'), Regexp(r"^[a-zA-Z0-9_\-'/()& ]+$", message='Name must contain only letters, numbers, underscores, dashes, single quotes, forward slashes, parentheses, and spaces')])
  category = SelectField('Category', choices=[('UTILITY', 'Utility'), ('TITAN', 'Titan'), ('KUBE', 'Kubernetes'), ('VM', 'Virtual Machine'), ('GRAY', 'Gray')], default='UTILITY')
  vendor = SelectField('Vendor', choices=[('DELL', 'Dell'), ('HP', 'HP'), ('OTHER', 'Other')], default='Other')
  serial_number = StringField('Serial Number')
  product_number = StringField('Product Number')
  login = StringField('Login')
  ips = FieldList(FormField(IPForm), min_entries=1)
  top_unit = IntegerField('Top Unit', validators=[DataRequired()])
  bottom_unit = IntegerField('Bottom Unit', validators=[DataRequired()])
  power_button = BooleanField('Power Button')
  power_button_ip = StringField('Power IP Address', validators=[Optional(), IPAddress(message="Please enter a valid IP address")])
  monday_on = BooleanField('Monday On')
  friday_off = BooleanField('Friday Off')
  rack_name = HiddenField()
  old_server_name = HiddenField()
  submit = SubmitField('Submit')

  def validate_top_unit(self, top_unit):
    if top_unit.data < self.bottom_unit.data:
      raise ValidationError('Top unit of server must be greater than bottom unit')
    rack = db.session.scalar(sa.select(Rack).where(Rack.name == self.rack_name.data))
    current_server = db.session.scalar(sa.select(Server).where(Server.name == self.old_server_name.data and Server.rack_id == rack.id))
    for server in rack.servers:
      if current_server != None and current_server == server:
        continue
      if server.top_unit >= top_unit.data and server.bottom_unit <= top_unit.data:
        raise ValidationError('Server location overlaps existing server')
  
  def validate_bottom_unit(self, bottom_unit):
    rack = db.session.scalar(sa.select(Rack).where(Rack.name == self.rack_name.data))
    current_server = db.session.scalar(sa.select(Server).where(Server.name == self.old_server_name.data and Server.rack_id == rack.id))
    for server in rack.servers:
      if current_server != None and current_server == server:
        continue
      if server.bottom_unit <= bottom_unit.data and server.top_unit >= bottom_unit.data:
        raise ValidationError('Server location overlaps existing server')

class RackForm(FlaskForm):
  name = StringField('Rack Name', validators=[DataRequired(message='Please input a name or the rack'), Regexp(r"^[a-zA-Z0-9_\-/() ]+$", message='Name must contain only letters, numbers, underscores, dashes, forward slashes, parentheses, and spaces')])
  mgmt_ip = StringField('Management IP', validators=[DataRequired(message='Please input a template for the management IPs')])
  oobm_ip = StringField('OOBM IP', validators=[DataRequired(message='Please input a template for the OOBM IPs')])
  stream_1_ip = StringField('Stream 1 IP', validators=[DataRequired(message='Please input a template for the stream 1 IPs')])
  stream_2_ip = StringField('Stream 2 IP', validators=[DataRequired(message='Please input a template for the stream 2 IPs')])
  submit = SubmitField('Submit')