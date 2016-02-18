# The data helper -- functions to work with our database.
# This includes importing data.
# But it should not include ROI/sorting algorithms.



from models import * # The data model & the database connection.
import csv # For reading CSVs.
from decorators import async


ipeds_file = "IPEDS data.csv" # The CSV file w/ data from IPEDS.
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

	for row in sheet:
		ipeds_id = get_school_id_for_row(row, from_csv_sheet = sheet)
		if not ipeds_id is None:
			school_ids.append(ipeds_id)

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
			# print "Couldn't get a price for '" + key + "'."
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

	school_info = {}

	# Pluck the appropriate info from the columns in the list -- using a function to safeguard against the columns rearranging.
	school_info['ipeds_id'] = row[get_number_for_column("unitid", from_csv_sheet = sheet)] # This should always be the same.
	school_info['name'] = row[get_number_for_column("institution name", from_csv_sheet = sheet)]
	school_info['kind'] = row[get_number_for_column("Institutional category", from_csv_sheet = sheet)]
	school_info['sector'] = row[get_number_for_column("Sector of institution", from_csv_sheet = sheet)]
	
	school_info['admission_rate'] = row[get_number_for_column("Percent admitted - total", from_csv_sheet = sheet)]
	if school_info['admission_rate'] == "": school_info['admission_rate'] = None
	
	school_info['city'] = row[get_number_for_column("City location of institution", from_csv_sheet = sheet)]
	school_info['state'] = row[get_number_for_column("State abbreviation", from_csv_sheet = sheet)]

	school_info["latitude"] = row[get_number_for_column("Latitude", from_csv_sheet = sheet)]
	school_info["longitude"] = row[get_number_for_column("Longitude", from_csv_sheet = sheet)]
	
	school_info['total_price'] = get_total_prices_for_school_id(ipeds_id, from_csv_sheet = sheet)
	school_info['net_price'] = get_net_prices_for_school_id(ipeds_id, from_csv_sheet = sheet)
	
	return school_info # name, ipeds_id, kind, sector, admission_rate, city, state, latitude, longitude, total_price, net_price


def get_recipe_data_from_csv_sheet(sheet):
	row = sheet[1]

	career_name = row[get_number_for_column("Career", from_csv_sheet = sheet)]
	recipe_number = int(row[get_number_for_column("Recipe Number", from_csv_sheet = sheet)])

	return career_name, recipe_number


def get_steps_data_from_csv_sheet(sheet):
	numbers = []
	titles = []
	descriptions = []
	school_kinds = []
	durations = []
	cips = []
	sort_bys = []

	for row in sheet[1:]: # Skips the first row, which is the header row.
		numbers.append(int(row[get_number_for_column("Step", from_csv_sheet = sheet)]))
		titles.append(row[get_number_for_column("Title", from_csv_sheet = sheet)])
		descriptions.append(row[get_number_for_column("Description", from_csv_sheet = sheet)])
		school_kinds.append(row[get_number_for_column("School Kind", from_csv_sheet = sheet)])
		durations.append(int(row[get_number_for_column("Duration", from_csv_sheet = sheet)]))
		sort_bys.append(row[get_number_for_column("Sort By", from_csv_sheet = sheet)])
		
		cips_string = str(row[get_number_for_column("CIP", from_csv_sheet = sheet)])
		cips_list = cips_string.split(", ")
		cips.append(cips_list)

	return numbers, titles, descriptions, school_kinds, durations, cips, sort_bys


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

	if school.kind == "Degree-granting, associate's and certificates" and len(cips) == 0:
		# Currently we don't have any salary info for community colleges, but we do need them in the database.
		# Let's give community colleges a General Studies program, with no salary info.
		names.append("General Studies")
		cips.append("24.0102")
		median_salaries.append(None)
		reportables.append(True) # We'll set them to be reportable, even though they aren't in PayScale's database.

	return names, cips, median_salaries, reportables



# ***************** DATA MODEL INTERACTION *****************

