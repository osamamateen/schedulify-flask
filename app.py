from flask import Flask, render_template, request, redirect, url_for, session, logging, flash
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField
from passlib.hash import sha256_crypt
from functools import wraps
import math
import time
import os
import csv
from os.path import join, dirname, realpath
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
import datetime
from pprint import pprint
import logging
import sys
from sqlalchemy import create_engine



engine = create_engine('mysql://root:root@localhost/schedulify-flask')
connection = engine.raw_connection()
cursor = connection.cursor()

app = Flask(__name__)

logger = logging.getLogger('werkzeug')  # grabs underlying WSGI logger
handler = logging.FileHandler('test.log')  # creates handler for the log file
logger.addHandler(handler)  # adds handler to the werkzeug WSGI logger

app.secret_key = '1231231'

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'schedulify-flask'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/schedulify-flask'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# init MySQL
mysql = MySQL(app)
db = SQLAlchemy(app)


class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), nullable=False, unique=True)
    faculty_code = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(255))
    register_date = db.Column(db.DateTime)
    role = db.Column(db.Boolean, nullable=False)
    status = db.Column(db.Boolean, default=0)
    deleted = db.Column(db.Boolean, default=0)
    username = db.Column(db.String(255), nullable=False)

    def __init__(self, name, email, faculty_code, password, register_date, role, status, deleted):
        self.name = name
        self.email = email
        self.faculty_code = faculty_code
        self.password = password
        self.register_date = register_date
        self.role = role
        self.status = status
        self.deleted = deleted


class CourseRequests(db.Model):
    __tablename__ = "course_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_code = db.Column(db.String(255), nullable=False)
    course_title = db.Column(db.String(255))
    semester = db.Column(db.Integer)
    slot = db.Column(db.Integer)
    day = db.Column(db.Integer)
    created_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow(), nullable=False)
    deleted = db.Column(db.Boolean, default=0)
    approved = db.Column(db.Boolean, default=0)

    def __init__(self, name, email, course_code, course_title, semester, slot, day, created_at, approved, deleted):
        self.name = name
        self.email = email
        self.course_code = course_code
        self.course_title = course_title
        self.semester = semester
        self.slot = slot
        self.day = day
        self.created_at = created_at
        self.approved = approved
        self.deleted = deleted

# Check if user logged in


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route('/')
@is_logged_in
def index():
    userRequests = Users.query.filter_by(status=0).all()

    cur = mysql.connection.cursor()

    # cursor.execute("SELECT * FROM users WHERE status = 0")

    # userRequests = cursor.fetchall()
    # commit to DB

    # CourseRequests = CourseRequests.query.join(
    #     Users).filter(CourseRequests.user_id == Users.id).all()

    courseRequests = cur.execute(
        "SELECT * FROM course_requests LEFT JOIN users ON course_requests.user_id = users.id")

    courseRequests = cur.fetchall()
    # courseRequests = ["hello"]

    mysql.connection.commit()
    # close connection
    # cursor.close()

    logger.info("here")
    logger.info(print(courseRequests))
    # logger.info(courseRequests)

    # print("You are in index")

    return render_template('index.html', userRequests=userRequests, courseRequests=courseRequests)


@app.route('/faculty', methods=['GET', 'POST'])
def faculty():
    faculty = Users.query.all()

    return render_template('faculty-listing.html', faculty=faculty)


# @app.route('faculty/insert', methods=['POST'])
# def insertFaculty():
#     if request.method == 'POST':

class courseRequestForm(Form):
    course_code = StringField('Course Code', validators=[
        validators.input_required(), validators.Length(min=6, max=6)])
    course_title = StringField('Course Title', validators=[
        validators.Length(min=4, max=25)])
    semester = SelectField(u'Semester', choices=[(1, 'First'), (2, 'Second'), (3, 'Third'), (
        4, 'Fourth'), (5, 'Fifth'), (6, 'Sixth'), (7, 'Seventh'), (8, 'Eighth')])
    # semester = StringField('Semester', validators=[
    # validators.input_required(), validators.Length(min=1, max=1)])
    day = SelectField(u'Day', choices=[(1, 'Mon-Wed'), (2, 'Tue-Thu'), (3, 'Sat'), (
        4, 'Sun')])
    # day = StringField('Day', validators=[
    #     validators.input_required(), validators.Length(min=1, max=1)])
    slot = SelectField(u'Slot', choices=[(1, 'First'), (2, 'Second'), (3, 'Third'), (
        4, 'Fourth')])
    # slot = StringField('Slot', validators=[
    #     validators.Length(min=1, max=1)])


