from hiuni_reports import application
from flask import render_template, redirect, request, abort, flash, session, url_for

from flask.ext.login import login_required, login_user, logout_user, current_user

from peewee import *
from playhouse.postgres_ext import *

from models import * # Includes the "database" variable.
import data_helper
import solver

from forms import *



# VIEWS

@application.route("/")
@application.route("/index")
def index():
	if current_user.is_authenticated:
		return redirect("/students")
	else:
		return redirect("/login")

	return render_template("index.html", title = "Home")


@application.route("/login", methods = ["GET", "POST"])
def login():
	form = Login_Form()
	
	if form.validate_on_submit():
		try:
			user = User.get(User.email == form.email.data)
			
			if user.is_correct_password(form.password.data):
				user.authenticated = True
				login_user(user, remember = form.remember.data)
				return redirect("/students")
		
		except DoesNotExist:
			flash("Email or password incorrect.")
	
	return render_template("login.html", form = form)



@application.route("/logout")
def logout():
	if current_user.is_authenticated:
		logout_user()
	return redirect("/index")


@application.route("/register", methods = ["GET", "POST"])
def register():
	form = Registration_Form()
	
	if form.validate_on_submit():
		customer = Customer()
		
		if form.organization.data != "":
			customer.organization = form.organization.data
			customer.is_organization = True
			customer.is_student = False # Default is True, so we just flop that.
		
		customer.save()

		try:
			user = User.create(
				email = form.email.data,
				password = form.password.data,
				customer = customer
			)
		except Exception:
			flash("Looks like somebody's already registered with that email!")
			return redirect("/register")

		# Log them in!
		user.authenticated = True
		login_user(user, remember = True)

		return redirect("/questions")

	return render_template("register.html", form = form)


@application.route("/register_employee", methods = ["GET", "POST"])
@login_required
def register_employee():
	if current_user.employee:
		form = Registration_Form()
		
		if form.validate_on_submit():
			employee = Employee()
			employee.save()
			
			user = User.create(
				email = form.email.data,
				password = form.password.data,
				employee = employee
			)
			
			user.save()
			
			return redirect("/students")

		return render_template("register_employee.html", form = form)

	else: return redirect("/")


@application.route("/manage_schools", methods = ["GET", "POST"])
@login_required
def manage_schools():
	if current_user.employee:
		if request.method == "POST":
			if "import" in request.form:
				data_helper.import_school_data_async()
				flash("Importing schools... This may take a while.")

		school_count = str(School.select().count())

		return render_template("manage_schools.html", school_count = school_count)

	else: return redirect("/")


@application.route("/manage_careers", methods = ["GET", "POST"])
@login_required
def manage_careers():
	if current_user.employee:
		recipe_count = str(Recipe.select().count())
		careers = []
		query = Career.select()
		for career in query:
			careers.append(career)

		if request.method == "POST":
			if "delete" in request.form:
				career = Career.get(id = request.form["delete"])
				print "Deleting career... " + career.name
				career.delete_instance(recursive = True)
				return redirect("/manage_careers")

		return render_template("manage_careers.html", careers = careers, recipe_count = recipe_count)

	else: return redirect("/")


@application.route("/career/<career_id>", methods = ["GET", "POST"])
@login_required
def career(career_id):
	if current_user.employee:
		career = Career.get(id = career_id)
		return render_template("career.html", career = career)

	else: return redirect("/")


@application.route("/add_career", methods = ["GET", "POST"])
@login_required
def add_career():
	if current_user.employee:
		form = Add_Career()

		if form.validate_on_submit():
			with database.atomic(): # This will fail, and rollback any commits, if the career isn't unique.
				career = Career.create(
					name = form.name.data,
					image = form.image.data,
					description = form.description.data
				)

				flash("Saved the career.")
				return redirect("/manage_careers/")

		else:
			for field, errors in form.errors.items():
				for error in errors:
					flash(error)

		return render_template("edit_career.html", form = form, career = None)

	else: return redirect("/")


