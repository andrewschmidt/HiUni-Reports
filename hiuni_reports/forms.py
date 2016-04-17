# Form imports:
from flask.ext.wtf import Form
from flask.ext.wtf.file import FileField, FileAllowed
from wtforms import widgets, StringField, SelectField, SelectMultipleField, PasswordField, TextAreaField, BooleanField as WTFBooleanField # Peewee also has a "BooleanField," so this was necessary.
from wtforms.fields.html5 import EmailField
from wtforms.validators import Email, Required, EqualTo
from wtfpeewee.fields import SelectQueryField # Unlike a regular WTForms SelectField, this returns actual model classes.

from models import *


# CUSTOM FIELDS

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


# FORMS

class Login_Form(Form):
	# For logging in users.
	email = EmailField("Email:", validators = [Required("Please enter your email."), Email("Please enter a valid email address.")])
	password = PasswordField("Password:", validators = [Required("Please enter your password.")])
	remember = WTFBooleanField("Keep me signed in")


class Registration_Form(Form):
	email = EmailField("Email:", validators = [Required("Please enter an email."), Email("Please enter a valid email address.")])
	password = PasswordField("Password:", validators = [Required("Please enter a password."), EqualTo("confirm_password", message = "Passwords must match.")])
	confirm_password = PasswordField("Confirm password:", validators = [Required("Please confirm your password.")])
	organization = StringField("Name of organization:")


class Employee_Form(Form):
	name = StringField("First name:", validators = [Required("Don't forget your name!")])
	email = EmailField("Email:", validators = [Required("Please enter an email."), Email("Please enter a valid email address.")])
	password = PasswordField("Password:", validators = [Required("Please enter a password."), EqualTo("confirm_password", message = "Passwords must match.")])
	confirm_password = PasswordField("Confirm password:", validators = [Required("Please confirm your password.")])


class Choose_Student(Form):
	student = SelectQueryField("Choose a student:", query = Student.select(), get_label = "name", allow_blank = True, blank_text = " ", validators = [Required()])


class Choose_Report(Form):
	report = SelectQueryField("Choose a report to view:", query = Report.select(), get_label = "career.name", allow_blank = True, blank_text = " ", validators = [Required()])


class Add_Report(Form):
	student = SelectQueryField("Make a report for:", query = Student.select(), get_label = "name", validators = [Required()])
	career = SelectQueryField("Choose a career:", query = Career.select(), get_label = "name", allow_blank = True, blank_text = " ", validators = [Required()])


class Add_Career(Form):
	name = StringField("Name", validators = [Required("Don't forget the career's name!")])
	image = FileField("Banner image", validators = [FileAllowed(["jpg", "png", "jpeg"], "You sure that's an image file? Upload a JPEG or PNG!")])
	description = TextAreaField("Description")


class Recipe_Step_Form(Form):
	title = StringField("Title:", validators = [Required("Please enter a step title.")])
	duration = StringField("Duration (in years):", validators = [Required("Please enter a duration in years.")])
	cips = StringField("Areas of study as CIPs (separated by commas):", validators = [Required("Please enter at least one CIP.")])
	school_kind = SelectQueryField("Kind of school:", query = School.select(School.kind).order_by(fn.COUNT(School.id)).distinct().order_by(), get_label = "kind", allow_blank = True, blank_text = " ", validators = [Required("Please choose a kind of school.")])
	sort_by = SelectQueryField("Sort by:", query = Step.select(Step.sort_by).distinct().order_by(), get_label = "sort_by", allow_blank = True, blank_text = " ", validators = [Required("Please choose a way to sort programs.")])
	description = TextAreaField("Description")


class Edit(Form):
	text = TextAreaField("Text")


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
	photo = FileField("Photo:", validators = [FileAllowed(["jpg", "png", "jpeg"], "Your photo needs to be either a JPEG or PNG. Sorry!")])
	career = SelectQueryField("Career:", query = Career.select().join(Recipe).distinct().where(Recipe.career == Career.id), get_label = "name", allow_blank = True, blank_text = " ", validators = [Required("Please choose a career.")])
	income = SelectField("What's your family's income level?", choices = income_choices, validators = [Required("Please select your family's income level.")])
	budget = SelectField("What's your budget for higher education?", choices = budget_choices, validators = [Required("Please enter a budget.")])
	city = StringField("What city do you live in?", validators = [Required("Please enter the city you live in.")])
	state = SelectField("What state do you live in?", choices = state_choices, validators = [Required("Please enter the state you live in.")])

	# Additional fields:
	appeal = TextAreaField("Why does this career appeal to you?")
	experience = TextAreaField("Do you have any experiences related to the career you chose?")
	scholarships = StringField("If you're expecting to receive scholarships or private grants, how much do you expect total?")
	
	list_of_choices = ["Personal savings", "Student loans", "Help from parents or relatives", "Federal grants", "Scholarships or private grants"]
	choices = [(x, x) for x in list_of_choices]
	payment = MultiCheckboxField("How do you plan to pay for college?", choices = choices)

