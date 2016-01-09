# Run this!

from flask import Flask, g, render_template, request

from peewee import *
from playhouse.postgres_ext import *
from wtfpeewee.orm import model_form

from data_model import *



# CONFIGURATION

DATABASE = "hiuni_database"
USER = "Andrew"
DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)

database = PostgresqlExtDatabase(DATABASE)



# REQUEST HANDLERS
# Apparently this is all I really needed from flask-peewee.

@app.before_request
def before_request():
	g.db = database
	g.db.connect()


@app.after_request
def after_request(response):
	g.db.close()
	return response



# FORMS

# def create_forms():
Student_Form = model_form(Student, exclude = ("location", "career"))
Career_Form = model_form(Career, exclude = ("nicknames",))
print "Successfully made forms..."


# VIEWS

@app.route("/")
@app.route("/index")
def index():
	student = Student.select().where(Student.name == "Jonathan Turpen").get()

	return render_template("index.html", title = "Home", student = student)


@app.route("/report/<student_id>")
def report(student_id):
	try:
		student = Student.get(id = student_id)
	except Student.DoesNotExist:
		abort(404)

	pathways = Pathway.select().where(Pathway.student == student)

	return render_template("report.html", title = student.name + "'s Report", student = student, pathways = pathways)


@app.route("/questions", methods = ['GET', 'POST'])
def questions():
	student = Student()

	if request.method == "POST":
		form = Student_Form(request.form, obj = student)
		
		if form.validate():
			form.populate_obj(student)
			student.save()

	else:
		form = Student_Form(obj = student)

	return render_template("questions.html", form = form, student = student)



# RUN IT

def create_tables():
	School.create_table(True)
	Program.create_table(True)
	Career.create_table(True)
	Student.create_table(True)
	Recipe.create_table(True)
	Step.create_table(True)
	Pathway.create_table(True)
	Pathway_Step.create_table(True)


if __name__ == '__main__':
    create_tables()
    # create_forms()
    app.run()