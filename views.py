from flask import render_template
from app import app
from data_model import *


@app.route("/")
@app.route("/index")
def index():
	student = Student.select().where(Student.name == "Jonathan Turpen").get()

	return render_template("index.html", title = "Home", student = student)