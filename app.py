from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.sqlite3')
db = SQLAlchemy(app)
app.app_context().push()

class Student(db.Model):
    __tablename__ = 'student'
    student_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    roll_number = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String)
    courses= db.relationship("Course", backref= "student", secondary = "enrollments" )

class Course(db.Model):
    __tablename__ = 'course'
    course_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_code = db.Column(db.String, unique=True, nullable=False)
    course_name = db.Column(db.String, nullable=False)
    course_description = db.Column(db.String)

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    enrollment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    estudent_id = db.Column(db.Integer, db.ForeignKey('student.student_id'), nullable=False)
    ecourse_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)


@app.route('/')
def index():
    students = Student.query.all()
    return render_template("home.html", students=students)

@app.route('/student/create', methods=['GET', 'POST'])
def add_student():
    if request.method == 'GET':
        return render_template('add.html')
    if request.method == 'POST':
        roll_number = request.form['roll']
        first_name = request.form['f_name']
        last_name = request.form['l_name']
        student = Student(roll_number=roll_number, first_name=first_name, last_name=last_name)

        if Student.query.filter_by(roll_number=roll_number).first():
            return render_template('dup.html')

        try:
            db.session.add(student)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
        return redirect('/')

@app.route('/student/<int:student_id>/update', methods=['GET', 'POST'])
def update_student(student_id):
    student = Student.query.get(student_id)
    courses=Course.query.all()
    if request.method == 'GET':
        return render_template('update.html', student=student,courses=courses)
    if request.method == 'POST':
        try:
            student.first_name = request.form['f_name']
            student.last_name = request.form['l_name']
            db.session.commit()
            course_ids = request.form.getlist('course')
            for course_id in course_ids:
                enroll = Enrollment(estudent_id=student.student_id, ecourse_id=course_id)
                db.session.add(enroll)
            db.session.commit()
        except Exception as e:
            db.session.rollback()

        return redirect("/")
    
@app.route('/student/<int:student_id>/delete')
def delete_student(student_id):
    student = Student.query.get(student_id)
    Enrollment.query.filter_by(estudent_id=student_id).delete()
    try:
        db.session.delete(student)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    return redirect("/")

@app.route('/student/<int:student_id>')
def details(student_id):
    student = Student.query.get(student_id)
    courses= student.courses
    return render_template("details.html", student=student, courses=courses)
@app.route('/student/<int:student_id>/withdraw/<int:course_id>')
def withdraw(student_id,course_id):
    enrollment = Enrollment.query.filter_by(estudent_id=student_id, ecourse_id=course_id).first()
    db.session.delete(enrollment)
    db.session.commit()
    return redirect("/")
@app.route('/courses')
def courses():
    courses = Course.query.all()
    return render_template("home_c.html", courses=courses) 

@app.route('/course/create', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        code = request.form['code']
        a=db.session.query(Course).filter(Course.course_code == code).first()
        if a :
            return render_template('dup_c.html')
        else:
            name = request.form['c_name']
            desc = request.form['desc']
            course = Course(course_code=code, course_name=name, course_description=desc)
            db.session.add(course)
            db.session.commit()
        return redirect('/courses')
    return render_template('add_c.html')


@app.route('/course/<int:course_id>/update', methods=['GET', 'POST'])
def c_update(course_id):
    course=Course.query.get(course_id)
    if request.method=='GET':
        return render_template('update_c.html',course=course)
    if request.method=='POST':
        course.course_name=request.form['c_name']
        course.course_description=request.form['desc']
        db.session.commit()
        return redirect('/courses')

@app.route('/course/<int:course_id>/delete')
def c_delete(course_id):
    course=Course.query.get(course_id)
    Enrollment.query.filter_by(ecourse_id=course_id).delete()
    db.session.delete(course)
    db.session.commit()
    return redirect('/courses')

@app.route('/course/<int:course_id>')
def c_details(course_id):
    course=Course.query.get(course_id)
    enrollments = Enrollment.query.filter_by(ecourse_id=course_id).all()
    student_ids = [enrollment.estudent_id for enrollment in enrollments]
    students = Student.query.filter(Student.student_id.in_(student_ids)).all()
    return render_template('details_c.html', course=course, students=students)


if __name__ == '__main__':
    app.run(debug=True)
