# Run this!

from flask import Flask, g, render_template, redirect, request, abort, flash, session

from peewee import *
from playhouse.postgres_ext import *

from flask.ext.wtf import Form
from wtforms.fields import StringField, SelectField
from wtforms.fields.html5 import EmailField
from wtforms.validators import Email, Required

from wtfpeewee.fields import SelectQueryField # Unlike a regular SelectField, this returns actual model classes.
from wtfpeewee.orm import model_form # For modeling forms from database objects. Not sure I really need it.

from data_model import * # Includes the "database" variable.
import solver



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
	# Let's hardcode some data.
	# First, income levels:
	income_levels = ["0-30,000", "30,001-48,000", "48,001-75,000", "75,001-110,000", "over 110,000"]
	income_choices = [("", "")]
	for level in income_levels:
		if level == "over 110,000":
			income_choices.append((level, "Over $110,000"))
		else:
			income_choices.append((level, "$"+level))

	# Next, US states:
	states = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"]
	state_choices = [("", "")]
	for state in states:
		state_choices.append((state, state))

	# Last, budget categories:
	budget_choices = [
		("", ""), 
		("10000", "Less than $10,000"), 
		("20000", "$10,000 - $20,000"), 
		("40000", "$20,000 - $40,000"), 
		("60000", "$40,000 - $60,000"), 
		("80000", "$60,000 - $80,000"), 
		("100000", "$80,000 - $100k"), 
		("120000", "$100k - $120k"), 
		("150000", "$120k - $150k"), 
		("200000", "$150k - $200k"), 
		("300000", "More than $200k")
	]

	# With that out of the way, let's generate some fields!
	first_name = StringField("First name:", validators = [Required("Please enter your first name.")])
	last_name = StringField("Last name:", validators = [Required("Please enter your last name.")])
	email = StringField("Email:", validators = [Required("Please enter your email."), Email("Please enter an email address.")])
	career = SelectQueryField("Career:", query = Career.select(), get_label = "name", allow_blank = True, blank_text = " ", validators = [Required("Please choose a career.")])
	income = SelectField("What's your family's income level?", choices = income_choices, validators = [Required("Please select your family's income level.")])
	budget = SelectField("What's your budget for higher education?", choices = budget_choices, validators = [Required("Please enter a budget.")])
	city = StringField("What city do you live in?", validators = [Required("Please enter the city you live in.")])
	state = SelectField("What state do you live in?", choices = state_choices, validators = [Required("Please enter the state you live in.")])



# VIEWS

@app.route("/")
@app.route("/index")
def index():
	return render_template("index.html", title = "Home")


@app.route("/report/<student_id>")
def report(student_id):
	try:
		student = Student.get(id = student_id)
	except Student.DoesNotExist:
		abort(404)

	pathways = Pathway.select().where(Pathway.student == student)

	edit_mode = False

	return render_template("report.html", title = student.name + "'s Report", student = student, pathways = pathways, edit_mode = edit_mode)


@app.route("/questions", methods = ['GET', 'POST'])
def questions():
	form = Questionnaire_Form()

	if form.validate_on_submit():
		try:
			with database.atomic(): # This will fail, and rollback any commits, if the student isn't unique.
				student = Student.create(
					name = form.first_name.data + " " + form.last_name.data,
					email = form.email.data,
					career = form.career.data,
					income = form.income.data,
					budget = int(form.budget.data),
					city = form.city.data,
					state = form.state.data
				)
		except IntegrityError:
			flash("It looks like you've already created a profile. Try logging in!")
			return redirect("/index")

		solver.make_pathways_async(student = student, how_many = 6) # This *should* be asynchronous.
		session["student name"] = student.name
		return redirect("/confirmation")

	else:
		for field, errors in form.errors.items():
			for error in errors:
				flash(error)

	return render_template("questions.html", form = form)


@app.route("/confirmation")
def confirmation():
	student_name = session["student name"]
	return render_template("confirmation.html", title = "Thank you!", student_name = student_name)



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