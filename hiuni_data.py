# The data model, and classes related to managing data in and out.

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



import xlrd

class data_helper:
	
	def __init__(self):
		return


	def get_sheet(self):
		# Load the workbook & sheet:
		book = xlrd.open_workbook("PayScale Sample (altered).xlsx")
		sheet = book.sheet_by_name("4-Digit CIP - Experienced Pay")

		return sheet


	def get_school_names_from_sheet(self, sheet):
		school_names = []
		
		number_of_rows = sheet.nrows - 1

		cell_values = sheet.col_values(1, start_rowx = 1, end_rowx = None)

		for value in cell_values:
			if not value in school_names:
				school_names.append(value)

		return school_names


	def get_school_ids_from_sheet(self, sheet):
		school_ids = []
		
		number_of_rows = sheet.nrows - 1

		cell_values = sheet.col_values(0, start_rowx = 1, end_rowx = None)

		for value in cell_values:
			if not value in school_ids:
				school_ids.append(value)

		return school_ids


	def create_programs_for_school(self, school, from_sheet):
		programs = []

		sheet = from_sheet
		number_of_rows = sheet.nrows

		for row in range(number_of_rows):
			row_id = sheet.cell_value(rowx = row, colx = 0)
			program_name = sheet.cell_value(rowx = row, colx = 2)
			cip = sheet.cell_value(rowx = row, colx = 3)
			median_salary = sheet.cell_value(rowx = row, colx = 5)

			if row_id == school.ipeds_id:
				program = Program.create(school = school, name = program_name, cip = cip, median_salary = median_salary)


	def create_schools_from_sheet(self, sheet):
		# First, let's get basic info about the schools.
		school_names = self.get_school_names_from_sheet(sheet)
		school_ids = self.get_school_ids_from_sheet(sheet)

		# Let's add some schools to the database, but only if they aren't already there!
		schools = []
		existing_schools = School.select()

		for i in range(len(school_names)):
			try:
				School.get(School.name == school_names[i])

			except Exception:
				print "\nLooks like the", school_names[i], "isn't in the database yet. Adding it!"
				school = School.create(name = school_names[i], ipeds_id = school_ids[i])
				schools.append(school)

			# else:
			# 	print "Duplicate detected!"

		return schools


	def load_schools_and_programs(self):
		# First load the spreadsheet:
		sheet = self.get_sheet()
		
		# Next create the schools:
		schools = self.create_schools_from_sheet(sheet)

		# Finally create all the programs for each school:
		for school in schools:
			self.create_programs_for_school(school, from_sheet = sheet)


	def create_database(self):
		# Only run this once.
		database.connect()
		# database.create_tables([School, Program]) #Seriously, just once!
		self.load_schools_and_programs()


	def delete_schools(self):
		# Truncate, meaning, delete all data.
		schools = School.select()
		for school in schools:
			school.delete_instance(recursive = True)
