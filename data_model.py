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
<<<<<<< HEAD
	total_price = HStoreField() # To setup, run "CREATE EXTENSION hstore;" for hiuni_database from psql.
=======
	total_price = HStoreField()
>>>>>>> origin/building-the-solver
	net_price = HStoreField() # For public institutions, net price refers to net price for in-state students only.

	def programs(self):
		return Program.select().where(School == self)


class Program(BaseModel):
	school = ForeignKeyField(School, related_name = "programs")
	name = CharField()
	cip = CharField()
	median_salary = IntegerField()