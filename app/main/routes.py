from flask import render_template, redirect, url_for, request, current_app
from flask_login import login_required
import logging
import sqlalchemy as sa
from app import db
from app.main import bp
from app.main.functions import fill_rack_gaps, server_from_form, create_server_ips, form_from_server
from app.main.forms import ServerForm, RackForm
from app.models import Rack, Server

# Enable debug logging
logging.basicConfig(level=logging.INFO)

'''
MAIN WEBPAGE STUFF
'''

@bp.route('/')
@bp.route('/index')
def index():
  db_racks = db.session.scalars(sa.select(Rack)).unique().all()
  db_racks.sort(key=lambda rack: rack.name)
  for rack in db_racks:
    rack.servers.sort(key=lambda server: server.top_unit, reverse=True)
    rack.display_servers = fill_rack_gaps(rack.servers)
  return render_template('index.jinja2', title='Denver Lab Webpage', db_racks=db_racks)

@bp.route('/lab_temp_graph')
def lab_temp_graph():
  return render_template('lab_temp_graph.jinja2', title='Lab Temperature Graph', temp_limit=current_app.config['TEMPERATURE_LIMIT'])

'''
RACK STUFF
'''
 
@login_required
@bp.route('/add_rack', methods=["GET", "POST"])
def add_rack():
  form = RackForm()
  if form.validate_on_submit():
    rack = Rack().create_from_form(form)
    db.session.add(rack)
    db.session.commit()
    return redirect(url_for('main.index'))
  form.mgmt_ip.data = '10.210.'
  form.oobm_ip.data = '10.210.'
  form.stream_1_ip.data = '10.210.'
  form.stream_2_ip.data = '10.210.'
  return render_template('add_rack.jinja2', title='Add Rack', form=form)

@login_required
@bp.route('/delete_rack/<rack_name>')
def delete_rack(rack_name):
  rack = db.session.scalar(sa.select(Rack).where(Rack.name == rack_name))
  db.session.delete(rack)
  db.session.commit()
  return redirect(url_for('main.index'))

@login_required
@bp.route('/edit_rack/<rack_name>', methods=["GET", "POST"])
def edit_rack(rack_name):
  rack = db.session.scalar(sa.select(Rack).where(Rack.name == rack_name))
  form = RackForm(obj=rack)
  if form.validate_on_submit():
    form.populate_obj(rack)
    db.session.commit()
    return redirect(url_for('main.index'))
  return render_template('add_rack.jinja2', title='Edit Rack', form=form)

'''
SERVER STUFF
'''

@login_required
@bp.route('/add_server/<rack_name>', methods=['GET', 'POST'])
def add_server(rack_name):
  rack = db.session.scalar(sa.select(Rack).where(Rack.name == rack_name))
  form = ServerForm()
  form.rack_name.data = rack_name
  if form.validate_on_submit():
    server_from_form(form, rack)
    db.session.commit()
    return redirect(url_for('main.index'))
  rack.servers.sort(key=lambda server: server.top_unit, reverse=True)
  rack.display_servers = fill_rack_gaps(rack.servers)
  return render_template('add_server.jinja2', title='Add Server', form=form, rack=rack)

@login_required
@bp.route('/delete_server/')
def delete_server():
  server_name = request.args.get('server_name')
  server = db.session.scalar(sa.select(Server).where(Server.name == server_name))
  db.session.delete(server)
  db.session.commit()
  return redirect(url_for('main.index'))


@login_required
@bp.route('/edit_server/<rack_name>/', methods=['GET', 'POST'])
def edit_server(rack_name):
  rack = db.session.scalar(sa.select(Rack).where(Rack.name == rack_name))
  form = ServerForm()
  form.rack_name.data = rack.name
  server_name = request.args.get('server_name')
  server = db.session.scalar(sa.select(Server).where(Server.name == server_name))
  if form.validate_on_submit():
    server.update_from_form(form)
    for ip in server.ips:
      db.session.delete(ip)
    create_server_ips(server.id, form.ips.data)
    db.session.commit()
    return redirect(url_for('main.index'))
  rack.servers.sort(key=lambda server: server.top_unit, reverse=True)
  rack.display_servers = fill_rack_gaps(rack.servers)
  form_from_server(form, server)
  return render_template('add_server.jinja2', title='Edit Server', form=form, rack=rack)
