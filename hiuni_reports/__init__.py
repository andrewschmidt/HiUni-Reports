import os
from flask import Flask, g
# import config # I *think* I can get rid of this...

from flask.ext.bcrypt import Bcrypt
from flask.ext.markdown import Markdown
from flask.ext.mail import Mail
from itsdangerous import URLSafeTimedSerializer



# START THE APPLICATION
cwd = os.getcwd()
static = cwd + "/static"

application = Flask(__name__, instance_relative_config = True, static_folder = static) # AWS expects this to be "application," not "app"
application.config.from_pyfile("config.py")

bcrypt = Bcrypt(application)
md = Markdown(application)
mail = Mail(application)
ts = URLSafeTimedSerializer(application.config["SECRET_KEY"])


# REQUEST HANDLERS
@application.before_request
def before_request():
	g.db = database
	g.db.connect()

@application.after_request
def after_request(response):
	g.db.close()
	return response


# LOGIN MANAGER
from flask.ext.login import LoginManager
from models import *

login_manager = LoginManager()
login_manager.init_app(application)

@login_manager.user_loader
def load_user(user_id):
	try:
		user = User.get(email = user_id)
	except DoesNotExist:
		print "Current user no longer exists!"
		current_user = None
		return
	return user


# VIEWS
import hiuni_reports.views


# TABLES
def create_tables():
	Customer.create_table(True)
	Employee.create_table(True)
	User.create_table(True)
	School.create_table(True)
	Program.create_table(True)
	Student.create_table(True)
	Career.create_table(True)
	Recipe.create_table(True)
	Step.create_table(True)
	Report.create_table(True)
	Pathway.create_table(True)
	Pathway_Step.create_table(True)

def create_admin():
	if Employee.select().count() == 0:
		print "Creating an admin."
		employee = Employee.create(
				is_admin = True
			)
		user = User.create(
			email = application.config["ADMINEMAIL"],
			is_confirmed = True,
			password = application.config["ADMINPASS"],
			employee = employee
		)

create_tables()
create_admin()