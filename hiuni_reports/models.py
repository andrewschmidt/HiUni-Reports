# Just the data model.

from peewee import *
from playhouse.postgres_ext import *

from hiuni_reports import application

from geopy.geocoders import Nominatim
from . import bcrypt

import boto
from boto.s3.key import Key
from werkzeug import secure_filename

from os import remove
from PIL import Image


# DATABASE	
db = application.config["DATABASE"]

database = PostgresqlExtDatabase(
	db["name"],
	host = db["host"],
	port = db["port"],
	user = db["user"],
	password = db["password"]
)

# S3
s3 = boto.connect_s3(application.config["AWS_ACCESS_KEY_ID"], application.config["AWS_SECRET_ACCESS_KEY"])

# Get a handle to the S3 bucket:
try:
	bucket = s3.get_bucket(application.config["BUCKET"])
except Exception:
	print "An error occurred connecting to the S3 bucket."

if bucket is None:
	bucket = s3.create_bucket(application.config["BUCKET"])
	print "Creating an S3 bucket called '" + application.config["BUCKET"] + "'."



# MODELS

class BaseModel(Model):
	class Meta:
		database = database


# USER AUTHENTICATION-RELATED MODELS

class Customer(BaseModel):
	is_student = BooleanField(default = True)
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
	nicknames = ArrayField(CharField, null = True)
	image_url = CharField(null = True)
	description = TextField(null = True)

	@property
	def image(self):
		return self.image_url # I should return the file from S3 here, but for now I'm just returning the image_url.

	@image.setter
	def image(self, file):
		filename = self.name + file.filename[-4:]
		filename = secure_filename(filename)
		data = file.read()

		key = bucket.get_key("career_images/" + filename)
		if key is None:
			key = bucket.new_key("career_images/" + filename)

		key.set_contents_from_string(data)
		key.set_acl('public-read')
		self.image_url = key.generate_url(expires_in = 0, query_auth = False)


class Student(Model):
	name = CharField()
	first_name = CharField()
	last_name = CharField()
	email = CharField()
	_photo = BlobField(null = True)

	@property
	def photo(self):
		return self._photo

	@photo.setter
	def photo(self, image_file):
		try:
			image = Image.open(image_file)
			image.thumbnail((1000,1000), Image.ANTIALIAS) # Replace with image compression! Bytea max size is 1GB.
			image.save("tmp.jpg")
			tmp = open("tmp.jpg", "r")
			self._photo = tmp.read()
			remove("tmp.jpg")
		except Exception:
			self._photo = None
	
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
	tagline = CharField(null = True)

	def cost(self):
		cost = 0
		for step in self.steps:
			cost += step.cost
		return cost

	def duration(self):
		duration = 0
		for step in self.steps:
			duration += step.duration
		return duration

	def median_salary(self):
		salary = 0
		for step in self.steps:
			salary = step.median_salary
		return salary

	def roi(self):
		total_cost = self.cost()
		gains = self.median_salary()*20
		roi = (gains-total_cost)/total_cost
		roi = float("{0:.2f}".format(roi))
		return roi


class Pathway_Step(BaseModel):
	pathway = ForeignKeyField(Pathway, related_name = "steps")
	program = ForeignKeyField(Program)
	step = ForeignKeyField(Step)

	number = IntegerField()
	title = CharField(null = True)
	cost = IntegerField()
	duration = IntegerField(null = True)
	median_salary = IntegerField(null = True)
	description = TextField(null = True)

	def save(self, *args, **kwargs):
		if self.title is None: self.title = self.step.title
		if self.duration is None: self.duration = self.step.duration
		if self.median_salary is None: self.median_salary = self.program.median_salary
		if self.description is None: self.description = self.step.description
		
		return super(Pathway_Step, self).save(*args, **kwargs)

	class Meta:
		order_by = ("number",)
