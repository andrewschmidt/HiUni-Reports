# Functions to help build pathways.

from models import *
import data_helper
from decorators import async

from geopy.distance import great_circle


unsafe_search_allowed = True


def calculate_roi(cost, gains):
	cost = float(cost)
	gains = float(gains)
	
	roi = (gains-cost)/cost
	roi = float("{0:.2f}".format(roi))
	
	return roi


def cost_for_school(school, duration, income_level, home_state):
	if school.state == home_state:
		# First get whatever net price we have:
		try:
			net_cost = int(school.net_price[income_level])
		except:
			try:
				net_cost = int(school.net_price["average"])
			except:
				net_cost = None

		# Then get a total price:
		if school.kind == "Degree-granting, associate's and certificates":    # Instead of hardcoding this, it'd be interesting to get a student's distance to a school-- 
			situation = "in-state students living off campus (with family)"   # and if it's close enough, default to this.
		else:
			situation = "in-state students living on campus"

		try:
			total_cost = int(school.total_price[situation])
		except:
			total_cost = None

		# Now find the lowest cost that's not None:
		if net_cost is not None and total_cost is not None:
			if net_cost < total_cost:
				cost = net_cost
			else:
				cost = total_cost

		elif net_cost is None: 
			cost = total_cost

		elif total_cost is None: 
			cost = net_cost
	
	else:
		cost = int(school.total_price.get("out-of-state students living on campus"))
		if cost is None:
			print "Out of state cost was none!"
			return None

	cost *= duration

	return cost
	

def roi_for_program(program, duration, income_level, home_state):
	school = program.school
	
	try: 
		gains = int(program.median_salary)*20 # Let's use a 20-year ROI for now.
		cost = cost_for_school(program.school, duration = duration, income_level = income_level, home_state = home_state)
		
		roi = calculate_roi(cost, gains)
		
		return roi
	
	except Exception:
 		# print "Error getting ROI for", program.name, "at", school.name + "." # Activate this only to debug.
		return None
		
		
def programs_by_roi_for_cip(cip, duration, income_level, home_state, only_reportable):
	if only_reportable: 
		query = (
			(Program.cip == cip) & 
			(Program.reportable == True) & 
			(Program.median_salary.is_null(False)))
	else:
		query = (
			(Program.cip == cip) & 
			(Program.median_salary.is_null(False)))

	programs = []
	
	for program in Program.select().where(query):
		programs.append(program)
	
	programs.sort(key = lambda p: roi_for_program(p, duration = duration, income_level = income_level, home_state = home_state), reverse = True)
	
	return programs


def check_school_kind(program, step):
	school = program.school
	if school.kind == step.school_kind:
		# print "School kind '" + school.kind + "' DOES mach the kind called for:", step.school_kind + "."
		return True
	else:
		# print "School kind '" + school.kind + "' does not match kind called for:", step.school_kind + "."
		return False


def find_programs_near(latitude, longitude, distance, kind, cip):
	latitude_str = str(latitude)
	longitude_str = str(longitude)

	long_lat = str(longitude_str + ", " + latitude_str)
	distance = str(distance)

	query_string = "SELECT * FROM school WHERE earth_box(ll_to_earth("+long_lat+"), "+distance+") @> ll_to_earth(longitude, latitude) AND kind = '"+kind+"' ORDER BY earth_distance(ll_to_earth("+long_lat+"), ll_to_earth(longitude, latitude));"
	
	schools = School.raw(query_string)
	programs = []

	for school in schools:
		try:
			program = Program.select().join(School).where((Program.cip == cip) & (School.ipeds_id == school.ipeds_id)).get()
			programs.append(program)
		except Exception:
			print "\nDidn't find the right program at nearby school", school.name + "."

	return programs


def distance_between(place_1, place_2):
	point_1 = (place_1.latitude, place_1.longitude)
	point_2 = (place_2.latitude, place_2.longitude)

	distance = great_circle(point_1, point_2).miles	
	return distance


