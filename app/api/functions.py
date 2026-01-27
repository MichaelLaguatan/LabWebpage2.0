import requests, csv, logging, json
from datetime import datetime, timedelta
import sqlalchemy as sa
from app import db, scheduler
from app.models import Server
from pysnmp.hlapi import getCmd, SnmpEngine, UsmUserData, usmHMACSHAAuthProtocol, usmAesCfb128Protocol, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # Gets rid of warnings for unverified https requests

STATUS_URLS = {
  "DELL": "https://{ip}/redfish/v1/Systems/System.Embedded.1/",
  "HP":   "https://{ip}/redfish/v1/Systems/1/"
}

POWER_URLS = {
  "DELL": "https://{ip}/redfish/v1/Systems/System.Embedded.1/Actions/ComputerSystem.Reset",
  "HP":   "https://{ip}/redfish/v1/Systems/1/Actions/ComputerSystem.Reset"
}

def power(server, session, payload):
  url = POWER_URLS[server.vendor.name].format(ip=server.power_button_ip)
  try:
    r = session.post(url, json=payload, timeout=10)
  except:
    None

def power_on():
  app = scheduler.app
  with app.app_context():
    servers = db.session.scalars(sa.select(Server).where(Server.vendor.in_(["DELL", "HP"]), Server.monday_on == True))
    session = requests.Session()
    session.verify = False
    session.auth = ('', '')
    payload = {'ResetType': 'On'}
    with ThreadPoolExecutor(max_workers=20) as pool:
      for server in servers:
        pool.submit(power, server, session, payload)

def shutdown():
  app = scheduler.app
  with app.app_context():
    servers = db.session.scalars(sa.select(Server).where(Server.vendor.in_(["DELL", "HP"]), Server.friday_off == True))
    session = requests.Session()
    session.verify = False
    session.auth = ('', '')
    payload = {'ResetType': 'GracefulShutdown'}
    with ThreadPoolExecutor(max_workers=20) as pool:
      for server in servers:
        pool.submit(power, server, session, payload)

def fetch_power(server, session):
  url = STATUS_URLS[server.vendor.name].format(ip=server.power_button_ip)
  try:
    r = session.get(url, timeout=8)
    return server.power_button_ip, r.json().get("PowerState")
  except Exception:
    return server.power_button_ip, None

def get_current_temperature():
  response = {"temp_f": None}
  try:
      iterator = getCmd(
          SnmpEngine(),
          UsmUserData(userName="", authKey="", privKey="", authProtocol=usmHMACSHAAuthProtocol, privProtocol=usmAesCfb128Protocol),
          UdpTransportTarget(("", 161), timeout=1, retries=3),
          ContextData(),
          ObjectType(ObjectIdentity(""))
      )
      errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
      if errorIndication:
        logging.error(f"SNMP error: {errorIndication}")
        response["error"] = str(errorIndication)
        return response
      if errorStatus:
        error_msg = f"{errorStatus.prettyPrint()} at {errorIndex}"
        logging.error(error_msg)
        response["error"] = error_msg
        return response
      for oid, value in varBinds:
        temp_raw = int(value)
        temp_f = temp_raw / 10.0
        logging.info(f"Temperature parsed: {temp_f}")
        response["temp_f"] = temp_f
  except Exception as e:
    logging.exception("Unhandled SNMP exception")
    response["error"] = str(e)
  return response

def parse_isoformat(dtstr):
  try:
    return datetime.strptime(dtstr, "%Y-%m-%dT%H:%M:%S.%f")
  except ValueError:
    return datetime.strptime(dtstr, "%Y-%m-%dT%H:%M:%S")
  
def get_last_alert(path: str, now: datetime):
  try:
    with open(path, 'r') as f:
      return json.load(f).get('last_alert', now.isoformat())
  except FileNotFoundError:
    logging.warning("Alert file not found in defined location, creating a new one")
    set_last_alert(path, now)
  return now.isoformat()

def set_last_alert(path: str, time_of_alert: datetime):
  with open(path, 'w') as f:
    json.dump({"last_alert": time_of_alert.isoformat()}, f)

def store_temperature():
  app = scheduler.app
  with app.app_context():
    now = datetime.now()
    temp = get_current_temperature()['temp_f']
    if temp >= app.config['TEMPERATURE_LIMIT']:
      last_alert = parse_isoformat(get_last_alert(app.config['ALERT_FILE'], now))
      cooldown = timedelta(seconds=app.config['ALERT_COOLDOWN'])
      if cooldown <= now - last_alert:
        resp = requests.put(f'http://localhost/email/send_alert/{temp}')
        set_last_alert(app.config['ALERT_FILE'], now)

    rows = []
    # Read existing data
    try:
      with open(app.config['DATA_FILE'], 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    except FileNotFoundError:
      logging.warning("Temperature file not found in defined location, creating a new one")
    # Append new row
    rows.append([now.isoformat(), str(temp)])
    # Prune old data
    cutoff = now - timedelta(days=app.config['MAX_DAYS'])
    pruned_rows = []
    for row in rows:
      try:
        ts = parse_isoformat(row[0])
        if ts >= cutoff:
          pruned_rows.append(row)
      except Exception as e:
        logging.error(f"Error parsing row {row}: {e}")
        continue
    # Write back
    with open(app.config['DATA_FILE'], 'w', newline='') as f:
      writer = csv.writer(f)
      writer.writerows(pruned_rows)