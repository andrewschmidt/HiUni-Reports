from flask import Flask, g
import config

from flask.ext.bcrypt import Bcrypt


# START THE APP
app = Flask(__name__, instance_relative_config = True) # AWS expects this to be "application," not "app"
app.config.from_object("config")
app.config.from_pyfile("config.py")

bcrypt = Bcrypt(app)


# LOGIN MANAGER
from flask.ext.login import LoginManager
from models import *

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
@app.before_request
def before_request():
	g.db = database
	g.db.connect()

@app.after_request
def after_request(response):
	g.db.close()
	return response


# VIEWS
import hiuni_reports.views


# SAFETY CHECK
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
		employee = Employee()
		employee.save()
		user = User.create(
			email = "admin@gohiuni.com",
			password = "admin",
			employee = employee
		)
		user.save()

create_tables()
create_admin()