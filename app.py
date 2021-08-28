from flask import Flask, render_template, request, redirect, url_for, session, logging, flash
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField, HiddenField
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
from datetime import datetime
from pprint import pprint
import logging
import sys
from sqlalchemy import create_engine
import mysql.connector
from flask import send_file
# solver imports
from helpers import getSlots
from helpers import findUnassignedCourse
from helpers import fillSlots
from helpers import populatePreAsigned
from helpers import validate

app = Flask(__name__)

logger = logging.getLogger('werkzeug')  # grabs underlying WSGI logger
handler = logging.FileHandler('test.log')  # creates handler for the log file
logger.addHandler(handler)  # adds handler to the werkzeug WSGI logger

app.secret_key = '1231231'


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/schedulify-flask'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Users(db.Model):
    # __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), nullable=False, unique=True)
    faculty_code = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(255))
    register_date = db.Column(db.DateTime)
    role = db.Column(db.String(1), nullable=False)
    status = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)

    def __init__(self, name, email, faculty_code, password, register_date, role, status, deleted, **kwargs):
        super(Users, self).__init__(**kwargs)
        self.name = name
        self.email = email
        self.faculty_code = faculty_code
        self.password = password
        self.register_date = register_date
        self.role = role
        self.status = status
        self.deleted = deleted


class CourseRequests(db.Model):
    # __tablename__ = "course_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user_name = db.Column(db.String(255), nullable=False)
    course_code = db.Column(db.String(255), nullable=False)
    course_title = db.Column(db.String(255))
    semester = db.Column(db.Integer)
    slot = db.Column(db.Integer)
    day = db.Column(db.Integer)
    created_at = db.Column(
        db.DateTime, nullable=False)
    deleted = db.Column(db.Boolean, default=0)
    approved = db.Column(db.Boolean, default=0)

    def __init__(self, user_id, user_name, course_code, course_title, semester, slot, day, created_at, deleted, approved, **kwargs):
        super(CourseRequests, self).__init__(**kwargs)
        self.user_id = user_id
        self.user_name = user_name
        self.course_code = course_code
        self.course_title = course_title
        self.semester = semester
        self.slot = slot
        self.day = day
        self.created_at = created_at
        self.deleted = deleted
        self.approved = approved

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


