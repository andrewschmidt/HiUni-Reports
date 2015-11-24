# The data helper -- functions to work with our database.
# This includes importing data.
# But it should not include ROI/sorting algorithms.



from data_model import * # The data model & the database connection.
import xlrd # For reading Excel workbooks.
import csv # For reading CSVs.


ipeds_file = "IPEDS data (altered).csv" # The CSV file w/ data from IPEDS.
payscale_file = "2015-10 Four Digit Experienced Pay (Converted).csv" # The CSV file w/ data from PayScale.


# ***************** CSV FUNCTIONS *****************

def get_csv_sheet(name):
	# Load the CSV sheet:
	sheet = []

	with open(name, 'rb') as f:
		reader = csv.reader(f)
	
		for row in reader:
			sheet.append(row)

	return sheet


def get_number_for_column(name, from_csv_sheet):
	sheet = from_csv_sheet
	header_row = sheet[0] # does this return the first row? Hope so.

	if header_row[0] == name:
		return 0

	for number, column in enumerate(header_row):
		if name in column:
			return number


def get_numbers_for_columns(name, from_csv_sheet):
	sheet = from_csv_sheet
	header_row = sheet[0]

	column_numbers = []

	for number, column in enumerate(header_row):
		if name in column:
			column_numbers.append(number)

	return column_numbers
		
		
def get_school_id_for_row(row, from_csv_sheet):
	sheet = from_csv_sheet

	id_column = get_number_for_column("unitid", from_csv_sheet = sheet)
	if id_column is None:
		id_column = get_number_for_column("IPEDS ID", from_csv_sheet = sheet)

	try:
		school_id = str(int(row[id_column])) # This wasn't working: str(row[id_column]).rstrip(".0")
		# print "SCHOOL_ID_FOR_ROW: Converted cell to integer, then string. Cell contained:", str(row[id_column]) + ", converted to:", school_id
		return school_id

	except Exception:
		# print "SCHOOL_ID_FOR_ROW: Failed to convert cell to integer, then to string. Cell contains:", str(row[id_column])
		return None
	

def get_row_for_school_id(ipeds_id, from_csv_sheet):
	sheet = from_csv_sheet
	column_number = get_number_for_column("unitid", from_csv_sheet = sheet)

	for row in sheet:
		row_id = get_school_id_for_row(row, from_csv_sheet = sheet)
		if row_id == ipeds_id:
			return row	
		
		
def get_number_for_nonempty_column(name, for_ipeds_id, from_csv_sheet):
	sheet = from_csv_sheet
	header_row = sheet[0]
	ipeds_id = for_ipeds_id
	
	column_numbers = get_numbers_for_columns(name, from_csv_sheet = sheet)
	row = get_row_for_school_id(ipeds_id, from_csv_sheet = sheet)
	
	for column_number in column_numbers:
		if not row[column_number] == "":
			return column_number
			

def get_school_ids_from_csv_sheet(sheet):
	school_ids = []
	# id_column = get_number_for_column("unitid", from_csv_sheet = sheet)

	# if id_column is None:
	# 	id_column = get_number_for_column("IPEDS ID", from_csv_sheet = sheet)

	for row in sheet:
		ipeds_id = get_school_id_for_row(row, from_csv_sheet = sheet)
		if not ipeds_id is None:
			school_ids.append(ipeds_id)

	# for row in sheet:
	# 	if row[id_column] != "unitid":
	# 		try:
	# 			ipeds_id = str(int(row[id_column])) # This wasn't working: str(row[id_column]).rstrip(".0")
				
	# 			print "SCHOOL_IDS_FROM_CSV_SHEET: Converted cell to integer, then string. Cell contained:", str(row[id_column]) + ", converted to:", ipeds_id
				
	# 			if ipeds_id not in school_ids:
	# 				school_ids.append(ipeds_id)

	# 		except Exception:
	# 			print "SCHOOL_IDS_FROM_CSV_SHEET: Failed to convert cell to integer, then to string. Cell contains:", str(row[id_column])
	# 			pass
		

	return school_ids
	
	
