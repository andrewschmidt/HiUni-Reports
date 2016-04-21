from hiuni_reports import application, md
from flask import render_template, redirect, request, abort, flash, session, url_for

from flask.ext.login import login_required, login_user, logout_user, current_user

from peewee import *
from playhouse.postgres_ext import *

from models import * # Includes the "database" variable.
import data_helper
import solver

from forms import *

from playhouse.migrate import *
migrator = PostgresqlMigrator(database)



# VIEWS

@application.route("/")
@application.route("/index")
def index():
	if current_user.is_authenticated:
		return redirect("/students")
	else:
		return redirect("/login")

	return render_template("index.html", title = "Home")


@application.route("/migrate")
@login_required
def migrations():
	if current_user.employee.is_admin:
		# migrate(
		# 	migrator.add_column("employee", "is_admin", BooleanField(default = False))
		# )
		# print "Migrated!"
		return redirect("/")
	else:
		return redirect("/")


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
		form = Employee_Form()
		
		if form.validate_on_submit():
			employee = Employee.create(
					name = form.name.data
				)			
			user = User.create(
				email = form.email.data,
				password = form.password.data,
				employee = employee
			)			
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


@application.route("/school/<school_id>", methods = ["GET", "POST"])
@login_required
def school(school_id):
	if current_user.employee:
		school = School.get(id = school_id)

		if request.method == "POST":
			if "delete_program" in request.form:
				program = Program.get(id = request.form["delete"])
				program.delete_instance(recursive = True)
				return redirect("/school/" + school_id)

			elif "delete_school" in request.form:
				school.delete_instance(recursive = True)
				return redirect("/manage_schools")

		return render_template("school.html", school = school)

	else: return redirect("/")


@application.route("/add_school", methods = ["GET", "POST"])
@application.route("/edit_school/<school_id>", methods = ["GET", "POST"])
@login_required
def edit_school(school_id = None):
	if current_user.employee:
		
		if school_id:
			school = School.get(id = school_id)

			form = Add_School(
					name = school.name,
					ipeds_id = school.ipeds_id,
					existing_kind = school.kind,
					admission_rate = str(school.admission_rate),
					city = school.city,
					state = school.state,
					latitude = school.latitude,
					longitude = school.longitude,
					total_price_in_state = school.total_price.get("in-state students living on campus"),
					total_price_in_state_off_campus = school.total_price.get("in-state students living off campus (with family)"),
					total_price_out_of_state = school.total_price.get("out-of-state students living on campus"),
					net_price_average = school.net_price.get("average")
				)
		else:
			school = School()
			form = Add_School()

		# Dynamically generate the choices for the "school kind" dropdown, based on what's in the database:
		s = School.select(School.kind).order_by(fn.COUNT(School.id)).distinct().order_by()
		kinds = [("", "")]
		for x in s:
			kinds.append((x.kind, x.kind))
		kinds.append(("Custom", "Custom"))
		form.existing_kind.choices = kinds

		if form.validate_on_submit():
			with database.atomic():
				school.name = form.name.data
				school.ipeds_id = form.ipeds_id.data
				school.admission_rate = int(form.admission_rate.data)
				
				if form.existing_kind.data != "Custom":
					school.kind = form.existing_kind.data
				else:
					school.kind = form.new_kind.data

				school.city = form.city.data
				school.state = form.state.data
				if form.longitude.data: school.longitude = form.longitude.data
				if form.latitude.data: school.latitude = form.latitude.data

				if not school_id:
					school.net_price = {}
					school.total_price = {}
					school.save()

				if form.total_price_in_state.data: school.total_price["in-state students living on campus"] = form.total_price_in_state.data
				if form.total_price_in_state_off_campus.data: school.total_price["in-state students living off campus (with family)"] = form.total_price_in_state_off_campus.data
				if form.total_price_out_of_state.data: school.total_price["out-of-state students living on campus"] = form.total_price_out_of_state.data
				if form.net_price_average.data: school.net_price["average"] = form.net_price_average.data

				school.save()
				flash("Updated", school.name)

				return redirect("/school/" + str(school.id))

		else:
			for field, errors in form.errors.items():
				for error in errors:
					flash(error)

		return render_template("edit_school.html", form = form, school = school)

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
				career.delete_instance(recursive = True)
				return redirect("/manage_careers")

		return render_template("manage_careers.html", careers = careers, recipe_count = recipe_count)

	else: return redirect("/")