@application.route("/edit_career/<career_id>", methods = ["GET", "POST"])
@login_required
def edit_career(career_id):
	if current_user.employee:
		career = Career.get(id = career_id)
		form = Add_Career(name = career.name, description = career.description)

		if form.validate_on_submit():
			career.name = form.name.data
			career.description = form.description.data
			if form.image.data:
				career.image = form.image.data

			career.save()
			flash("Updated the career!")

			return redirect("/manage_careers/")

		else:
			for field, errors in form.errors.items():
				for error in errors:
					flash(error)

		return render_template("edit_career.html", form = form, career = career)

	else: return redirect("/")


@application.route("/questions", methods = ["GET", "POST"])
@login_required
def questions():
	if current_user.customer is None:
		flash("You have to be a customer to add students.")
		return redirect("/")

	form = Questionnaire_Form(email = current_user.email)

	if form.validate_on_submit():
		try:
			with database.atomic(): # This will fail, and rollback any commits, if the student isn't unique.
				student = Student.create(
					name = form.first_name.data + " " + form.last_name.data,
					first_name = form.first_name.data,
					last_name = form.last_name.data,
					email = form.email.data,
					income = form.income.data,
					budget = int(form.budget.data),
					city = form.city.data,
					state = form.state.data,
					customer = current_user.customer
				)
				
				if form.photo.data:
					student.photo = form.photo.data
					student.save()
				
				report = Report.create(
					student = student,
					career = form.career.data
				)

		except IntegrityError:
			flash("It looks like you've already created a profile. Try logging in!")
			return redirect("/index")

		solver.make_pathways_async(student = student, report = report, how_many = 6)
		return redirect("/confirmation")

	else:
		for field, errors in form.errors.items():
			for error in errors:
				flash(error)

	return render_template("questions.html", form = form)


@application.route("/add_report", methods = ["GET", "POST"])
@login_required
def add_report():
	form = Add_Report()
	form.student.query = Student.select().where(Student.customer == current_user.customer)

	if form.validate_on_submit():
		student = form.student.data

		report = Report.create(
			student = student,
			career = form.career.data
		)

		solver.make_pathways_async(student = student, report = report, how_many = 6)
		return redirect("/confirmation")

	return render_template("add_report.html", form = form)


@application.route("/students", methods = ["GET", "POST"])
@login_required
def list_students():
	# Create a query for the user's students.
	# If the user is an employee, that should be *all* students.
	if current_user.customer is not None:
		query = Student.select().where(Student.customer == current_user.customer)
		if query.count() == 1:
			student = query.get()
			return redirect("/reports/" + str(student.id))
		elif query.count() == 0:
			return redirect("/questions")

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


@application.route("/reports/<student_id>", methods = ["GET", "POST"])
@login_required
def list_reports(student_id):
	student = Student.get(id = student_id)
	
	if current_user.employee is None:
		query = Report.select().join(Student).where((Student.id == student_id) & (Report.published == True))
	else:
		query = Report.select().join(Student).where(Student.id == student_id)

	if query.count() == 1:
		report = query.get()
		return redirect("/report/" + str(student.id) + "_" + str(report.id))
	elif query.count() == 0:
		if Report.select().join(Student).where(Student.id == student_id).count() > 0:
			return redirect("/confirmation")
		else:
			return redirect("/")

	form = Choose_Report()
	form.report.query = query

	if form.validate_on_submit():
		report = form.report.data
		return redirect("/report/" + str(student.id) + "_" + str(report.id))

	return render_template("reports.html", title = student.name + "'s Reports", student = student, form = form)


@application.route("/report/<student_id>_<report_id>", methods = ["GET", "POST"])
def report(student_id, report_id):
	try:
		student = Student.get(id = student_id)
		report = Report.get(id = report_id)
	except DoesNotExist:
		abort(404)

	if not report.published and current_user.employee is None:
		return redirect("/confirmation")

	if request.method == "POST" and current_user.employee is not None:

		if "delete" in request.form:
			pathway_id = request.form["delete"]
			pathway = Pathway.get(id = pathway_id)
			pathway.delete_instance(recursive = True)
		
		elif "publish" in request.form:
			report.published = True
			report.save()

		elif "unpublish" in request.form:
			report.published = False
			report.save()

	return render_template("report.html", title = student.name + "'s Report", student = student, report = report)


@application.route("/confirmation")
@login_required
def confirmation():
	return render_template("confirmation.html", title = "Thank you!")