def get_total_prices_for_school_id(ipeds_id, from_csv_sheet):
	sheet = from_csv_sheet
	row = get_row_for_school_id(ipeds_id, from_csv_sheet = sheet)
	
	total_price = {}
	total_price_keys = ["in-state students living on campus", "in-state students living off campus (with family)", "out-of-state students living on campus"]
	
	for key in total_price_keys:
		try:
			total_price[key] = row[get_number_for_nonempty_column(key, for_ipeds_id = ipeds_id, from_csv_sheet = sheet)]
		except Exception:
			pass
		
	return total_price
	
	
def get_net_prices_for_school_id(ipeds_id, from_csv_sheet):
	sheet = from_csv_sheet
	row = get_row_for_school_id(ipeds_id, from_csv_sheet = sheet)
	
	net_price = {}
	net_price_keys = ["0-30,000", "30,001-48,000", "48,001-75,000", "75,001-110,000", "over 110,000"]
	
	for key in net_price_keys:
		try:
			net_price[key] = row[get_number_for_nonempty_column(("income "+key), for_ipeds_id = ipeds_id, from_csv_sheet = sheet)]
		except Exception:
			pass
		
	# Also get the average net price:
	try:	
		net_price["average"] = row[get_number_for_nonempty_column("Average net price", for_ipeds_id = ipeds_id, from_csv_sheet = sheet)]
	except Exception:
		pass
		
	return net_price
	

def get_school_info_from_csv_sheet(sheet, for_ipeds_id):
	ipeds_id = for_ipeds_id
	row = get_row_for_school_id(ipeds_id, from_csv_sheet = sheet)

	# Pluck the appropriate info from the columns in the list -- using a function to safeguard against the columns rearranging.
	ipeds_id = row[get_number_for_column("unitid", from_csv_sheet = sheet)] # This should always be the same.
	name = row[get_number_for_column("institution name", from_csv_sheet = sheet)]
	school_type = row[get_number_for_column("HD2013.Institutional category", from_csv_sheet = sheet)]
	
	admission_rate = row[get_number_for_column("DRVIC2013_RV.Percent admitted - total", from_csv_sheet = sheet)]
	if admission_rate == "": admission_rate = None
	
	city = row[get_number_for_column("HD2013.City location of institution", from_csv_sheet = sheet)]
	state = row[get_number_for_column("HD2013.State abbreviation", from_csv_sheet = sheet)]

	latitude = row[get_number_for_column("Latitude", from_csv_sheet = sheet)]
	longitude = row[get_number_for_column("Longitude", from_csv_sheet = sheet)]
	location = {"latitude": latitude, "longitude": longitude}
	
	total_price = get_total_prices_for_school_id(ipeds_id, from_csv_sheet = sheet)
	net_price = get_net_prices_for_school_id(ipeds_id, from_csv_sheet = sheet)
	
	return name, ipeds_id, school_type, admission_rate, city, state, location, total_price, net_price


def get_template_data_from_csv_sheet(sheet):
	row = sheet[1]

	career_name = row[get_number_for_column("Career", from_csv_sheet = sheet)]
	template_number = int(row[get_number_for_column("Template Number", from_csv_sheet = sheet)])

	return career_name, template_number


def get_steps_data_from_csv_sheet(sheet):
	numbers = []
	titles = []
	descriptions = []
	school_types = []
	durations = []
	cips = []
	sort_bys = []

	for row in sheet[1:]: # Skips the first row, which is the header row.
		numbers.append(int(row[get_number_for_column("Step", from_csv_sheet = sheet)]))
		titles.append(row[get_number_for_column("Title", from_csv_sheet = sheet)])
		descriptions.append(row[get_number_for_column("Description", from_csv_sheet = sheet)])
		school_types.append(row[get_number_for_column("School Type", from_csv_sheet = sheet)])
		durations.append(int(row[get_number_for_column("Duration", from_csv_sheet = sheet)]))
		sort_bys.append(row[get_number_for_column("Sort By", from_csv_sheet = sheet)])
		
		cips_string = str(row[get_number_for_column("CIP", from_csv_sheet = sheet)])
		cips_list = cips_string.split(", ")
		cips.append(cips_list)

	return numbers, titles, descriptions, school_types, durations, cips, sort_bys


def get_school_names_from_csv_sheet(sheet):
	school_names = []
	name_column = get_number_for_column("School", from_csv_sheet = sheet)

	for row in sheet:
		if not row[name_column] in school_names:
			school_names.append(row[name_column])

	return school_names