def is_logged_in_index(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap


@app.route('/')
@is_logged_in_index
def index():
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
@is_logged_in
def dashboard():
    userRequests = Users.query.filter(Users.status == 0).all()

    activeFaculty = Users.query.filter(Users.status == 1).all()
    activeFaculty = len(activeFaculty)

    approved_requests = CourseRequests.query.filter(
        (CourseRequests.approved == 1) & (CourseRequests.deleted == 0)).all()

    course_requests = CourseRequests.query.filter(
        (CourseRequests.deleted != 1) & (CourseRequests.approved == 0)).all()

    user_id = session['id']
    user_course_requests = CourseRequests.query.filter(
        (CourseRequests.approved == 0) & (CourseRequests.deleted == 0) & (CourseRequests.user_id == user_id)).all()

    logger.info("here")

    if session['role'] != '2':
        return render_template('faculty-dashboard.html', courseRequests=user_course_requests)
    else:
        return render_template('admin-dashboard.html', activeFaculty=activeFaculty, userRequests=userRequests, approvedRequests=approved_requests, courseRequests=course_requests)


@app.route('/delete-course/<id>', methods=['GET', 'POST'])
@is_logged_in
def deleteCourse(id):
    delete_course = CourseRequests.query.get(id)
    delete_course.deleted = 1
    db.session.commit()
    flash('Course Request Deleted Successfully')
    return redirect(request.referrer)


@app.route('/approve-course/<id>', methods=['GET', 'POST'])
@is_logged_in
def approveCourse(id):
    approve_course = CourseRequests.query.get(id)
    approve_course.approved = 1
    db.session.commit()
    flash('Course Request Approved Successfully')
    return redirect(request.referrer)


@app.route('/disapprove-course/<id>', methods=['GET', 'POST'])
@is_logged_in
def disapproveCourse(id):
    disapprove_course = CourseRequests.query.get(id)
    disapprove_course.approved = 0
    db.session.commit()
    flash('Course Request Disapproved Successfully')
    return redirect(request.referrer)


@app.route('/delete-faculty/<id>', methods=['GET', 'POST'])
@is_logged_in
def deleteFaculty(id):
    delete_faculty = Users.query.get(id)
    db.session.delete(delete_faculty)
    db.session.commit()

    flash('Faculty Request Deleted Successfully', 'success')

    return redirect(request.referrer)


@app.route('/approve-faculty/<id>', methods=['GET', 'POST'])
@is_logged_in
def approveFaculty(id):
    approve_faculty = Users.query.get(id)
    approve_faculty.status = 1
    db.session.commit()

    flash('Faculty Request Approved Successfully', 'success')

    return redirect(request.referrer)


@app.route('/faculty-listing', methods=['GET', 'POST'])
def facultyListing():
    faculty = Users.query.filter((Users.status == 1) & (
        Users.deleted == 0) & (Users.role == 1)).all()
    return render_template('faculty-listing.html', faculty=faculty)


class courseRequestForm(Form):
    course_code = StringField('Course Code', validators=[
        validators.input_required(), validators.Length(min=6, max=6)])
    course_title = StringField('Course Title', validators=[
        validators.Length(min=4, max=25)])
    semester = SelectField(u'Semester', choices=[(1, 'First'), (2, 'Second'), (3, 'Third'), (
        4, 'Fourth'), (5, 'Fifth'), (6, 'Sixth'), (7, 'Seventh'), (8, 'Eighth')])
    day = SelectField(u'Day', choices=[(1, 'Mon-Wed'), (2, 'Tue-Thu'), (3, 'Sat'), (
        4, 'Sun')])
    slot = SelectField(u'Slot', choices=[(1, 'First'), (2, 'Second'), (3, 'Third'), (
        4, 'Fourth')])
    approved = HiddenField()


@app.route('/course-requests', methods=['GET', 'POST'])
@is_logged_in
def courseRequest():
    approved_requests = CourseRequests.query.filter(
        (CourseRequests.approved == 1) & (CourseRequests.deleted == 0)).all()

    course_requests = CourseRequests.query.filter(
        (CourseRequests.approved == 0) & (CourseRequests.deleted == 0)).all()

    form = courseRequestForm(request.form)
    if request.method == 'POST' and form.validate():

        user_id = session['id']
        user_name = session['name']
        course_code = form.course_code.data
        course_title = form.course_title.data
        semester = form.semester.data
        slot = form.slot.data
        day = form.day.data
        created_at = 'dummy-date'
        deleted = 0

        if session['role'] == '2':
            approved = 1
        else:
            approved = 0

        course_request = CourseRequests(
            user_id, user_name, course_code, course_title, semester, slot, day, created_at, deleted, approved)
        db.session.add(course_request)
        db.session.commit()
        flash('Your request has been submitted.', 'success')

        return redirect(url_for('index'))

    if session['role'] == '2':
        return render_template('course-request-listing.html', form=form, courseRequests=course_requests, approvedRequests=approved_requests)
    else:
        return render_template('course-request.html', form=form, courseRequests=course_requests)


@app.route('/scheduler', methods=['GET', 'POST'])
def scheduler():
    with open('schedule.csv') as f:
        result = [{k: v for k, v in row.items()}
                  for row in csv.DictReader(f, skipinitialspace=True)]
    return render_template('scheduler.html', result=result, coursesAssigned=0, timeTaken=round(0, 1), violated=0, isSolved=False)


UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/upload', methods=['POST'])
def upload():
    if request.files:
        csvFile = request.files['upload-file']
        csvFile.filename = 'data.csv'
        path = os.path.join(app.config['UPLOAD_FOLDER'], csvFile.filename)
        csvFile.save(path)
        print("file saved")
    else:
        print('no file')
    return redirect(url_for('scheduler'))

# Register form class


class RegisterForm(Form):
    name = StringField('Name', validators=[
                       validators.input_required(), validators.Length(min=1, max=50)])
    faculty_code = StringField('Faculty Code', validators=[
        validators.input_required(), validators.Length(min=4, max=25)])
    email = StringField('Email', validators=[
                        validators.input_required(), validators.Length(min=6, max=50)])
    password = PasswordField('Password', validators=[
        validators.input_required(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    role = SelectField('Role', choices=[(
        1, 'Faculty'), (2, 'Coordinator')], validators=[validators.input_required()])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        faculty_code = request.form['faculty_code']
        password = sha256_crypt.encrypt(str(request.form['password']))
        register_date = request.form['faculty_code']
        role = request.form['role']
        status = 0
        deleted = 0
        register_data = Users(name, email, faculty_code, password, register_date, role,
                              status, deleted)
        db.session.add(register_data)
        db.session.commit()
        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html')

# user login


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # get form fields
        email = request.form['email']
        password_candidate = request.form['password']
        result = Users.query.filter(Users.email == email).first()
        if result:
            password = result.password

            # compare passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['email'] = email
                session['id'] = result.id
                session['name'] = result.name
                session['role'] = result.role
                session['status'] = result.status

                print(session['name'])

                flash('You are now logged in', 'success')
                return redirect(url_for('index'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)

        else:
            error = 'Email not found'
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


# ----------------------------SOLVER----------------------------------
# read csv file and save it to dictionary
fileName = 'uploads/data.csv'
f = open(fileName, 'r', errors="ignore")
reader = csv.reader(f)
next(reader)
coursesData = {}

for row in reader:
    if(row):
        coursesData[row[0]] = {'title': row[1], 'faculty': row[2],
                               'semester': row[3].split(' '), 'slot': row[4]}
courses = sorted(coursesData, key=lambda x: (coursesData[x]['faculty']))

courseLimit = math.ceil(len(courses)/12)
slots = getSlots()

preAssigned = []
constraintsviolated = []
result = []


def solve(courses, courseData, slots):
    if not findUnassignedCourse(courses, coursesData):
        return True
    course = findUnassignedCourse(courses, coursesData)
    for slot in slots.keys():
        count = slots[slot]['count']
        if(validate(slot, course, count, courseLimit, coursesData, slots)):
            coursesData[course]['slot'] = slot
            slots[slot]['count'] = slots[slot]['count'] + 1
            slots[slot]['faculty'].append(coursesData[course]['faculty'])
            for semester in coursesData[course]['semester']:
                slots[slot]['semester'].append(semester)
            course_detail = {
                'course': course,
                'title': coursesData[course]["title"],
                'faculty': coursesData[course]["faculty"],
                'semester': ' '.join(map(str, coursesData[course]["semester"])),
                'slot': slot,
            }
            result.append(course_detail)
            isSolved = solve(courses, courseData, slots)
            if (isSolved == True):
                return True
            else:
                coursesData[course]['slot'] = ''
                slots[slot]['count'] = slots[slot]['count'] - 1
                slots[slot]['faculty'].remove(coursesData[course]['faculty'])
                for semester in coursesData[course]['semester']:
                    slots[slot]['semester'].remove(semester)
                result.remove(course_detail)
                constraintsviolated.append(course)

    return False


@app.route('/generate', methods=['GET'])
def generate():
    started = time.time()
    fillSlots(courses, coursesData, slots)
    populatePreAsigned(courses, coursesData, preAssigned)
    isSolved = solve(courses, coursesData, slots)
    completed = time.time()
    coursesAssigned = len(result)
    if(completed and started):
        timeTaken = completed - started
    else:
        timeTaken = 0
    print(completed - started)
    violated = len(constraintsviolated)
    toCSV = result
    keys = toCSV[0].keys()
    with open('schedule.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(toCSV)
    with open('schedule.csv') as f:
        savedSolution = [{k: v for k, v in row.items()}
                         for row in csv.DictReader(f, skipinitialspace=True)]
    return render_template('scheduler.html', result=savedSolution, coursesAssigned=coursesAssigned, timeTaken=float("{:.2f}".format(timeTaken * 100)), violated=violated, isSolved=isSolved)


if __name__ == '__main__':
    # app.run(host="schedulify", port=8000, debug=True)
    app.run(debug=True)
