# Run this!

from flask import Flask, g, render_template, redirect, request, abort, flash, session

from peewee import *
from playhouse.postgres_ext import *

from flask.ext.wtf import Form
from wtforms import StringField, SelectField, PasswordField, BooleanField as WTFBooleanField # Peewee also has a "BooleanField," so this was necessary.
from wtforms.fields.html5 import EmailField
from wtforms.validators import Email, Required, EqualTo

from wtfpeewee.fields import SelectQueryField # Unlike a regular WTForms SelectField, this returns actual model classes.
from wtfpeewee.orm import model_form # For modeling forms from database objects. Not sure I really need it, but I do really like it.

from flask.ext.login import login_required, LoginManager, login_user, logout_user, current_user

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

# Start the app:
app = Flask(__name__)
app.config.from_object(__name__)

# Login config:
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
	try:
		user = User.get(email = user_id)
	except DoesNotExist:
		print "Current user no longer exists!"
		current_user = None
		return
	return user



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

class Login_Form(Form):
	# For logging in users.
	email = EmailField("Email:", validators = [Required("Please enter your email."), Email("Please enter a valid email address.")])
	password = PasswordField("Password:", validators = [Required("Please enter your password.")])
	remember = WTFBooleanField("Remember me")


class Registration_Form(Form):
	email = EmailField("Email:", validators = [Required("Please enter an email."), Email("Please enter a valid email address.")])
	password = PasswordField("Password:", validators = [Required("Please enter a password."), EqualTo("confirm_password", message = "Passwords must match.")])
	confirm_password = PasswordField("Confirm password:", validators = [Required("Please confirm your password.")])
	user_type = SelectField("Are you a customer or an employee?", choices = [("", ""),("customer", "Customer"), ("employee", "Employee")], validators = [Required()])


class Choose_Student(Form):
	student = SelectQueryField("Choose a student:", query = Student.select(), get_label = "name", allow_blank = True, blank_text = " ", validators = [Required()])


class Choose_Report(Form):
	report = SelectQueryField("Choose a report to view:", query = Report.select(), get_label = "career.name", allow_blank = True, blank_text = " ", validators = [Required()])


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
	email = EmailField("Email:", validators = [Required("Please enter your email."), Email("Please enter a valid email address.")])
	career = SelectQueryField("Career:", query = Career.select(), get_label = "name", allow_blank = True, blank_text = " ", validators = [Required("Please choose a career.")])
	income = SelectField("What's your family's income level?", choices = income_choices, validators = [Required("Please select your family's income level.")])
	budget = SelectField("What's your budget for higher education?", choices = budget_choices, validators = [Required("Please enter a budget.")])
	city = StringField("What city do you live in?", validators = [Required("Please enter the city you live in.")])
	state = SelectField("What state do you live in?", choices = state_choices, validators = [Required("Please enter the state you live in.")])



# VIEWS

@app.route("/")
@app.route("/index")
def index():
	if current_user.is_authenticated:
		return redirect("/students")
	else:
		return redirect("/login")

	return render_template("index.html", title = "Home")


@app.route("/login", methods = ["GET", "POST"])
def login():
	form = Login_Form()
	
	if form.validate_on_submit():
		try:
			user = User.get(User.email == form.email.data)
			if user.password == form.password.data:
				user.authenticated = True
				login_user(user, remember = form.remember.data)
				return redirect("/students")
		
		except DoesNotExist:
			flash("Email or password incorrect.")
	
	return render_template("login.html", form = form)


@app.route("/register", methods = ["GET", "POST"])
def register():
	form = Registration_Form()
	
	if form.validate_on_submit():
		user = User.create(
			email = form.email.data,
			password = form.password.data
		)
		
		if form.user_type.data == "customer":
			customer = Customer.create()
			user.customer = customer
		elif form.user_type.data == "employee":
			employee = Employee.create()
			user.employee = employee

		user.save()

		return redirect("/login")

	return render_template("register.html", form = form)


@app.route("/logout")
def logout():
	if current_user.is_authenticated:
		logout_user()
	return redirect("/index")


@app.route("/questions", methods = ['GET', 'POST'])
@login_required
def questions():
	if current_user.customer is None:
		return redirect("/")

	form = Questionnaire_Form(email = current_user.email)

	if form.validate_on_submit():
		try:
			with database.atomic(): # This will fail, and rollback any commits, if the student isn't unique.
				student = Student.create(
					name = form.first_name.data + " " + form.last_name.data,
					email = form.email.data,
					income = form.income.data,
					budget = int(form.budget.data),
					city = form.city.data,
					state = form.state.data,
					customer = current_user.customer
				)
				report = Report.create(
					student = student,
					career = form.career.data
				)
				student.save()
				report.save()
		except IntegrityError:
			flash("It looks like you've already created a profile. Try logging in!")
			return redirect("/index")

		solver.make_pathways_async(student = student, report = report, how_many = 6) # This *should* be asynchronous.
		return redirect("/confirmation")

	else:
		for field, errors in form.errors.items():
			for error in errors:
				flash(error)

	return render_template("questions.html", form = form)


@app.route("/students", methods = ["GET", "POST"])
@login_required
def list_students():
	# Create a query for the user's students.
	# If the user is an employee, that should be *all* students.
	if current_user.customer is not None:
		query = Student.select().where(Student.customer == current_user.customer)
	elif current_user.employee is not None:
		query = Student.select()
		student_query = Student.select()
	else:
		flash("User is neither customer nor employee!")
		print(current_user.customer)
		return redirect("/logout")

	form = Choose_Student()
	form.student.query = query

	if form.validate_on_submit():
		student = form.student.data
		return redirect("/reports/" + str(student.id))

	return render_template("students.html", form = form)


@app.route("/reports/<student_id>", methods = ["GET", "POST"])
@login_required
def list_reports(student_id):
	student = Student.get(id = student_id)
	query = Report.select().join(Student).where(Student.id == student_id)

	form = Choose_Report()
	form.report.query = query

	if form.validate_on_submit():
		report = form.report.data
		return redirect("/report/" + str(student.id) + "_" + str(report.id))

	return render_template("reports.html", title = student.name + "'s Reports", student = student, form = form)


@app.route("/report/<student_id>_<report_id>")
def report(student_id, report_id):
	try:
		student = Student.get(id = student_id)
		report = Report.get(id = report_id)
	except DoesNotExist:
		abort(404)

	return render_template("report.html", title = student.name + "'s Report", student = student, report = report)


@app.route("/confirmation")
@login_required
def confirmation():
	return render_template("confirmation.html", title = "Thank you!")



# RUN IT

def create_tables():
	School.create_table(True)
	Program.create_table(True)
	Career.create_table(True)
	Student.create_table(True)
	Recipe.create_table(True)
	Step.create_table(True)
	Report.create_table(True)
	Pathway.create_table(True)
	Pathway_Step.create_table(True)
	Customer.create_table(True)
	Employee.create_table(True)
	User.create_table(True)


if __name__ == '__main__':
    create_tables()
    app.run()