# Functions to help build pathways.

from data_model import *


def calculate_roi(cost, gains):
	cost = float(cost)
	gains = float(gains)
	
	roi = (gains-cost)/cost
	roi = float("{0:.2f}".format(roi))
	
	return roi


def cost_for_school(school, duration, income_level, home_state):
	if school.state == home_state:
		try:
			cost = int(school.net_price[income_level])*duration
		
		except Exception:
			cost = int(school.total_price["in-state students living on campus"])*duration
	
	else:
		cost = int(school.total_price["out-of-state students living on campus"])*duration

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


def print_pathways_for_student(student): # I need to create the Pathway class for this to really work. For now, just testing...
	# First, get the templates for the student's chosen career:
	try:
		career = student.career
		templates = career.templates

	except Exception:
		print "Unable to find the career or its templates."
		return None

	print "\nPathways for", student.name + ":"
	
	i = 1
	for template in templates:
		total_cost = 0

		print "\n  Pathway #" + str(i) + ":"
		
		ii = 1
		for step in template.steps:
			programs = programs_for_step(step, student)
			program = programs[0]

			cost = cost_for_school(program.school, duration = step.duration, income_level = student.income, home_state = student.state)

			print "\n      Step", str(ii) + ":"
			print "        Study", program.name, "at", program.school.name
			print "            Cost: $" + str(cost)
			print "            Duration:", str(step.duration), "years"

			total_cost += cost

			ii += 1

		final_salary = program.median_salary # Get the salary of the program chosen for the final step.
		gains = final_salary*20
		
		roi = calculate_roi(cost = total_cost, gains = gains)

		print "\n      Total Cost: $" + str(total_cost)
		print "  Total Duration:", str(template.duration()),  "years"
		print "20-year Earnings: $" + str(gains)
		print "             ROI:", str(roi) + "%"

		i += 1