def programs_by_distance_for_cip(cip, school_kind, student, only_reportable):	
	if only_reportable:
		possible_programs = find_programs_near(latitude = student.latitude, longitude = student.longitude, distance = 7500, kind = school_kind, cip = cip)
		programs = []
		
		for program in possible_programs:
			if program.reportable:
				programs.append(program)

	else:
		programs = find_programs_near(latitude = student.latitude, longitude = student.longitude, distance = 7500, kind = school_kind, cip = cip)

	checked_programs = []
	for program in programs:
		if distance_between(student, program.school) < 30.0: # Max distance
			checked_programs.append(program)
	
	checked_programs.sort(key = lambda p: distance_between(student, p.school)) # Put them in order of closest to furthest.
	
	print "\nSorted:"
	for program in checked_programs:
		print "   - " + program.school.name + " -- " + str(distance_between(student, program.school)) + " miles away"
	print " "
	
	return checked_programs


def programs_by_roi_for_step(step, student):
	safe_search = True

	programs = []

	for cip in step.cips:
		p = programs_by_roi_for_cip(cip = cip, duration = step.duration, income_level = student.income, home_state = student.state, only_reportable = True)
		
		if len(p) == 0:
			p = programs_by_roi_for_cip(cip = cip, duration = step.duration, income_level = student.income, home_state = student.state, only_reportable = False)
			safe_search = False
		
		if len(p) > 0:
			for program in p:
				if check_school_kind(program, step) is True:
					programs.append(program)

	# The function we used to fetch programs sorts them by ROI.
	# But if we called it multiple times, our array isn't properly sorted.
	# Let's fix that:
	if len(step.cips) > 1:
		programs.sort(key = lambda p: roi_for_program(p, duration = step.duration, income_level = student.income, home_state = student.state), reverse = True)

	return programs, safe_search


def programs_by_distance_for_step(step, student):
	safe_search = True

	programs = []

	for cip in step.cips:
		p = programs_by_distance_for_cip(cip = cip, school_kind = step.school_kind, student = student, only_reportable = True)

		if len(p) == 0:
			p = programs_by_distance_for_cip(cip = cip, school_kind = step.school_kind, student = student, only_reportable = False)
			safe_search = False
		
		if len(p) > 0:
			for program in p:
				if check_school_kind(program, step) is True:
					programs.append(program)

	# May need to sort by distance again here, as above.

	return programs, safe_search


def programs_for_step(step, student):
	if step.sort_by == "ROI":
		programs, safe_search = programs_by_roi_for_step(step, student)
	elif step.sort_by == "Location":
		programs, safe_search = programs_by_distance_for_step(step, student)

	if safe_search:
		used_low_data = False
		return programs, used_low_data
	elif unsafe_search_allowed:
		print "Had to use programs with low data."
		used_low_data = True
		return programs, used_low_data

	return None, None


def get_excluded_schools(report):
	schools = []
	for pathway in report.pathways:
		for step in pathway.steps:
			school = step.program.school
			if school.kind != "Community College": # It's OK to reuse community colleges.
				schools.append(step.program)
	return schools


def pathway_complete(pathway, recipe):
	# Check if we made enough pathway steps:
	if len(pathway.steps) != len(recipe.steps):
		return False
	else:
		return True


def pathway_schools_conflict(pathway_1, pathway_2):
	pathways = pathway_1, pathway_2
	school_sets = []

	for pathway in pathways:
		schools = []
		for step in pathway.steps:
			schools.append(step.program.school)
		school_sets.append(schools)

	school_sets.sort(key = lambda s: len(s), reverse = True) # The set with more schools should come first.

	for school in school_sets[0]:
		if school in school_sets[1]:
			return True

	return False


