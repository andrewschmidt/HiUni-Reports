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
	kind = CharField()
	admission_rate = IntegerField(null = True)
	
	# Location:
	city = CharField()
	state = CharField()
	location = HStoreField()
	
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


class Student(BaseModel):
	name = CharField()
	email = CharField()
	
	career = ForeignKeyField(Career, null = True)
	income = CharField()
	budget = IntegerField()
	
	city = CharField()
	state = CharField()
	location = HStoreField(null = True) # For storing latitude and longitude keys.

	def sorted_pathways(self): # Pathways aren't returned in any particular order; this sorts them by ROI.
		pathways = []
		for p in self.pathways:
			pathways.append(p)
		pathways.sort(key = lambda p: p.roi(), reverse = True)
		return pathways


class Template(BaseModel):
	career = ForeignKeyField(Career, related_name = "templates")
	number = IntegerField()

	def duration(self):
		duration = 0
		for step in self.steps:
			duration += step.duration
		return duration


class Step(BaseModel):
	template = ForeignKeyField(Template, related_name = "steps")

	number = IntegerField()
	title = CharField()
	description = TextField()
	
	school_kind = CharField()
	duration = IntegerField()
	cips = ArrayField(CharField)
	sort_by = CharField()


class Pathway(BaseModel):
	student = ForeignKeyField(Student, related_name = "pathways")

	def sorted_steps(self): # Steps aren't returned in any particular order; this sorts them.
		steps = []
		for step in self.pathway_steps:
			steps.append(step)
		steps.sort(key = lambda s: s.number)
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
		# if len(self.pathway_steps) > 1:
		pathway_steps = self.sorted_steps()
		last_pathway_step = pathway_steps[-1]
			# last_pathway_step = self.sorted_steps()[len(self.pathway_steps)-1]
		# else:
		# 	last_pathway_step = self.pathway_steps[0]
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
