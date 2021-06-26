from flask import Flask, render_template, request, redirect, url_for, session, logging, flash
import os
import csv
from os.path import join, dirname, realpath
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import math
import time 
app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'schedulify-flask'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init MySQL
mysql = MySQL(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    with open('schedule.csv') as f:
        result = [{k: v for k, v in row.items()}
            for row in csv.DictReader(f, skipinitialspace=True)]
    return render_template('index.html', result = result)

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
    return redirect(url_for('index'))



# read csv file and save it to dictionary
fileName = 'uploads/data.csv'
f = open(fileName, 'r')
reader = csv.reader(f)
coursesData = {}
for row in reader:
    coursesData[row[0]] = {'faculty': row[1], 'semester': row[2]}

# courses data by faculty name
courses = sorted(coursesData, key=lambda x: (coursesData[x]['faculty']))

# user login
@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    # get form fields
    username = request.form['username']
    password_candidate = request.form['password']
    
    #create a cursor
    cur = mysql.connection.cursor()

    #get user by username
    result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

    if result > 0:
      # get stored hash
      data = cur.fetchone()
      password = data['password']

      #compare passwords
      if sha256_crypt.verify(password_candidate, password):
        # Passed
        session['logged_in'] = True
        session['username'] = username
        flash('You are now logged in', 'success')
        return redirect(url_for('index'))
      else:
        error = 'Invalid Login'
        return render_template('login.html', error = error)
      #close connection
      cur.close()

    else:
      error = 'Username not found'
      return render_template('login.html', error = error)

  return render_template('login.html')

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

# logout
@app.route('/logout')
@is_logged_in 
def logout():
  session.clear()
  flash('You are now logged out', 'success')
  return redirect(url_for('login'))



# initialize variables
board = []
day1 = []
day2 = []
slot_len = math.ceil((len(courses)/2)/4)
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
    board.append(day1)
    board.append(day2)


# custom function to print the board neatly
def print_board():
    for i in range(len(board)):
        print("Day", i, end="       | ")
        for j in range(len(board[i])):
            if j % slot_len == 0 and j != 0:
                print(" | ", end="")
            print(board[i][j], "-", coursesData[board[i][j]]
                  ['faculty'], "-", coursesData[board[i][j]]
                  ['semester'], end="")
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
                if(col >= 0 and col < len(board[row])/4):
                    slot = 1
                if(col >= len(board[row])/4 and col < len(board[row])/2):
                    slot = 2
                if(col >= len(board[row])/2  and col < (len(board[row])* 3/4)):
                    slot = 3
                if(col >= (len(board[row]) * 3/4)  and col < len(board[row])):
                    slot = 4
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
    with open('schedule.csv', 'w', newline='')  as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(toCSV)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)