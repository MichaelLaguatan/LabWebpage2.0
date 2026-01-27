from typing import List, Optional
import enum
import sqlalchemy as sa
import sqlalchemy.orm as so
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login

class vendor(enum.Enum):
  HP = 1
  DELL = 2
  OTHER = 3

class server_type(enum.Enum):
  UTILITY = 1
  TITAN = 2
  KUBE = 3
  VM = 4
  GRAY = 5

class ip_type(enum.Enum):
  OOBM = 1
  MANAGEMENT = 2

class User(UserMixin, db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key=True)
  username: so.Mapped[str] = so.mapped_column(sa.String(60), index=True, unique=True)
  password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

  def set_password(self, password):
    self.password_hash = generate_password_hash(password)
  
  def check_password(self, password):
    return check_password_hash(self.password_hash, password)

  def __repr__(self):
    return f'<User {self.username}>'
  
@login.user_loader
def load_user(id):
  return db.session.get(User, int(id))

class Rack(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key=True)
  name: so.Mapped[str] = so.mapped_column(sa.String(60), index=True, unique=True, nullable=False)
  mgmt_ip: so.Mapped[str] = so.mapped_column(sa.String(45), nullable=False)
  oobm_ip: so.Mapped[str] = so.mapped_column(sa.String(45), nullable=False)
  stream_1_ip: so.Mapped[str] = so.mapped_column(sa.String(45), nullable=False)
  stream_2_ip: so.Mapped[str] = so.mapped_column(sa.String(45), nullable=False)

  servers: so.Mapped[List['Server']] = so.relationship(back_populates='location', cascade="all, delete-orphan", lazy="joined")

  @classmethod
  def create_from_form(cls, form):
    return cls(
      name=form.name.data,
      mgmt_ip=form.mgmt_ip.data,
      oobm_ip=form.oobm_ip.data,
      stream_1_ip=form.stream_1_ip.data,
      stream_2_ip=form.stream_2_ip.data
    )

  def __repr__(self):
    return f'<Rack {self.name}>'

class Server(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key=True)
  name: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, nullable=False)
  serial_number: so.Mapped[str] = so.mapped_column(sa.String(60), default='', nullable=False)
  product_number: so.Mapped[str] = so.mapped_column(sa.String(60), default='', nullable=False)
  login: so.Mapped[str] = so.mapped_column(sa.String(60), default='', nullable=False)
  category: so.Mapped[server_type] = so.mapped_column(sa.Enum(server_type), nullable=False)
  vendor: so.Mapped[vendor] = so.mapped_column(sa.Enum(vendor), nullable=False)
  top_unit: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
  bottom_unit: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
  power_button: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, nullable=False)
  power_button_ip: so.Mapped[str] = so.mapped_column(sa.String(45), default='', nullable=True)
  monday_on: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, nullable=False)
  friday_off: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False, nullable=False)
  rack_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Rack.id), index=True)

  location: so.Mapped[Rack] = so.relationship(back_populates='servers')
  ips: so.Mapped[List['ServerIP']] = so.relationship(back_populates='server', cascade="all, delete-orphan")

  __table_args__ = (
    sa.Index('idx_vendor_power_button', vendor, power_button),
  )

  @classmethod
  def create_from_form(cls, form, rack_id):
    return cls(
      name = form.name.data,
      serial_number = form.serial_number.data,
      product_number = form.product_number.data,
      login = form.login.data,
      category = server_type[form.category.data],
      vendor = vendor[form.vendor.data],
      top_unit = form.top_unit.data,
      bottom_unit = form.bottom_unit.data,
      power_button = form.power_button.data,
      power_button_ip = form.power_button_ip.data,
      monday_on = form.monday_on.data,
      friday_off = form.friday_off.data,
      rack_id = rack_id
    )
  
  def update_from_form(self, form):
    self.name = form.name.data
    self.serial_number = form.serial_number.data
    self.product_number = form.product_number.data
    self.login = form.login.data
    self.category = server_type[form.category.data]
    self.vendor = vendor[form.vendor.data]
    self.top_unit = form.top_unit.data
    self.bottom_unit = form.bottom_unit.data
    self.power_button = form.power_button.data
    self.power_button_ip = form.power_button_ip.data
    self.monday_on = form.monday_on.data
    self.friday_off = form.friday_off.data

  def __repr__(self):
    return f'<Server {self.name}>'
  
class ServerIP(db.Model):
  id: so.Mapped[int] = so.mapped_column(primary_key=True)
  category: so.Mapped[ip_type] = so.mapped_column(sa.Enum(ip_type), nullable=False)
  label: so.Mapped[str] = so.mapped_column(sa.String(45), default='')
  ip: so.Mapped[str] = so.mapped_column(sa.String(45), default='')
  server_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Server.id), index=True)

  server: so.Mapped[Server] = so.relationship(back_populates='ips')

  def __repr__(self):
    return f'<Server IP {self.label}: {self.ip}>'