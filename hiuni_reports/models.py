# Just the data model.

from peewee import *
from playhouse.postgres_ext import *

from hiuni_reports import application
db = application.config["DATABASE"]

from geopy.geocoders import Nominatim
from . import bcrypt

from os import remove
from PIL import Image


# DATABASE	

database = PostgresqlExtDatabase(
	db["name"],
	host = db["host"],
	port = db["port"],
	user = db["user"],
	password = db["password"]
)


# MODELS

class BaseModel(Model):
	class Meta:
		database = database


# USER AUTHENTICATION-RELATED MODELS

class Customer(BaseModel):
	is_organization = BooleanField(default = False)
	organization = TextField(null = True)


class Employee(BaseModel):
	name = TextField(null = True)


class User(BaseModel):
	customer = ForeignKeyField(Customer, related_name = "users", null = True)
	employee = ForeignKeyField(Employee, related_name = "users", null = True)

	authenticated = BooleanField(default = False)
	email = TextField(unique = True, primary_key = True)
	_password = CharField()

	@property
	def password(self):
		return self._password

	@password.setter
	def password(self, plaintext):
		self._password = bcrypt.generate_password_hash(plaintext)

	def is_correct_password(self, plaintext):
		return bcrypt.check_password_hash(self._password, plaintext)

	# The rest is required by Flask-Login
	def is_active(self):
		return True

	def get_id(self):
		return self.email

	def is_authenticated(self):
		return self.authenticated

	def is_anonymous(self):
		return False


# SOLVER-RELATED MODELS

class School(BaseModel):
	name = CharField()
	ipeds_id = CharField()
	kind = CharField()
	admission_rate = IntegerField(null = True)
	
	# Location:
	city = CharField()
	state = CharField()
	latitude = DoubleField(null = True) # Don't forget to "CREATE EXTENSION cube, earthdistance;" to enable querying by location.
	longitude = DoubleField(null = True)
	
	# Cost:
	total_price = HStoreField() # To setup, run "CREATE EXTENSION hstore;" for hiuni_database from psql.
	net_price = HStoreField() # For public institutions, net price refers to net price for in-state students only.


class Program(BaseModel):
	school = ForeignKeyField(School, related_name = "programs")
	name = CharField()
	cip = CharField()
	median_salary = IntegerField(null = True)
	reportable = BooleanField()


class Career(BaseModel):
	name = CharField()
	nicknames = ArrayField(CharField, null = True) # Neither of these are being imported yet.
	description = TextField(null = True)


class Student(Model):
	name = CharField()
	email = CharField()
	_photo = BlobField(null = True)

	@property
	def photo(self):
		return self._photo

	@photo.setter
	def photo(self, image_file):
		image = Image.open(image_file)
		image.thumbnail((500,500), Image.ANTIALIAS) # Replace with image compression! Bytea max size is 1GB.
		image.save("tmp.jpg")
		tmp = open("tmp.jpg", "r")
		self._photo = tmp.read()
		remove("tmp.jpg")
	
	income = CharField()
	budget = IntegerField()
	
	city = CharField()
	state = CharField()
	latitude = DoubleField(null = True)
	longitude = DoubleField(null = True)

	customer = ForeignKeyField(Customer, related_name = "students")

	def save(self, *args, **kwargs):
		if self.latitude is None:
			geolocator = Nominatim()
			location = geolocator.geocode(str(self.city + ", " + self.state))
			self.latitude, self.longitude = location.latitude, location.longitude

		return super(Student, self).save(*args, **kwargs)

	class Meta:
		database = database
		indexes = ((("name", "email", "income", "budget", "city", "state"), True),) # This make it impossible to make a duplicate student.


class Recipe(BaseModel):
	career = ForeignKeyField(Career, related_name = "recipes")
	number = IntegerField()

	def duration(self):
		duration = 0
		for step in self.steps:
			duration += step.duration
		return duration

	def sorted_steps(self): # Steps aren't returned in any particular order; this sorts them.
		steps = []
		for step in self.steps:
			steps.append(step)
		return steps


class Step(BaseModel):
	recipe = ForeignKeyField(Recipe, related_name = "steps")

	number = IntegerField()
	title = CharField()
	description = TextField()
	
	school_kind = CharField()
	duration = IntegerField()
	cips = ArrayField(CharField)
	sort_by = CharField()

	class Meta:
		order_by = ("number",)


class Report(BaseModel):
	student = ForeignKeyField(Student, related_name = "reports")
	career = ForeignKeyField(Career)
	published = BooleanField(default = False)

	def sorted_pathways(self): # Pathways aren't returned in any particular order; this sorts them by ROI.
		pathways = []
		for p in self.pathways:
			pathways.append(p)
		pathways.sort(key = lambda p: p.roi(), reverse = True)
		return pathways


class Pathway(BaseModel):
	report = ForeignKeyField(Report, related_name = "pathways")
	low_data = BooleanField(default = False)

	def sorted_steps(self): # Steps aren't returned in any particular order; this sorts them.
		steps = []
		for step in self.pathway_steps:
			steps.append(step)
		return steps

	def cost(self):
		cost = 0
		for step in self.pathway_steps:
			cost += step.cost
		return cost

	def duration(self):
		duration = 0
		for pathway_step in self.pathway_steps:
			duration += pathway_step.duration()
		return duration

	def median_salary(self):
		pathway_steps = self.sorted_steps()
		salary = pathway_steps[-1].median_salary()
		return salary

	def roi(self):
		total_cost = self.cost()
		gains = self.median_salary()*20
		roi = (gains-total_cost)/total_cost
		roi = float("{0:.2f}".format(roi))
		return roi


class Pathway_Step(BaseModel):
	pathway = ForeignKeyField(Pathway, related_name = "pathway_steps")
	program = ForeignKeyField(Program)
	step = ForeignKeyField(Step)

	number = IntegerField()
	cost = IntegerField()

	def title(self):
		return self.step.title

	def description(self):
		return self.step.description

	def duration(self):
		return self.step.duration

	def median_salary(self):
		return self.program.median_salary

	class Meta:
		order_by = ("number",)