@application.route("/career/<career_id>", methods = ["GET", "POST"])
@login_required
def career(career_id):
	if current_user.employee:
		career = Career.get(id = career_id)

		if request.method == "POST":
			if "delete" in request.form:
				recipe = Recipe.get(id = request.form["delete"])
				recipe.delete_instance(recursive = True)
				return redirect("/career/" + career_id)

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
					description = form.description.data
				)
				if form.image.data: 
					career.image = form.photo.data
					career.save()

				flash("Saved the career.")
				return redirect("/career/" + str(career.id))

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

			return redirect("/career/" + str(career.id))

		else:
			for field, errors in form.errors.items():
				for error in errors:
					flash(error)

		return render_template("edit_career.html", form = form, career = career)

	else: return redirect("/")


@application.route("/add_recipe/<career_id>", methods = ["GET", "POST"])
@application.route("/edit_recipe/<recipe_id>", methods = ["GET", "POST"])
@login_required
def edit_recipe(career_id = None, recipe_id = None):
	if current_user.employee:
		if recipe_id:
			recipe = Recipe.get(id = recipe_id)
			career = recipe.career
		else:
			career = Career.get(id = career_id)
			recipe = None

		form = Recipe_Step_Form()

		# Dynamically generate the choices for the "school kind" dropdown, based on what's in the database:
		s = School.select(School.kind).order_by(fn.COUNT(School.id)).distinct().order_by()
		kinds = [("", "")]
		for x in s:
			kinds.append((x.kind, x.kind))

		form.school_kind.choices = kinds

		if request.method == "POST":
			if "delete" in request.form:
				step = Step.get(id = request.form["delete"])
				step.delete_instance(recursive = True)
				return redirect("/edit_recipe/" + recipe_id)

		if form.validate_on_submit():
			if recipe == None:
				recipe = Recipe.create(career = career)

			number = recipe.steps.count() + 1
			cips = [cip.strip() for cip in form.cips.data.split(',')]

			try:
				step = Step.create(
					recipe = recipe,
					number = number,
					title = form.title.data,
					duration = int(form.duration.data),
					cips = cips,
					school_kind = form.school_kind.data,
					sort_by = form.sort_by.data,
					description = form.description.data
				)
			except Exception:
				flash("Error saving step.")

			return redirect("/edit_recipe/" + str(recipe.id))

		else:
			for field, errors in form.errors.items():
				for error in errors:
					flash(error)

		return render_template("edit_recipe.html", form = form, recipe = recipe, career = career)

	else: return redirect("/")


@application.route("/edit_recipe/<recipe_id>/step/<step_id>", methods = ["GET", "POST"])
@login_required
def edit_recipe_step(recipe_id, step_id):
	if current_user.employee:
		try:
			step = Step.get(id = step_id)
			
			cips = ", ".join(step.cips)

			form = Recipe_Step_Form(
					title = step.title,
					duration = step.duration,
					cips = cips,
					school_kind = step.school_kind,
					sort_by = step.sort_by,
					description = step.description
				)

			if form.validate_on_submit():
				cips = [cip.strip() for cip in form.cips.data.split(',')]

				step.title = form.title.data
				step.duration = form.duration.data
				step.cips = cips
				step.school_kind = form.school_kind.data
				step.description = form.description.data
				step.save()

				return redirect("/edit_recipe/" + recipe_id)

			else:
				for field, errors in form.errors.items():
					for error in errors:
						flash(error)

			return render_template("edit_recipe_step.html", form = form, step = step)

		except DoesNotExist:
			abort(404)

	else: return redirect("/")


@application.route("/questions", methods = ["GET", "POST"])
@application.route("/questions/<student_id>", methods = ["GET", "POST"])
@login_required
def questions(student_id = None):
	if current_user.customer is None:
		flash("You have to be a customer to add students.")
		return redirect("/")

	if student_id:
		student = Student.get(id = student_id)
		hide_photo = True
		form = Questionnaire_Form(
				first_name = student.first_name,
				last_name = student.last_name,
				email = student.email,
				city = student.city,
				state = student.state,
				income = student.income,
				budget = student.budget
			)
	else:
		student = Student()
		hide_photo = False
		form = Questionnaire_Form(email = current_user.email)

	if form.validate_on_submit():
		experience = {}
		appeal = {}

		try:
			with database.atomic(): # This will fail, and rollback any commits, if the student isn't unique.
				career = form.career.data
				experience[career.name] = form.experience.data
				appeal[career.name] = form.appeal.data

				student.name = form.first_name.data + " " + form.last_name.data
				student.first_name = form.first_name.data
				student.last_name = form.last_name.data
				student.email = form.email.data
				student.income = form.income.data
				student.budget = int(form.budget.data)
				student.city = form.city.data
				student.state = form.state.data
				student.customer = current_user.customer
				
				if student.experience:
					student.experience.update(experience)
				else:
					student.experience = experience
				
				if student.appeal:
					student.appeal.update(appeal)
				else:
					student.appeal = appeal

				student.save()

				if form.photo.data: 
					student.photo = form.photo.data
					student.save()
				
				report = Report.create(
					student = student,
					career = career
				)

		except IntegrityError:
			flash("It looks like you've already created a profile. Try logging in!")
			return redirect("/index")

		solver.make_pathways_async(student = student, report = report, how_many = 10)
		return redirect("/confirmation")

	else:
		for field, errors in form.errors.items():
			for error in errors:
				flash(error)

	return render_template("questions.html", form = form, hide_photo = hide_photo)


