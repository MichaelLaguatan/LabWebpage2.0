from flask import request, current_app
import requests, logging
import sqlalchemy as sa
import csv
from datetime import datetime, timedelta
from app import db
from app.api import bp
from app.api.functions import get_current_temperature, fetch_power, parse_isoformat
from app.models import Server, User
from concurrent.futures import ThreadPoolExecutor, as_completed

# Enable debug logging
logging.basicConfig(level=logging.INFO)

@bp.route("/temperature")
def get_temperature():
  temp = get_current_temperature()
  return temp

@bp.route('/modal/')
def modal():
  server_name = request.args.get('server_name')
  server = db.session.scalar(sa.select(Server).where(Server.name == server_name))
  oobm = ''
  mgmt = ''
  for ip in server.ips:
    if ip.category.name == 'MANAGEMENT':
      if ip.label == "":
        mgmt += f'<a href="http://{ip.ip}" target="_blank">{ip.ip}</a><br>'
      else:
        mgmt += f'<a>{ip.label}: </a><a href="http://{ip.ip}" target="_blank">{ip.ip}</a><br>'
    else:
      if ip.label == "":
        oobm += f'<a href="http://{ip.ip}" target="_blank">{ip.ip}</a><br>'
      else:
        oobm += f'<a>{ip.label}: </a><a href="http://{ip.ip}" target="_blank">{ip.ip}</a><br>'
  return {'name': server.name, 'serial_number': server.serial_number or "None", 'product_number': server.product_number or "None", 'login': server.login or "None", 'oobm': oobm or "None", 'mgmt': mgmt or "None"}

@bp.route('/power_states')
def power_states():
  servers = list(db.session.scalars(sa.select(Server).where(Server.vendor.in_(["DELL", "HP"]), Server.power_button_ip != '')))
  power_states = {}
  session = requests.Session()
  session.verify = False
  session.auth = ('root', 'Denver2018!')
  with ThreadPoolExecutor(max_workers=20) as pool:
    futures = [pool.submit(fetch_power, server, session) for server in servers]
    for f in as_completed(futures):
      ip, state = f.result()
      power_states[ip] = state
  return power_states

@bp.route("power_on/<power_ip>", methods=['POST'])
def power_on(power_ip):
  server_name = request.args.get('server_name')
  server = db.session.scalar(sa.select(Server).where(Server.name == server_name))
  data={'ResetType': 'On'}
  if server.vendor.name == 'DELL':
    try:
      req=requests.post(f'https://{power_ip}/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset', json=data, verify=False, auth=('root','Denver2018!'))
      return '', req.status_code
    except:
      return '', req.status_code
  elif server.vendor.name == 'HP':
    try:
      req=requests.post(f'https://{power_ip}/redfish/v1/Systems/1/Actions/ComputerSystem.Reset', json=data, verify=False, auth=('root','Denver2018!'))
      return '', req.status_code
    except:
      return '', req.status_code
  else:
    return '', 400
  
@bp.route('/get_temperature_history')
def get_temperature_history():
    labels = []
    data = []
    now = datetime.now()
    cutoff = now - timedelta(days=current_app.config['MAX_DAYS'])
    try:
        with open(current_app.config['DATA_FILE'], 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                try:
                    ts = parse_isoformat(row[0])
                    if ts >= cutoff:
                        labels.append(ts.strftime('%Y-%m-%d %H:%M'))
                        data.append(float(row[1]))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return {'labels': labels, 'data': data}
    
@bp.route('/clear_db', methods=["POST"])
def clear_db():
  db.drop_all()
  db.create_all()
  administrator = User(username=request.args['username'])
  administrator.set_password(request.args['password'])
  db.session.add(administrator)
  db.session.commit()
  logging.info("DB has been reset")
  return '', 204