import os, csv
from flask import Flask, redirect, render_template, request, flash, url_for
from sqlalchemy.exc import OperationalError, IntegrityError
from App.models import db, User, Student, Review
from datetime import timedelta
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    current_user,
    set_access_cookies,
    unset_jwt_cookies,
)

def create_app():
  app = Flask(__name__, static_url_path='/static')
  CORS(app)
  app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
  app.config['TEMPLATES_AUTO_RELOAD'] = True
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'data.db')
  app.config['DEBUG'] = True
  app.config['SECRET_KEY'] = 'MySecretKey'
  app.config['PREFERRED_URL_SCHEME'] = 'https'
  app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
  app.config['JWT_REFRESH_COOKIE_NAME'] = 'refresh_token'
  app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
  app.config["JWT_COOKIE_SECURE"] = True
  app.config["JWT_SECRET_KEY"] = "super-secret"
  app.config["JWT_COOKIE_CSRF_PROTECT"] = False
  app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

  app.app_context().push()
  return app

app = create_app()
db.init_app(app)

jwt = JWTManager(app)

@jwt.user_identity_loader
def user_identity_lookup(user):
  return str(user)  

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
  return User.query.get(jwt_data["sub"])

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
  flash("Your session has expired. Please log in again.")
  return redirect(url_for('login'))

def parse_students():
  with open('students.csv', mode='r', encoding='utf-8') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
      student = Student(id=row['ID'],
                        first_name=row['FirstName'],
                        image=row['Picture'],
                        last_name=row['LastName'],
                        programme=row['Programme'],
                        start_year=row['YearStarted'])
      db.session.add(student)
    db.session.commit()

def create_reviews():
  review1 = Review(student_id='820321819', user_id=1, text='This is a review 1', rating=4)
  review2 = Review(student_id='820321819', user_id=2, text='This is a review 2', rating=2)
  review3 = Review(student_id='820321819', user_id=3, text='This is a review 3', rating=3)
  review4 = Review(student_id='820321819', user_id=2, text='This is a review 4', rating=1)
  review5 = Review(student_id='820321819', user_id=1, text='This is a review 5', rating=4)
  db.session.add_all([review1, review2, review3, review4, review5])
  db.session.commit()

def create_users():
  rob = User(username="rob", password="robpass")
  bob = User(username="bob", password="bobpass")
  sally = User(username="sally", password="sallypass")
  pam = User(username="pam", password="pampass")
  chris = User(username="chris", password="chrispass")
  db.session.add_all([rob, bob, sally, pam, chris])
  db.session.commit()

def initialize_db():
  db.drop_all()
  db.create_all()
  create_users()
  parse_students()
  create_reviews()
  print('database initialized')

@app.route('/')
def login():
  return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_action():
  username = request.form.get('username')
  password = request.form.get('password')
  user = User.query.filter_by(username=username).first()
  if user and user.check_password(password):
    response = redirect(url_for('home'))
    access_token = create_access_token(identity=str(user.id))
    set_access_cookies(response, access_token)
    return response
  else:
    flash('Invalid username or password')
    return redirect(url_for('login'))

@app.route('/app')
@app.route('/app/<student_id>')
@jwt_required()
def home(student_id="820321819"):
  students = Student.query.all()
  selected_student = Student.query.get(student_id)
  reviews = Review.query.filter_by(student_id=student_id).all()

  avg_rating = None
  if reviews:
    avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 2)

  return render_template('index.html',
                         students=students,
                         selected_student=selected_student,
                         reviews=reviews,
                         avg_rating=avg_rating,
                         user=current_user)

@app.route('/review', methods=['POST'])
@jwt_required()
def submit_review():
  student_id = request.form.get('student_id')
  rating = int(request.form.get('rating'))
  text = request.form.get('text')

  review = Review(student_id=student_id, user_id=current_user.id, text=text, rating=rating)
  db.session.add(review)
  db.session.commit()
  flash("Review submitted.")
  return redirect(url_for('home', student_id=student_id))

@app.route('/delete/<int:review_id>/<student_id>')
@jwt_required()
def delete_review(review_id, student_id):
  review = Review.query.get(review_id)
  if review and review.user_id == current_user.id:
    db.session.delete(review)
    db.session.commit()
    flash("Review deleted.")
  else:
    flash("You can only delete your own reviews.")
  return redirect(url_for('home', student_id=student_id))

@app.route('/logout')
def logout():
  response = redirect(url_for('login'))
  unset_jwt_cookies(response)
  flash('logged out')
  return response

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080, debug=True)