@app.route('/course-request', methods=['GET', 'POST'])
def courseRequest():
    logger.info(session['id'])
    form = courseRequestForm(request.form)
    if request.method == 'POST' and form.validate():
        course_code = form.course_code.data
        course_title = form.course_title.data
        semester = form.semester.data
        day = form.day.data
        slot = form.slot.data
        user_id = session['id']

        # create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO course_requests(user_id, course_code, course_title, semester, day, slot) VALUES(%s,%s, %s, %s, %s,%s)",
                    (user_id, course_code, course_title, semester, day, slot))

        # commit to DB
        mysql.connection.commit()

        # close connection
        cur.close()

        flash('Your request has been submitted.', 'success')

        return redirect(url_for('index'))
    return render_template('course-request.html', form=form)


# @app.route('/course-request-listing', methods=['GET', 'POST'])
# def courseRequestListing():
#     courseRequests = CourseRequests.query.all()


@app.route('/scheduler', methods=['GET', 'POST'])
def scheduler():
    with open('schedule.csv') as f:
        result = [{k: v for k, v in row.items()}
                  for row in csv.DictReader(f, skipinitialspace=True)]
    return render_template('scheduler.html', result=result)


UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/upload', methods=['POST'])
def upload():
    if request.files:
        csvFile = request.files['upload-file']
        csvFile.filename = 'data.csv'
        path = os.path.join(app.config['UPLOAD_FOLDER'], csvFile.filename)
        csvFile.save(path)

        print("SAVED")
    else:
        print('no file')
    return redirect(url_for('scheduler'))


# read csv file and save it to dictionary
fileName = 'uploads/data2.csv'
f = open(fileName, 'r', errors="ignore")
reader = csv.reader(f)
coursesData = {}
for row in reader:
    coursesData[row[0]] = {'faculty': row[1], 'semester': row[2]}

# courses data by faculty name
courses = sorted(coursesData, key=lambda x: (coursesData[x]['faculty']))

# Register form class