def get_programs_data_from_csv_sheet(sheet, for_school):
	school = for_school
	
	id_column = get_number_for_column("IPEDS ID", from_csv_sheet = sheet)
	name_column = get_number_for_column("Major", from_csv_sheet = sheet)
	cip_column = get_number_for_column("CIP Code", from_csv_sheet = sheet)
	median_salary_column = get_number_for_column("Median Pay", from_csv_sheet = sheet)
	reportable_column = get_number_for_column("Report or Don't Report", from_csv_sheet = sheet)

	# Let's search the sheet for programs for our school, and return the basic data about them:
	names = []
	cips = []
	median_salaries = []
	reportables = []

	for row in sheet:
		if row[id_column] == school.ipeds_id:
			names.append(row[name_column])
			cips.append(row[cip_column])
			median_salaries.append(row[median_salary_column])
			if row[reportable_column] == "Don't Report":
				reportables.append(False)
			else:
				reportables.append(True)

	return names, cips, median_salaries, reportables



# ***************** DATA MODEL INTERACTION *****************

def update_school_with_ipeds_id(ipeds_id, from_cost_sheet):
	sheet = from_cost_sheet

	# Get all the info on the school from the CSV.
	name, new_ipeds, school_type, admission_rate, city, state, location, total_price, net_price = get_school_info_from_csv_sheet(sheet, for_ipeds_id = ipeds_id)

	# Let's figure out if the school is already in the database, or needs creating.
	try:
		school = School.get(School.ipeds_id == ipeds_id)
		print "\nUpdating info for the", school.name + "."
	except Exception:
		school = School()
		print "\nAdding a school to the database: the", name + "."

	# Then assign the new data. Peewee is smart enough to only make changes if the data actually changed:
	school.name = name
	school.ipeds_id = new_ipeds
	school.school_type = school_type
	school.admission_rate = admission_rate
	school.city = city
	school.state = state
	school.location = location
	school.total_price = total_price
	school.net_price = net_price
	
	# Finally, save it:
	school.save()


def update_programs_for_school(school, from_salary_sheet):
	sheet = from_salary_sheet

	names, cips, median_salaries, reportables = get_programs_data_from_csv_sheet(sheet, for_school = school)
	
	# Now let's add the new programs, and update the existing ones.
	updated = []
	created = []	

	for i in range(len(cips)):	
		try:
			query = Program.select().join(School)
			query_filter = (Program.cip == cips[i]) & (School.ipeds_id == school.ipeds_id)
			
			p = query.where(query_filter).get()
			
			# Only update the program if something's changed:
			if p.name != names[i] or p.median_salary != median_salaries[i] or p.reportable != reportables[i]:
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
			p.reportable = reportables[i]

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


def update_career(name, nicknames, description):
	try:
		career = Career.get(Career.name == name)
		print "\nUpdating info for the career '" + career.name + "'."
	except Exception:
		career = Career()
		print "\nAdding a career to the database:", name + "."

	career.name = name
	
	if nicknames is not None and nicknames is not "":
		print "Nicknames for the career were not None OR:"
		for name in nicknames:
			career.nicknames.append(name)

	if description is not None and description is not "":		
		career.description = description
	
	career.save()


def update_template_from_sheet(sheet):
	career_name, template_number = get_template_data_from_csv_sheet(sheet)

	# First let's fetch the career, creating it if necessary in the process:
	update_career(career_name, nicknames = None, description = None)
	career = Career.get(Career.name == career_name)

	# Next either update the info for an existing template, or create a new one. This is based on the "template number":
	try:
		template = Template.select().join(Career).where((Template.number == template_number) & (Template.career == career)).get()
		print "\nUpdating info for the template number", template.number, "for the career '" + career.name + ".'"
	except Exception:
		template = Template()
		print "\nAdding template number", str(template_number) + ", for the career '" + career.name + ".'"

	template.career = career
	template.number = template_number

	template.save()