def update_school_with_ipeds_id(ipeds_id, from_cost_sheet):
	sheet = from_cost_sheet

	# Get all the info on the school from the CSV.
	info = get_school_info_from_csv_sheet(sheet, for_ipeds_id = ipeds_id)

	# Let's figure out if the school is already in the database, or needs creating.
	try:
		school = School.get(School.ipeds_id == ipeds_id)
		print "\nUpdating info for the", school.name + "."
	except Exception:
		school = School()
		print "\nAdding a school to the database: the", info['name'] + "."

	# Then assign the new data. Peewee is smart enough to only make changes if the data actually changed:
	school.name = info['name']
	school.ipeds_id = info['ipeds_id']
	school.kind = info['kind']
	school.admission_rate = info['admission_rate']
	school.city = info['city']
	school.state = info['state']
	school.latitude = info['latitude']
	school.longitude = info['longitude']
	school.total_price = info['total_price']
	school.net_price = info['net_price']
	
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
		for name in nicknames:
			career.nicknames.append(name)

	if description is not None and description is not "":		
		career.description = description
	
	career.save()


def update_recipe_from_sheet(sheet):
	career_name, recipe_number = get_recipe_data_from_csv_sheet(sheet)

	# First let's fetch the career, creating it if necessary in the process:
	update_career(career_name, nicknames = None, description = None)
	career = Career.get(Career.name == career_name)

	# Next either update the info for an existing recipe, or create a new one. This is based on the "recipe number":
	try:
		recipe = Recipe.select().join(Career).where((Recipe.number == recipe_number) & (Recipe.career == career)).get()
		print "\nUpdating info for recipe #" + str(recipe.number), "for the career '" + career.name + ".'"
	except Exception:
		recipe = Recipe()
		print "\nAdding recipe number", str(recipe_number) + ", for the career '" + career.name + ".'"

	recipe.career = career
	recipe.number = recipe_number

	recipe.save()


def update_steps_for_recipe(recipe, from_sheet):
	sheet = from_sheet

	numbers, titles, descriptions, school_kinds, durations, cips, sort_bys = get_steps_data_from_csv_sheet(sheet)

	for i in range(len(titles)):
		try:
			step = Step.select().join(Recipe).where((Step.number == numbers[i]) & (Step.recipe == recipe)).get()
			print "    - Updating info for step #" + str(step.number) + "."
			print "        School kind:", school_kinds[i]
			print "        Duration:", str(durations[i])
			print "        CIP:", str(cips[i])
			print "        Sort by:", sort_bys[i]

		except Exception:
			step = Step()
			print "\n    - Adding step #" + str(numbers[i]) + ", titled '" + titles[i] + "'"
			print "        School kind:", school_kinds[i]
			print "        Duration:", str(durations[i])
			print "        CIP:", str(cips[i])
			print "        Sort by:", sort_bys[i]

		step.recipe = recipe

		step.number = numbers[i]
		step.title = titles[i]
		step.description = descriptions[i]
		
		step.school_kind = school_kinds[i]
		step.duration = durations[i]
		step.cips = cips[i]
		step.sort_by = sort_bys[i]

		step.save()



# ***************** EXTERNAL FUNCTIONS ******************

def save_pathway_step(pathway, program, step, number, cost):
	pathway_step = Pathway_Step()
	
	pathway_step.pathway = pathway
	pathway_step.program = program
	pathway_step.step = step

	pathway_step.number = number
	pathway_step.cost = cost

	pathway_step.save()


def save_pathway(report):
	pathway = Pathway()
	pathway.report = report
	pathway.low_data = False
	pathway.save()
	
	return pathway



# ***************** DATA IMPORT *****************

def import_recipe_from_sheet(sheet):
	update_recipe_from_sheet(sheet)

	career_name, recipe_number = get_recipe_data_from_csv_sheet(sheet)
	recipe = Recipe.select().join(Career).where((Recipe.number == recipe_number) & (Career.name == career_name)).get()

	update_steps_for_recipe(recipe, from_sheet = sheet)


def import_recipe_from_file(file_name):
	if ".csv" not in file_name:
		file_name += ".csv"

	folder = "Career Recipes/"
	folder += file_name

	print "\nSearching for", file_name + "..."

	sheet = get_csv_sheet(folder)
	import_recipe_from_sheet(sheet)


