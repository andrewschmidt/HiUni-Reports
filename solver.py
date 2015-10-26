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
	
	print "\nGetting ROI for", program.name, "at the", school.name +"..."
	
	cost = int(school.net_price[income_level])*duration
	gains = int(program.median_salary)*20 # Let's use a 20-year ROI for now.
	
	print "Total price:", "$" + str(cost)
	print "20-year income:", "$" + str(gains)
	
	roi = calculate_roi(cost, gains)
	print "ROI:", str(roi) + "%"
	return roi
	

