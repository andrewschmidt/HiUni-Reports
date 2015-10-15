# The data helper -- functions to work with our database.
# This includes importing data.
# But it should not include ROI/sorting algorithms.



from data_model import * # The data model & the database connection.
import xlrd # For reading Excel workbooks.
import csv # For reading CSVs.



csv_file = "IPEDS data (altered).csv" # The CSV file w/ data from IPEDS.
xls_file = "PayScale Sample (altered).xlsx" # The current Excel file w/ data from PayScale.



# ***************** CSV FUNCTIONS *****************

def get_csv_sheet(name):
	# Load the CSV sheet:
	sheet = []

	with open(csv_file, 'rb') as f:
		reader = csv.reader(f)
	
		for row in reader:
			sheet.append(row)

	return sheet


def get_number_for_column_named(name, from_csv_sheet):
	sheet = from_csv_sheet
	header_row = sheet[0] # does this return the first row? Hope so.

	for number, column in enumerate(header_row):
		if name in column:
			return number


def get_numbers_for_columns_named(name, from_csv_sheet):
	sheet = from_csv_sheet
	header_row = sheet[0] # does this return the first row? Hope so.

	column_numbers = []

	for number, column in enumerate(header_row):
		if name in column:
			column_numbers.append(number)

	if len(column_numbers) > 1:
		return column_numbers
	else:
		column_number = column_numbers[0]
		return column_number


def get_school_ids_from_csv_sheet(sheet):
	school_ids = []
	id_column = get_number_for_column_named("unitid", from_csv_sheet = sheet)

	for row in sheet:
		ipeds_id = str(row[id_column]).rstrip(".0")
		
		if ipeds_id not in school_ids:
			school_ids.append(ipeds_id)

	return school_ids


def get_row_from_csv_sheet(sheet, for_ipeds_id):
	ipeds_id = for_ipeds_id
	column_number = get_numbers_for_columns_named("unitid", from_csv_sheet = sheet)

	for row in sheet:
		if row[column_number] == ipeds_id:
			return row


def get_school_info_from_csv_sheet(sheet, for_ipeds_id):
	ipeds_id = for_ipeds_id
	row = get_row_from_csv_sheet(sheet, for_ipeds_id = ipeds_id)

	# Pluck the appropriate info from the columns in the list -- using a function to safeguard against the columns rearranging.
	ipeds_id = row[get_number_for_column_named("unitid", from_csv_sheet = sheet)] # This should always be the same.
	name = row[get_number_for_column_named("institution name", from_csv_sheet = sheet)]
	
	city = row[get_number_for_column_named("HD2013.City location of institution", from_csv_sheet = sheet)]
	state = row[get_number_for_column_named("HD2013.State abbreviation", from_csv_sheet = sheet)]
	zip_code = row[get_number_for_column_named("HD2013.ZIP code", from_csv_sheet = sheet)]

	return name, ipeds_id



# ***************** XLS FUNCTIONS *****************

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
		value = str(value).rstrip(".0") # Convert to string, drop any trailing zero.

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
		row_id = str(sheet.cell_value(rowx = row, colx = 0)).rstrip(".0")
		
		if row_id == school.ipeds_id:
			cips.append(sheet.cell_value(rowx = row, colx = 3))
			names.append(sheet.cell_value(rowx = row, colx = 2))
			median_salaries.append(sheet.cell_value(rowx = row, colx = 5))

	return names, cips, median_salaries



# ***************** DATA MODEL INTERACTION *****************

def update_school_with_ipeds_id(ipeds_id, from_cost_sheet):
	sheet = from_cost_sheet

	# Get all the info on the school from the CSV.
	name, new_ipeds_id = get_school_info_from_csv_sheet(sheet, for_ipeds_id = ipeds_id)

	# Let's figure out if the school is already in the database, or needs creating.
	try:
		school = School.get(School.ipeds_id == ipeds_id)
		print "\nUpdating info for the", school.name + "."
	except Exception:
		school = School()
		print "\nAdding a school to the database: the", name + "."

	# Then assign the new data. Peewee is smart enough to only make changes if the data actually changed:
	school.name = name
	school.ipeds_id = new_ipeds_id

	# Finally, save it:
	school.save()


def update_info_for_school(school, from_cost_sheet):
	sheet = from_cost_sheet

	print "\nUpdating info for the", school.name + "."

	school.name, school.ipeds_id = get_school_info_from_csv_sheet(sheet, for_ipeds_id = school.ipeds_id)
		
	school.save()


def update_programs_for_school(school, from_salary_sheet):
	sheet = from_salary_sheet
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
	if len(created) > 0 or len(updated) > 0:
		print "\nFor the", school.name + "..."

	if len(created) > 0: 
		print "    Created programs:"
		for program in created:
			print "        -", program.name

	if len(updated) > 0: 
		print "    Updated programs:"
		for program in updated:
			print "        -", program.name



# ***************** IMPORT FUNCTIONS *****************

def get_ipeds_ids_in_both(cost_sheet, salary_sheet):
	cost_sheet_ids = get_school_ids_from_csv_sheet(cost_sheet)
	salary_sheet_ids = get_school_ids_from_xls_sheet(salary_sheet)

	ids_in_both = []

	for ipeds_id in cost_sheet_ids:
		if ipeds_id in salary_sheet_ids:
			ids_in_both.append(ipeds_id)

	return ids_in_both


def import_data_from_sheets(cost_sheet, salary_sheet):
	# Find out which IPEDS IDs are in both sheets:	
	ids_from_sheets = get_ipeds_ids_in_both(cost_sheet, salary_sheet)

	schools_to_update = []
	ids_of_schools_to_add = []

	for ipeds_id in ids_from_sheets:
		try:
			school = School.get(School.ipeds_id == ipeds_id)
			schools_to_update.append(school)

		except Exception:
			ids_of_schools_to_add.append(ipeds_id)

	for school in schools_to_update:
		update_school_with_ipeds_id(school.ipeds_id, from_cost_sheet = cost_sheet)
		update_programs_for_school(school, from_salary_sheet = salary_sheet)

	for ipeds_id in ids_of_schools_to_add:
		# Make a new school:
		update_school_with_ipeds_id(ipeds_id, from_cost_sheet = cost_sheet)
		# Get the new school:
		school = School.get(School.ipeds_id == ipeds_id)
		# Make its programs:
		update_programs_for_school(school, from_salary_sheet = salary_sheet)


def import_data(): # A hands-off version of import_data_from_sheets().
	cost_sheet = get_csv_sheet(csv_file)
	salary_sheet = get_xls_sheet(xls_file)
	print "\nLet's import!"
	import_data_from_sheets(cost_sheet, salary_sheet = salary_sheet)



# ***************** DATABASE MANAGEMENT *****************

def delete_all_schools():
	# This will also remove the programs that belong to the schools.
	schools = School.select()
	for school in schools:
		school.delete_instance(recursive = True)


def create_tables():
	# Only run this once.
	# Remember, this doesn't create a database. Just the tables.
	# To do that, use PostgreSQL's "createdb" command.
	print "\nConnecting to the database..."
	database.connect()
	print "\nCreating tables..."
	database.create_tables([School, Program])


def populate_tables():
	print "\nAttempting to import schools & programs data..."
	import_data()


def drop_tables():
	# Only do this if you're serious.
	print "\nDropping tables..."
	database.drop_tables([School, Program], safe = True)