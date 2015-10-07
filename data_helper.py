# The data helper -- functions to work with our database.
# This includes importing data.
# But it should not include ROI/sorting algorithms.


import xlrd # For reading Excel workbooks.
from data_model import *
from peewee import * # Our ORM.

# Connect to the database:
database = PostgresqlDatabase("hiuni_database", user = "Andrew")


def get_sheet():
		# Load the workbook & sheet:
		book = xlrd.open_workbook("PayScale Sample (altered).xlsx")
		sheet = book.sheet_by_name("4-Digit CIP - Experienced Pay")

		return sheet


def get_school_names_from_sheet(sheet):
	school_names = []
	
	number_of_rows = sheet.nrows - 1

	cell_values = sheet.col_values(1, start_rowx = 1, end_rowx = None)

	for value in cell_values:
		if not value in school_names:
			school_names.append(value)

	return school_names


def get_school_ids_from_sheet(sheet):
	school_ids = []
	
	number_of_rows = sheet.nrows - 1

	cell_values = sheet.col_values(0, start_rowx = 1, end_rowx = None)

	for value in cell_values:
		if not value in school_ids:
			school_ids.append(value)

	return school_ids


def create_programs_for_school(school, from_sheet):
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


def create_schools_from_sheet(sheet):
	# First, let's get basic info about the schools.
	school_names = get_school_names_from_sheet(sheet)
	school_ids = get_school_ids_from_sheet(sheet)

	# Let's add some schools to the database, but only if they aren't already there!
	schools = []
	existing_schools = School.select()

	print ""

	for i in range(len(school_names)):
		try:
			School.get(School.name == school_names[i])

		except Exception:
			print "Looks like the", school_names[i], "isn't in the database yet. Adding it!"
			school = School.create(name = school_names[i], ipeds_id = school_ids[i])
			schools.append(school)

		else:
			print "Duplicate school detected!"

	return schools


def load_schools_and_programs():
	# First load the spreadsheet:
	sheet = get_sheet()
	
	# Next create the schools:
	schools = create_schools_from_sheet(sheet)

	# Finally create all the programs for each school:
	for school in schools:
		create_programs_for_school(school, from_sheet = sheet)


def delete_schools():
	# This will also remove the programs that belong to the schools.
	schools = School.select()
	for school in schools:
		school.delete_instance(recursive = True)


def create_tables():
	# Only run this once.
	# Remember, this doesn't create a database.
	# To do that, use PostgreSQL's "createdb" command.
	print "\nConnecting to the database..."
	database.connect()
	print "\nCreating tables..."
	database.create_tables([School, Program])


def populate_tables():
	print "\nLoading in data..."
	load_schools_and_programs()


def drop_tables():
	# Only do this if you're serious.
	print "\nDropping tables..."
	database.drop_tables([School, Program], safe = True)