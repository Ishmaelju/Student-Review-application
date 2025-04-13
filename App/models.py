from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  password = db.Column(db.String(120), nullable=False)

  def __init__(self, username, password):
    self.username = username
    self.set_password(password)

  def set_password(self, password):
    self.password = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.password, password)
    
class Student(db.Model):
  id = db.Column(db.String(9), primary_key=True)
  first_name = db.Column(db.String(80))
  last_name = db.Column(db.String(80))
  programme = db.Column(db.String(80))
  start_year = db.Column(db.Integer)
  image = db.Column(db.String(120))
  reviews = db.relationship('Review', backref='student', lazy=True)

class Review(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  student_id = db.Column(db.String(9), db.ForeignKey('student.id'), nullable=False)
  text = db.Column(db.Text, nullable=False)
  rating = db.Column(db.Integer, nullable=False)
  user = db.relationship('User', backref='reviews')
