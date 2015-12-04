# Functions to help build pathways.

from data_model import *


def calculate_roi(cost, gains):
	cost = float(cost)
	gains = float(gains)
	
	roi = (gains-cost)/cost
	roi = float("{0:.2f}".format(roi))
	
	return roi
	

def roi_for_program(program, duration, income_level, home_state):
	school = program.school
	
	try: 
		gains = int(program.median_salary)*20 # Let's use a 20-year ROI for now.				
		if school.state == home_state:
			try:
				cost = int(school.net_price[income_level])*duration
			except Exception:
				cost = int(school.total_price["in-state students living on campus"])*duration
		else:
			cost = int(school.total_price["out-of-state students living on campus"])*duration
		
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
		
		for program in p:
			school = program.school
			if school.kind == step.school_kind:
				programs.append(program)









