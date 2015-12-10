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
		try:
			cost = int(school.net_price[income_level])
		
		except Exception:
			cost = int(school.total_price["in-state students living on campus"])
	
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
		print "School kind '" + school.kind + "' DOES mach the kind called for:", step.school_kind + "."
		return True
	else:
		# print "School kind '" + school.kind + "' does not match kind called for:", step.school_kind + "."
		return False


def programs_by_city_for_step(step, student):
	# This is hacky right now. It returns all schools in the same city, instead of finding them by distance.
	# And it should be making its own database calls, taking into account location.
	programs = []
	
	query = (
		(School.city == student.city) & 
		(School.state == student.state) & 
		(School.kind == step.school_kind))

	for p in Program.select().join(School).where(query): # THIS IS THE PROBLEM. No community college has a single program. I need to make null programs (or general ed) for them!
		programs.append(p)

	# programs = []

	# for p in nearby_programs:
	# 	# print "School nearby! Checking kind..."
	# 	if check_school_kind(p, step):
	# 		# print "And it's the correct kind!"
	# 		programs.append(p)
	# 	# else:
	# 	# 	"It's the wrong kind:", p.school.kind

	# print "Found", str(len(programs)), "parsing by school type."
	# for p in programs:
	# 	school = p.school
	# 	if school.city == student.city and school.state == student.state and check_school_kind(p, step) is True:
	# 		print "\nFound some matching programs by city..."
	# 		if check_school_kind(program, step) is True:
	# 			print "And some with the correct school kind..."
	# 			programs.append(p)

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


def programs_for_step(step, student):
	if step.sort_by == "ROI":
		programs, safe_search = programs_by_roi_for_step(step, student)

		if not safe_search:
			print "Couldn't find any reportable programs, had to remove that restriction..."

	elif step.sort_by == "Location":
		programs = programs_by_city_for_step(step, student)
		
		if len(programs) == 0:
			print "Couldn't find any nearby programs."
		else:
			print "Found", str(len(programs)), "programs nearby."


	return programs


def make_pathways_for_student(student, how_many):
	career = student.career
	templates = career.templates

	for template in templates:
		pathways_needed = how_many		
		pathways_created = 0
		abort = False

		print "\nWorking on template #" + str(template.number)
		print "Pathways needed: ", pathways_needed
		while pathways_created < pathways_needed:
			# Create the pathway first, since the steps have to reference it:
			print "\nTrying to make a pathway...\n"
			pathway = data_helper.save_pathway(student)

			# Now create its steps:
			i = 0
			for step in template.steps:
				programs = programs_for_step(step, student)

				print "Found", str(len(programs)), "possible programs for step #" + str(step.number) + "."
				
				if len(programs) < pathways_needed:
					pathways_needed = len(programs)
					print "Only found enough programs to make", str(pathways_needed), "pathway(s)."

				try:
					program = programs[i]
				except Exception:
					print "Ran out of programs to make pathways with!"
					pathway.delete_instance(recursive = True) # No sense having an incomplete pathway.
					abort = True
					break

				number = step.number
				cost = cost_for_school(program.school, duration = step.duration, income_level = student.income, home_state = student.state)

				data_helper.save_pathway_step(pathway = pathway, program = program, step = step, number = number, cost = cost)

			if abort: break
			
			if pathway.cost() > student.budget:
				print "Pathway was too expensive! Trying again..."
				pathway.delete_instance(recursive = True) # No sense having a pathway that's too expensive.
			else:
				pathways_created += 1
			
			i += 1

		print "\nMade " + str(pathways_created) + " pathways from template #" + str(template.number) + ".\n"