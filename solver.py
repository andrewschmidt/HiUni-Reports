# Functions to help build pathways.

from data_model import *
import data_helper


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
		if school.kind == "Degree-granting, associate's and certificates":
			situation = "in-state students living off campus (with family)"
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
		cost = int(school.total_price["out-of-state students living on campus"])

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


def programs_by_distance_for_cip(cip, school_kind, student, only_reportable):
	# This is hacky right now. It returns all schools in the same city, instead of finding them by distance.
	if only_reportable:
		query = (
			(Program.cip == cip) & 
			(Program.reportable == True) & 
			(School.city == student.city) & # Replace city & state with an actual distance algorithm.
			(School.state == student.state) & 
			(School.kind == school_kind))
	else:
		query = (
			(Program.cip == cip) & 
			(School.city == student.city) & # Replace city & state with an actual distance algorithm.
			(School.state == student.state) & 
			(School.kind == school_kind))
	
	programs = []

	for p in Program.select().join(School).where(query):
		programs.append(p)

	return programs


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

	if not safe_search:
		print "Had to use programs with low data."

	return programs


def pathway_complete(pathway, template):
	# Check if we made enough pathway steps:
	if len(pathway.pathway_steps) != len(template.steps):
		# print "Oh no! The pathway didn't have enough steps :("
		# print "Deleting it..."
		# pathway.delete_instance(recursive = True)
		return False
	else:
		return True


def within_budget(pathway, student):
	if pathway.cost() <= student.budget:
		return True
	else:
		return False


def excluded_programs(student):
	programs = []

	for pathway in student.pathways:
		for step in pathway.pathway_steps:
			school = step.program.school
			if school.kind != "Degree-granting, associate's and certificates": # It's OK to reuse community colleges.
				programs.append(step.program)

	return programs


def make_pathway_from_template(template, student):
	pathway = data_helper.save_pathway(student) # Pathway steps reference their pathway, so we need it in the database right away.

	# Make as many pathway steps as we can:
	for step in template.steps:
		# Get all applicable programs:
		programs = programs_for_step(step, student)
		print "Found", len(programs), "programs for step #" + str(step.number)

		# Then try to find one that fits juuust right:
		program_found = False
		i = 0
		while not program_found and i < len(programs):
			
			program = programs[i]

			if not program in excluded_programs(student):	
				try:
					cost = cost_for_school(program.school, duration = step.duration, income_level = student.income, home_state = student.state)
					
					# if pathway.cost() + cost <= student.budget: # I'm not entirely sure if I need this. Worth checking.
					program_found = True
					print program.name, "at", program.school.name, "works for step", step.number
					
				except Exception:
					print program.name, "at", program.school.name, "didn't work out :("

			i += 1

		# And save whatever we've got!
		if program_found:
			data_helper.save_pathway_step(pathway = pathway, program = program, step = step, number = step.number, cost = cost)

	return pathway


def make_pathways(student):
	career = student.career
	templates = career.templates
	good_pathways = []
		
	for template in templates:
		print "\nMaking a pathway."
		print "  Career:", career.name
		print "  Template:", template.number, "\n"
		
		pathway = make_pathway_from_template(template, student)
		
		print "\nChecking the pathway..."

		if pathway_complete(pathway, template) and within_budget(pathway, student):
			good_pathways.append(pathway)
			print "Made a pathway."
		else:
			print "Pathway is too expensive or incomplete."

	return good_pathways


def make_pathways_for_student(student, how_many):	
	good_pathways = []

	# First make tons of pathways:
	while len(good_pathways) < how_many:
		good_pathways += make_pathways(student)

	# Now clean up the leftovers --
	# Starting with pathways that were too expensive or incomplete:
	for p in student.pathways:
		if not within_budget(p, student):
			p.delete_instance(recursive = True)
		
		s = p.pathway_steps
		for pathway_step in s:
			template = pathway_step.step.template

		if not pathway_complete(p, template):
			p.delete_instance(recursive = True)

	# And any extra ones:
	if len(good_pathways) > how_many:

		good_pathways.sort(key = lambda p: p.roi(), reverse = True)

		# pathways = []
		# for pathway in student.sorted_pathways():
		# 	pathways.append(pathway)

		index = -1
		while len(good_pathways) > how_many:
			p = good_pathways[index]
			print "Deleting a pathway with an ROI of", str(p.roi())
			p.delete_instance(recursive = True)
			good_pathways.remove(p)
			index -= 1

