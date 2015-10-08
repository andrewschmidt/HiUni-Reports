# The data helper -- functions to work with our database.
# This includes importing data.
# But it should not include ROI/sorting algorithms.


from data_model import * # The data model & the database connection.
import xlrd # For reading Excel workbooks.


xls = "PayScale Sample (altered).xlsx" # The current Excel file w/ data from PayScale.


def get_xls_sheet(name):
	# Load the workbook & sheet:
	book = xlrd.open_workbook(name)
	sheet = book.sheet_by_name("4-Digit CIP - Experienced Pay")

	return sheet


def get_school_names_from_xls_sheet(sheet):
	school_names = []
	
	number_of_rows = sheet.nrows - 1

	cell_values = sheet.col_values(1, start_rowx = 1, end_rowx = None)

	for value in cell_values:
		if not value in school_names:
			school_names.append(value)

	return school_names


def get_school_ids_from_xls_sheet(sheet):
	school_ids = []
	
	number_of_rows = sheet.nrows - 1

	cell_values = sheet.col_values(0, start_rowx = 1, end_rowx = None)

	for value in cell_values:
		if not value in school_ids:
			school_ids.append(value)

	return school_ids


def get_programs_data_from_xls_sheet(sheet, for_school):
	school = for_school
	number_of_rows = sheet.nrows
	
	# Let's search the sheet for programs for our school, and return the basic data about them:
	names = []
	cips = []
	median_salaries = []

	for row in range(number_of_rows):
		row_id = sheet.cell_value(rowx = row, colx = 0)
		
		if row_id == school.ipeds_id:
			cips.append(sheet.cell_value(rowx = row, colx = 3))
			names.append(sheet.cell_value(rowx = row, colx = 2))
			median_salaries.append(sheet.cell_value(rowx = row, colx = 5))

	return names, cips, median_salaries


def update_programs_from_xls_sheet(sheet, for_school):
	school = for_school
	number_of_rows = sheet.nrows

	names, cips, median_salaries = get_programs_data_from_xls_sheet(sheet, for_school = school)

	# Now let's add the new programs, and update the existing ones.
	updated = []
	created = []	

	for i in range(len(cips)):	
		try:
			query = Program.select().join(School)
			query_filter = (Program.cip == cips[i]) & (School.ipeds_id == school.ipeds_id)
			
			p = query.where(query_filter).get()
			
			# Only update the program if something's changed:
			if p.name != names[i] or p.median_salary != median_salaries[i]:
				p.name = names[i]
				p.median_salary = median_salaries[i]
				
				p.save()

				updated.append(p)

		except Exception:
			p = Program()
			
			p.school = school
			p.name = names[i]
			p.cip = cips[i]
			p.median_salary = median_salaries[i]

			p.save()
			
			created.append(p)

	# Print results:
	print "\nFor the", school.name + "..."
	if len(created) > 0: 
		print "    Created programs:"
		for program in created:
			print "        -", program.name

	if len(updated) > 0: 
		print "    Updated programs:"
		for program in updated:
			print "        -", program.name


def update_schools_from_xls_sheet(sheet):
	# First, let's get basic info about the schools.
	school_ids = get_school_ids_from_xls_sheet(sheet)
	school_names = get_school_names_from_xls_sheet(sheet)

	# Now let's add the new schools, and update the existing ones untouched.
	schools = []

	print ""

	for i in range(len(school_ids)):
		try:
			school = School.get(School.ipeds_id == school_ids[i])
			print school_names[i], "is already in the database. Checking for updates..."

		except Exception:
			school = School()
			print school_names[i], "isn't in the database yet. Adding it!"
		
		# Set the school's data.
		school.name = school_names[i]
		school.ipeds_id = school_ids[i]
		
		# Save the school -- either creating it, or updating it!
		school.save()

		# And append it to the array of schools we'll return.
		schools.append(school)

	return schools


def load_schools_and_programs():
	# First load the XLS spreadsheet:
	sheet = get_xls_sheet(name = xls)
	
	# Next update the schools in the sheet:
	schools = update_schools_from_xls_sheet(sheet)

	# Finally update the programs for each school in the sheet:
	for school in schools:
		update_programs_from_xls_sheet(sheet, for_school = school)


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