class RegisterForm(Form):
    name = StringField('Name', validators=[
                       validators.input_required(), validators.Length(min=1, max=50)])
    username = StringField('Username', validators=[
                           validators.input_required(), validators.Length(min=4, max=25)])
    email = StringField('Email', validators=[
                        validators.input_required(), validators.Length(min=6, max=50)])
    password = PasswordField('Password', validators=[
        validators.input_required(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    role = SelectField('Role', choices=[('1', 'Faculty'), ('2', 'Coordinator')], validators=[validators.input_required()])

    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        role = form.role.data
        password = sha256_crypt.encrypt(str(form.password.data))
# remove this later
        faculty_code = username
        # create cursor
        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name, email, username, password, role, faculty_code, deleted) VALUES(%s, %s, %s, %s, %s, %s, %s)", (name, email, username, password, role, faculty_code ,0))

        # commit to DB
        mysql.connection.commit()

        # close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# user login


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        # create a cursor
        cur = mysql.connection.cursor()

        # get user by username
        result = cur.execute(
            "SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # get stored hash
            data = cur.fetchone()
            password = data['password']

            # compare passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
                session['id'] = data['id']

                flash('You are now logged in', 'success')
                return redirect(url_for('index'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
            # close connection
            cur.close()

        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')


# logout


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    logger.info("session cleared")
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


# initialize variables
board = []
day1 = []
day2 = []
day3 = []
day4 = []
slot_len = math.ceil((len(courses)/4)/4)
assigned_courses = []
previous_courses = []
result = []
k = 0

# create an empty board with -- representing an emoty slot


def create_board(num_of_courses):
    x = math.ceil(slot_len * 4)
    for slot in range(x):
        day1.append("--")
        day2.append("--")
        day3.append("--")
        day4.append("--")
    board.append(day1)
    board.append(day2)
    board.append(day3)
    board.append(day4)

# custom function to print the board neatly
def print_board():
    for i in range(len(board)):
        print("Day", i, end="       | ")
        for j in range(len(board[i])):
            if j % slot_len == 0 and j != 0:
                print(" | ", end="")
            print(board[i][j], end="")
        print("")


# check if the course is valid for the current slot
def valid(thisCourse, thisDay, thisSlot):
    global previous_courses
    # if the courses in the slot have reached the max length of slot then empty the temp variable to keep track of courses in the slot
    if(len(previous_courses) == slot_len):
        previous_courses = []

    # if the course is already assigned return false
    if thisCourse in assigned_courses:
        return False

    # check the slot being assigned a course
    if thisSlot % slot_len != 0 and thisSlot != 0:

        # iterate over all the courses in the current slot
        for prevCourse in previous_courses:
            # if there is an empty space return true
            if prevCourse == "--":
                return True
            # if the faculty of this course is the same as the faculty of any other course in this slot return false
            if coursesData[prevCourse]["faculty"] == coursesData[thisCourse]["faculty"]:
                return False

            # if there is already a course of the same semester in this slot return false
            if coursesData[prevCourse]["semester"] == coursesData[thisCourse]["semester"]:
                return False
    return True


# find an empty space in the board
def find_empty(board):
    for row in range(len(board)):
        for col in range(len(board[0])):
            # if the position is empty denoted by -- then return the position
            if board[row][col] == "--":
                return (row, col)
    # if there is no empty space return none
    return None


def solve(board, courses, k):
    if (k >= len(courses)):
        return True
    if len(courses) == len(assigned_courses):
        return True
    if not find_empty(board):
        return True
    else:
        pos = find_empty(board)
        row = pos[0]
        col = pos[1]
        for i in range(k, len(courses)):
            thisCourse = list(courses)[i]
            if(valid(thisCourse, row, col)):
                board[row][col] = thisCourse
                if(row < 2):
                    if(col >= 0 and col < len(board[row])/4):
                        slot = 1
                    if(col >= len(board[row])/4 and col < len(board[row])/2):
                        slot = 2
                    if(col >= len(board[row])/2 and col < (len(board[row]) * 3/4)):
                        slot = 3
                    if(col >= (len(board[row]) * 3/4) and col < len(board[row])):
                        slot = 4
                else:
                    board[row][col+1] = "x"
                    if(col >= 0 and col < len(board[row])/4):
                        slot = 1
                    if(col >= len(board[row])/4 and col < len(board[row])/2):
                        slot = 1
                    if(col >= len(board[row])/2 and col < (len(board[row]) * 3/4)):
                        slot = 2
                    if(col >= (len(board[row]) * 3/4) and col < len(board[row])):
                        slot = 2 

                course_detail = {
                    'course': thisCourse,
                    'faculty': coursesData[thisCourse]["faculty"],
                    'semester': coursesData[thisCourse]["semester"],
                    'slot': slot,
                    'day': row
                }
                previous_courses.append(thisCourse)
                assigned_courses.append(thisCourse)
                result.append(course_detail)
                isSolved = solve(board, courses, k + 1)
                if (isSolved == True):
                    return True
                assigned_courses.pop()
                result.pop()
                k = k - 1
                board[row][col] = "--"
        return False


@app.route('/generate', methods=['GET'])
def generate():
    started = time.time()
    create_board(len(courses))
    solve(board, courses, k)
    print_board()
    print("Solution Found: ", solve(board, courses, k))
    completed = time.time()
    print("Time Taken: ", completed - started)
    toCSV = result
    keys = toCSV[0].keys()
    with open('schedule.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(toCSV)
    return redirect(url_for('scheduler'))


if __name__ == '__main__':
    app.run(debug=True)
