# Just the data model.


from peewee import *
from playhouse.postgres_ext import *

database = PostgresqlExtDatabase("hiuni_database", user = "Andrew")


class BaseModel(Model):
	class Meta:
		database = database


class School(BaseModel):
	name = CharField()
	ipeds_id = CharField()
	school_type = CharField()
	admission_rate = IntegerField(null = True)
	
	# Location:
	city = CharField()
	state = CharField()
	location = HStoreField()
	
	# Cost:
	total_price = HStoreField() # To setup, run "CREATE EXTENSION hstore;" for hiuni_database from psql.
	net_price = HStoreField() # For public institutions, net price refers to net price for in-state students only.

	def programs(self):
		return Program.select().where(School == self)


class Program(BaseModel):
	school = ForeignKeyField(School, related_name = "programs")
	name = CharField()
	cip = CharField()
	median_salary = IntegerField()
	reportable = BooleanField()


class Career(BaseModel):
	name = CharField()
	nicknames = ArrayField(CharField, null = True) # Neither of these are being imported yet.
	description = TextField(null = True)

	def templates(self):
		return Template.select().where(Career == self)


class Student(BaseModel):
	name = CharField()
	email = CharField()
	
	career = ForeignKeyField(Career)
	income = CharField()
	budget = IntegerField()
	
	city = CharField()
	state = CharField()
	location = HStoreField(null = True) # For storing latitude and longitude keys.


class Template(BaseModel):
	career = ForeignKeyField(Career, related_name = "templates")
	number = IntegerField()

	def steps(self):
		return Step.select().where(Template == self)

	def duration(self):
		duration = 0
		steps = Step.select().where(Template == self)
		for step in steps:
			duration += step.duration
		return duration


class Step(BaseModel):
	template = ForeignKeyField(Template, related_name = "steps")

	number = IntegerField()
	title = CharField()
	description = TextField()
	
	school_type = CharField()
	duration = IntegerField()
	cips = ArrayField(CharField)
	sort_by = CharField()