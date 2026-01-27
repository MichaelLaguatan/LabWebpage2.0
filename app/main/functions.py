from app import db
from app.models import Server, ServerIP

def fill_rack_gaps(servers, rack_top=45, rack_bottom=1):
  filled = []
  current_u = rack_top

  for server in servers:
      # Gap above this server
      if server.top_unit < current_u:
        filled.append({'name':'BLANK', 'top_unit':current_u, 'bottom_unit':server.top_unit + 1})
      # Add the actual server
      filled.append(server)
      # Move pointer below this server
      current_u = server.bottom_unit - 1
  # Gap at bottom of rack
  if current_u >= rack_bottom:
    filled.append({'name':'BLANK', 'top_unit':current_u, 'bottom_unit':rack_bottom})
  return filled

def server_from_form(form, rack):
  server = Server().create_from_form(form, rack.id)
  db.session.add(server)
  db.session.flush()
  create_server_ips(server.id, form.ips.data)

def create_server_ips(server_id, ips):
  for ip in ips:
    if ip['deleted'] == '1' or ip['ip'] == '':
      continue
    db.session.add(ServerIP(category=ip['category'], label=ip['ip_name'], ip=ip['ip'], server_id=server_id))

def form_from_server(form, server):
  form.name.data = server.name
  form.serial_number.data = server.serial_number
  form.product_number.data = server.product_number
  form.login.data = server.login
  form.category.data = server.category.name
  form.vendor.data = server.vendor.name
  form.top_unit.data = server.top_unit
  form.bottom_unit.data = server.bottom_unit
  form.power_button.data = server.power_button
  form.power_button_ip.data = server.power_button_ip
  form.monday_on.data = server.monday_on
  form.friday_off.data = server.friday_off
  form.old_server_name.data = server.name
  form.ips.entries = []
  for ip in server.ips:
    form.ips.append_entry({
      'ip_name': ip.label,
      'category': ip.category.name,
      'ip': ip.ip,
      'deleted': '0'
    })
    