# Just the data model.


from peewee import *
database = PostgresqlDatabase("hiuni_database", user = "Andrew")


class BaseModel(Model):
	class Meta:
		database = database


class School(BaseModel):
	name = CharField()
	ipeds_id = IntegerField()

	def programs(self):
		return Program.select().where(School == self)


class Program(BaseModel):
	school = ForeignKeyField(School, related_name = "programs")
	name = CharField()
	cip = FloatField()
	median_salary = IntegerField()