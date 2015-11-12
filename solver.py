# Functions to help build pathways.

from data_model import *


def calculate_roi(cost, gains):
	cost = float(cost)
	gains = float(gains)
	
	roi = (gains-cost)/cost
	roi = float("{0:.2f}".format(roi))
	
	return roi
	

def roi_for_program(program, duration, income_level):
	school = program.school
	
	try: 
		cost = int(school.net_price[income_level])*duration
		gains = int(program.median_salary)*20 # Let's use a 20-year ROI for now.				
		roi = calculate_roi(cost, gains)
		return roi
	
	except Exception:
 		print "Error getting ROI."
		return None
		
		
def programs_by_roi_for_cip(cip, duration, income_level):
	programs = []
	
	for program in Program.select().where(Program.cip == cip):
		if program.median_salary is not None:
			programs.append(program)
	
	programs.sort(key = lambda p: roi_for_program(p, duration = duration, income_level = income_level), reverse = True)
	
	return programs