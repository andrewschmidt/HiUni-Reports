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
 		print "Error getting ROI for", program.name, "at", school.name + "."
		return None
		
		
def programs_by_roi_for_cip(cip, duration, income_level, home_state):
	programs = []
	
	for program in Program.select().where(Program.cip == cip):
		if program.reportable and program.median_salary is not None: # We only want to return programs w/ salary data, and enough of it.
			programs.append(program)
	
	programs.sort(key = lambda p: roi_for_program(p, duration = duration, income_level = income_level, home_state = home_state), reverse = True)
	
	return programs


def programs_by_roi_for_step(step, student):
	programs = []
	
	for cip in step.cips:
		p = programs_by_roi_for_cip(cip = cip, duration = step.duration, income_level = student.income, home_state = student.state)
		
		if len(p) > 0:
			for program in p:
				school = program.school
				if school.kind == step.school_kind:
					programs.append(program)
				else:
					print "School kind '" + school.kind + "' does not match kind called for:", step.school_kind + "."

	# The function we used to fetch programs sorts them by ROI.
	# But if we called it multiple times, our array isn't properly sorted.
	# Let's fix that:
	if len(step.cips) > 1:
		programs.sort(key = lambda p: roi_for_program(p, duration = duration, income_level = income_level, home_state = home_state), reverse = True)

	return programs


def programs_by_city_for_step(step, student):
	# This is hacky right now. It returns all schools in the same city, instead of finding them by distance.
	# And it should be making its own database calls, taking into account location.
	programs = []

	for p in programs_by_roi_for_step(step, student):
		school = p.school
		if school.city == student.city and school.state == student.state:
			programs.append(p)

	return programs


def programs_for_step(step, student):
	if step.sort_by == "ROI":
		programs = programs_by_roi_for_step(step, student)
	else:
		programs = programs_by_city_for_step(step, student)

	return programs


def make_pathways_for_student(student, how_many):
	pathways_needed = how_many		
	career = student.career
	templates = career.templates

	print "\nFound", len(templates), "templates."

	for template in templates:
		
		pathways_created = 0
		i = 0
		abort = False

		while pathways_created < pathways_needed:
			# Create the pathway first, since the steps have to reference it:
			pathway = data_helper.save_pathway(student)

			# Now create its steps:
			for step in template.steps:
				programs = programs_for_step(step, student)
				
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

	print "Made", str(pathways_created), "pathways for", student.name + "!\n"