def update_steps_for_template(template, from_sheet):
	sheet = from_sheet

	numbers, titles, descriptions, school_types, durations, cips, sort_bys = get_steps_data_from_csv_sheet(sheet)

	for i in range(len(titles)):
		try:
			step = Step.select().join(Template).where((Step.number == numbers[i]) & (Step.template == template)).get()
			print "    - Updating info for step #" + str(step.number) + "."
		except Exception:
			step = Step()
			print "    - Adding a step, titled '" + titles[i] + "'"

		step.template = template

		step.number = numbers[i]
		step.title = titles[i]
		step.description = descriptions[i]
		
		step.school_type = school_types[i]
		step.duration = durations[i]
		step.cips = cips[i]
		step.sort_by = sort_bys[i]

		step.save()



# ***************** DATA IMPORT *****************

def import_template_from_sheet(sheet):
	update_template_from_sheet(sheet)

	career_name, template_number = get_template_data_from_csv_sheet(sheet)
	template = Template.select().join(Career).where((Template.number == template_number) & (Career.name == career_name)).get()

	update_steps_for_template(template, from_sheet = sheet)


def get_ipeds_ids_in_both(cost_sheet, salary_sheet):
	cost_sheet_ids = get_school_ids_from_csv_sheet(cost_sheet)
	salary_sheet_ids = get_school_ids_from_csv_sheet(salary_sheet)

	ids_in_both = []

	for ipeds_id in cost_sheet_ids:
		if ipeds_id in salary_sheet_ids:
			ids_in_both.append(ipeds_id)

	return ids_in_both


def import_school_data_from_sheets(cost_sheet, salary_sheet):
	# Find out which IPEDS IDs are in both sheets:	
	ids_from_sheets = get_ipeds_ids_in_both(cost_sheet, salary_sheet)

	schools_done = 0
	total_schools = ids_from_sheets.count()

	for ipeds_id in ids_from_sheets:
		# Make or update the school for the ID:
		update_school_with_ipeds_id(ipeds_id, from_cost_sheet = cost_sheet)
		# Get the school:
		school = School.get(School.ipeds_id == ipeds_id)
		# Make or update its programs:
		update_programs_for_school(school, from_salary_sheet = salary_sheet)

		schools_done += 1
		print "\nUpdated/created", str(schools_done) + "/" + str(total_schools), "schools\n"

	# schools_to_update = []
	# ids_of_schools_to_add = []

	# for ipeds_id in ids_from_sheets:
	# 	try:
	# 		school = School.get(School.ipeds_id == ipeds_id)
	# 		schools_to_update.append(school)

	# 	except Exception:
	# 		ids_of_schools_to_add.append(ipeds_id)

	# for school in schools_to_update:
	# 	update_school_with_ipeds_id(school.ipeds_id, from_cost_sheet = cost_sheet)
	# 	update_programs_for_school(school, from_salary_sheet = salary_sheet)

	# for ipeds_id in ids_of_schools_to_add:
	# 	# Make a new school:
	# 	update_school_with_ipeds_id(ipeds_id, from_cost_sheet = cost_sheet)
	# 	# Get the new school:
	# 	school = School.get(School.ipeds_id == ipeds_id)
	# 	# Make its programs:
	# 	update_programs_for_school(school, from_salary_sheet = salary_sheet)


def import_school_data(): # A hands-off version of import_school_data_from_sheets().
	cost_sheet = get_csv_sheet(ipeds_file)
	salary_sheet = get_csv_sheet(payscale_file)
	print "\nLet's import!"
	import_school_data_from_sheets(cost_sheet, salary_sheet = salary_sheet)



# ***************** DATABASE MANAGEMENT *****************

def delete_all_schools():
	# This will also remove the programs that belong to the schools.
	schools = School.select()
	for school in schools:
		school.delete_instance(recursive = True)


def delete_all_careers():
	# This should also remove related templates and steps.
	careers = Career.select()
	for career in careers:
		career.delete_instance(recursive = True)


def create_tables():
	# Only run this once.
	# Remember, this doesn't create a database. Just the tables.
	# To do that, use PostgreSQL's "createdb" command.
	print "\nConnecting to the database..."
	database.connect()
	print "\nCreating tables..."
	database.create_tables([School, Program])
	database.create_tables([Career, Template, Step])


def populate_tables():
	print "\nAttempting to import schools & programs data..."
	import_school_data()


def drop_tables():
	# Only do this if you're serious.
	print "\nDropping tables..."
	database.drop_tables([School, Program], safe = True)
	database.drop_tables([Career, Template, Step], safe = True)