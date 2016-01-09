# Run this!

from flask import Flask, g, render_template

from peewee import *
from playhouse.postgres_ext import *

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



# VIEWS

@app.route("/")
@app.route("/index")
def index():
	student = Student.select().where(Student.name == "Jonathan Turpen").get()

	return render_template("index.html", title = "Home", student = student)


@app.route("/report/<id>")
def report(id):
	student = Student.get(Student.id == id)
	pathways = Pathway.select().where(Pathway.student == student)

	return render_template("report.html", student = student, pathways = pathways)



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