@application.route("/add_report", methods = ["GET", "POST"])
@login_required
def add_report():
	if current_user.customer is not None:
		query = Student.select().where(Student.customer == current_user.customer)
		if query.count() == 1:
			student = query.get()
			return redirect("/questions/" + str(student.id))
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
		return redirect("/questions/" + str(student.id))

	return render_template("students.html", form = form)


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
		if current_user.employee is None:
			return redirect("/report/" + str(student.id) + "_" + str(report.id))
	elif query.count() == 0:
		if Report.select().join(Student).where(Student.id == student_id).count() > 0:
			return redirect("/confirmation")
		elif current_user.employee is None:
				return redirect("/questions")

	form = Choose_Report()
	form.report.query = query

	if request.method == "POST" and current_user.employee.is_admin:
		if "delete_student" in request.form:
			student.delete_instance(recursive = True)
			return redirect("/students")

	if form.validate_on_submit():
		report = form.report.data
		return redirect("/report/" + str(student.id) + "_" + str(report.id))

	return render_template("reports.html", title = student.name + "'s Reports", student = student, form = form)


@application.route("/report/<student_id>_<report_id>", methods = ["GET", "POST"])
def report(student_id, report_id):
	try:
		student = Student.get(id = student_id)
		report = Report.get(id = report_id)

		if not report.published and current_user.employee is None:
			return redirect("/confirmation")
		elif not report.published and current_user.employee is not None:
			return redirect("/edit_report/" + str(student.id) + "_" + str(report.id))

		if request.method == "POST" and current_user.employee is not None:
			
			if "unpublish" in request.form:
				report.published = False
				report.save()
				return redirect("/edit_report/" + str(student.id) + "_" + str(report.id))

		return render_template("report.html", title = student.name + "'s Report", student = student, report = report)
	
	except DoesNotExist:
		abort(404)


@application.route("/edit_report/<student_id>_<report_id>", methods = ["GET", "POST"])
@login_required
def edit_report(student_id, report_id):
	if current_user.employee:
		try:
			student = Student.get(id = student_id)
			report = Report.get(id = report_id)

			if request.method == "POST" and current_user.employee is not None:

				if "unpublish" in request.form:
					report.published = False
					report.save()
				
				if "publish" in request.form:
					report.published = True
					report.save()
					return redirect("/report/" + str(student.id) + "_" + str(report.id))

				if "delete_report" in request.form:
					report.delete_instance(recursive = True)
					return redirect("/reports/" + str(student.id))

				if "delete_pathway" in request.form:
					pathway_id = request.form["delete_pathway"]
					pathway = Pathway.get(id = pathway_id)
					pathway.delete_instance(recursive = True)

				if "delete_student" in request.form:
					student.delete_instance(recursive = True)
					return redirect("/students")

			return render_template("edit_report.html", title = student.name + "'s Report", student = student, report = report)

		except DoesNotExist:
			abort(404)

	else: return redirect("/")


@application.route("/edit_report/<student_id>_<report_id>/pathway/<pathway_id>/tagline", methods = ["GET", "POST"])
@login_required
def edit_report_tagline(student_id, report_id, pathway_id):
	if current_user.employee:
		try:
			pathway = Pathway.get(id = pathway_id)

			form = Edit(text = pathway.tagline)

			if form.validate_on_submit():
				pathway.tagline = form.text.data
				pathway.save()
				return redirect("/edit_report/" + student_id + "_" + report_id)

			return render_template("edit.html", title = "Edit tagline", form = form, rows = "2")

		except DoesNotExist:
			abort(404)
	
	else: return redirect("/")


@application.route("/edit_report/<student_id>_<report_id>/step/<step_id>", methods = ["GET", "POST"])
@login_required
def edit_pathway_step(student_id, report_id, step_id):
	if current_user.employee:
		try:
			step = Pathway_Step.get(id = step_id)

			form = Edit(text = step.description)

			if form.validate_on_submit():
				step.description = form.text.data
				step.save()
				return redirect("/edit_report/" + student_id + "_" + report_id)

			return render_template("edit.html", title = "Edit description", form = form, rows = "15")

		except DoesNotExist:
			abort(404)

	else: return redirect("/")


@application.route("/confirmation")
@login_required
def confirmation():
	return render_template("confirmation.html", title = "Thank you!")