def make_pathway_from_recipe(recipe, student, report, excluded_schools, budget_modifier):
	pathway = data_helper.save_pathway(report) # Pathway steps reference their pathway, so we need it in the database right away.

	# Working through the steps backwards prioritizes the final step --
	# which is the step whose salary matters most.
	steps = []
	for step in recipe.steps:
		steps.append(step)
	steps.reverse()

	# Make as many pathway steps as we can:
	for step in steps:
		# Get all applicable programs:
		programs, used_low_data = programs_for_step(step, student)
				
		if programs is None:
			print "Couldn't find any programs."
			break
		
		# Make note of whether the pathway uses low data or not:
		if used_low_data:
			pathway.low_data = True
			pathway.save()

		print "Found", len(programs), "programs for step #" + str(step.number)

		# Then try to find one that fits juuust right:
		program_found = False
		for program in programs:
			if not program_found and program not in excluded_schools:
				try:
					cost = cost_for_school(program.school, duration = step.duration, income_level = student.income, home_state = student.state)
					
					if pathway.cost() + cost <= student.budget + budget_modifier:
						program_found = True
						data_helper.save_pathway_step(pathway = pathway, program = program, step = step, number = step.number, cost = cost)
						
						print program.name, "at", program.school.name, "works for step", step.number
					
				except Exception:
					# print program.name, "at", program.school.name, "didn't work out :("
					pass

	if not pathway_complete(pathway, recipe):
		pathway.delete_instance(recursive = True)
		return None

	# Assign the default pathway tagline.
	# I'd like to add Markdown support to this at some point.
	rounded_roi = int(round(pathway.roi()))
	pathway.tagline = "Make <b class='light darker-gray'>$" + str(rounded_roi) + "</b> for every <b class='light darker-gray'>$1</b> spent on tuition."
	pathway.save()
	
	return pathway


def make_pathway_for_every_recipe(student, report, excluded_schools, budget_modifier):
	career = report.career
	recipes = career.recipes
	good_pathways = []
		
	for recipe in recipes:
		print "\nMaking a pathway."
		print "  Career:", career.name
		print "  Recipe:", recipe.id, "\n"
		
		pathway = make_pathway_from_recipe(recipe, student, report, excluded_schools, budget_modifier)

		if pathway is not None:
			good_pathways.append(pathway)
			print "Made a pathway."

	if len(good_pathways) > 0:
		return good_pathways
	else:
		return None


def make_pathways_for_student(student, report, how_many):	
	# Prepopulate the excluded schools list with schools from any preexisting pathways:
	excluded_schools = get_excluded_schools(report)
	budget_modifier = 0
	budget_leeway = 80000

	good_pathways = []
	failed = False

	# First make pathways:
	while len(good_pathways) < how_many and not failed:
		made_pathways = make_pathway_for_every_recipe(student, report, excluded_schools, budget_modifier)

		if made_pathways is not None:
			made_pathways.sort(key = lambda p: p.roi()) # Worst to best ROI.
			
			# Let's check if any of the schools in these conflict.
			for i in range(len(made_pathways)-1):
				pathway_1 = made_pathways[i]
				try:
					pathway_2 = made_pathways[i+1]
					
					# Pathway 2 has a better ROI than Pathway 1 -- so if their schools conflict, let's keep pathway 2.
					if pathway_schools_conflict(pathway_1, pathway_2):
						
						if budget_modifier == 0:
							print "Found duplicate schools: deleting a pathway with", str(pathway_1.roi()) + "% ROI in favor of one with", str(pathway_2.roi()) + "%"
							pathway_to_delete = pathway_1
						
						elif budget_modifier > 0:
							p = [pathway_1, pathway_2]
							p.sort(key = lambda c: c.cost()) # Cheapest to most expensive.
							print "Found duplicate schools: deleting a $" + str(p[1].cost()), "pathway in favor of a $" + str(p[0].cost()), "one."
							pathway_to_delete = p[1]

						pathway_to_delete.delete_instance(recursive = True)
						made_pathways.remove(pathway_to_delete)

				except Exception:
					print "Hit the end of the list"
					pass

			# Finally, update the list of excluded schools:
			excluded_schools = get_excluded_schools(report)

			# And add this narrower list of pathways to our list of good pathways:
			good_pathways += made_pathways

		elif budget_modifier < budget_leeway: # At some point we have to give up... right?
			budget_modifier += 10000

		else:
			failed = True

	# Now clean up any extra pathways:
	if len(good_pathways) > how_many:
		good_pathways.sort(key = lambda p: p.roi(), reverse = True)

		index = -1
		while len(good_pathways) > how_many:
			p = good_pathways[index]
			print "Deleting a pathway with an ROI of", str(p.roi())
			p.delete_instance(recursive = True)
			good_pathways.remove(p)
			index -= 1

	if not failed:
		print "\nSuccessfully made", len(good_pathways), "pathways for", student.name + ".\n"
	else:
		print "\nFailed to make pathways for", student.name + ".\n"


@async
def make_pathways_async(student, report, how_many):
	make_pathways_for_student(student = student, report = report, how_many = how_many)