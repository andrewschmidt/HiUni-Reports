# Run this!

from flask import Flask, g, render_template, request, abort, flash

from peewee import *
from playhouse.postgres_ext import *

from flask.ext.wtf import Form
from wtforms.fields import StringField, SelectField
from wtforms.validators import DataRequired, Email

from wtfpeewee.orm import model_form # For modeling forms from database objects. Not sure I really need it.

from data_model import *



# CONFIGURATION

# Database config:
DATABASE = "hiuni_database"
USER = "Andrew"
DEBUG = True

# Forms config:
WTF_CSRF_ENABLED = True
SECRET_KEY = 'secret'

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

class Questionnaire_Form(Form):
	first_name = StringField("First name:")
	last_name = StringField("Last name:")

	email = StringField("Email:")

	careers = Career.select()
	career_choices = [(None, "")]
	for career in careers:
		career_choices.append((career.name, career.name))
	career = SelectField("Career:", choices = career_choices)

	income_levels = ["0-30,000", "30,001-48,000", "48,001-75,000", "75,001-110,000", "over 110,000"]
	income_choices = [(None, "")]
	for level in income_levels:
		if level == "over 110,000":
			income_choices.append((level, "Over $110,000"))
		else:
			income_choices.append((level, "$"+level))
	income = SelectField("What's your family's income level?", choices = income_choices)

	budget = StringField("What's your budget for higher education? $")

	city = StringField("What city do you live in?")
	state = StringField("What state do you live in?")



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
	form = Questionnaire_Form()

	if form.validate_on_submit():
		flash("Validated!")

		student = Student()
		
		student.name = form.first_name.data + " " + form.last_name.data
		student.email = form.email.data
		student.career = Career.get(Career.name == form.career.data)
		student.income = form.income.data
		student.budget = int(form.budget.data)
		student.city = form.city.data
		student.state = form.state.data

		flash("Saving the student...")
		student.save()
		flash("Saved!")
	
	if len(form.errors) > 0:
		for error in form.errors:
			flash(error)

	return render_template("questions.html", form = form)



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
    app.run()