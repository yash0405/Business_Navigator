from . import db   # . means importing package from the website folder
from flask_login import UserMixin   # this helps user in logging in
from sqlalchemy.sql import func 
import datetime

class Inventory(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    quantity = db.Column(db.String)
    price = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    location= db.Column(db.String(50))
    shop_name = db.Column(db.String(100))
    contact= db.Column(db.String(10))   
    inventory = db.relationship('Inventory')
    def get_id(self):
        return 'User|' + str(self.id)

class Consumer(db.Model, UserMixin):
    consumer_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    contact= db.Column(db.String(10))
    def get_id(self):
        return 'Consumer|' + str(self.consumer_id)

class Debt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item=db.Column(db.String(50))
    amount = db.Column(db.String(10))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    shopkeeper_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    shopkeeper = db.relationship('User', backref=db.backref('debts', lazy=True))
    consumer_id = db.Column(db.Integer, db.ForeignKey('consumer.consumer_id'))
    consumer = db.relationship('Consumer', backref=db.backref('debts', lazy=True))

class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shopkeeper_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    consumer_id = db.Column(db.Integer, db.ForeignKey('consumer.consumer_id'))
    shopkeeper = db.relationship('User', foreign_keys=[shopkeeper_id], backref=db.backref('connections', lazy='dynamic'))
    consumer = db.relationship('Consumer', foreign_keys=[consumer_id], backref=db.backref('connected_to', lazy='dynamic'))

    