def get_ipeds_ids_in_both(cost_sheet, salary_sheet):
	cost_sheet_ids = get_school_ids_from_csv_sheet(cost_sheet)
	salary_sheet_ids = get_school_ids_from_csv_sheet(salary_sheet)

	ids_in_both = []

	for ipeds_id in cost_sheet_ids:
		if ipeds_id in salary_sheet_ids:
			ids_in_both.append(ipeds_id)

	return ids_in_both


def get_ipeds_ids_of_community_colleges(cost_sheet):
	cost_sheet_ids = get_school_ids_from_csv_sheet(cost_sheet)

	community_college_ids = []

	for ipeds_id in cost_sheet_ids:
		info = get_school_info_from_csv_sheet(cost_sheet, for_ipeds_id = ipeds_id)

		# It's pretty hard to detect genuine, public, community colleges that are likely to offer General Studies.
		# Here's my attempt:

		if info['kind'] == "Degree-granting, associate's and certificates" and info['sector'] == "Public, 2-year":
			
			red_flags = ["Technical", "Trade", "Nursing", "Health", "Tech", "Technology"]
			flagged = False
			
			for flag in red_flags:
				if flag in info['name']:
					flagged = True

			if "Community" in info['name']:
				flagged = False

			if not flagged:
				community_college_ids.append(ipeds_id)

	return community_college_ids


def import_school_data_from_sheets(cost_sheet, salary_sheet):
	print "Fetching school ids from the CSV sheets..."

	# Find out which IPEDS IDs are in both sheets:	
	ids_in_both_sheets = get_ipeds_ids_in_both(cost_sheet, salary_sheet)
	
	# And which community colleges are in the cost sheet:
	ids_of_community_colleges = get_ipeds_ids_of_community_colleges(cost_sheet)

	# Add them together:
	ids_from_sheets = ids_in_both_sheets + ids_of_community_colleges

	schools_done = 0
	total_schools = len(ids_from_sheets)

	for ipeds_id in ids_from_sheets:
		# Make or update the school for the ID:
		update_school_with_ipeds_id(ipeds_id, from_cost_sheet = cost_sheet)
		# Get the school:
		school = School.get(School.ipeds_id == ipeds_id)
		# Make or update its programs:
		update_programs_for_school(school, from_salary_sheet = salary_sheet)

		schools_done += 1
		print "\nUpdated/created", str(schools_done) + "/" + str(total_schools), "schools"


def import_school_data(): # A hands-off version of import_school_data_from_sheets().
	folder = "School Data Sources/"
	ipeds = folder+ipeds_file
	payscale = folder+payscale_file

	cost_sheet = get_csv_sheet(ipeds)
	salary_sheet = get_csv_sheet(payscale)
	print "\nLet's import!"
	import_school_data_from_sheets(cost_sheet, salary_sheet = salary_sheet)


@async
def import_school_data_async():
	import_school_data()



# ***************** DATABASE MANAGEMENT *****************

def delete_all_schools():
	# This will also remove the programs that belong to the schools.
	schools = School.select()
	for school in schools:
		school.delete_instance(recursive = True)


def delete_all_careers():
	# This should also remove related recipes and steps.
	careers = Career.select()
	for career in careers:
		career.delete_instance(recursive = True)


def delete_all_pathways():
	pathways = Pathway.select()
	for pathway in pathways:
		pathway.delete_instance(recursive = True)


def delete_all_students():
	students = Student.select()
	for student in students:
		student.delete_instance(recursive = True)


def create_tables():
	# Only run this once.
	# Remember, this doesn't create a database. Just the tables.
	# To do that, use PostgreSQL's "createdb" command.
	print "\nConnecting to the database..."
	database.connect()
	print "\nCreating tables..."
	database.create_tables([School, Program])
	database.create_tables([Career, Recipe, Step])
	database.create_tables([Student])
	database.create_tables([Pathway, Pathway_Step])


def populate_tables():
	print "\nAttempting to import schools & programs data..."
	import_school_data()


def drop_tables():
	# Only do this if you're serious.
	print "\nDropping tables..."
	# database.drop_tables([School, Program], safe = True)
	# database.drop_tables([Student], safe = True)
	# database.drop_tables([Career, Recipe, Step], safe = True)
	database.drop_tables([Pathway, Pathway_Step], safe = True)