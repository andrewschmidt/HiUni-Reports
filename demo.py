# A text-based demo of the HiUni Reports backend.

from data_model import *
import data_helper
import solver

def make_student():
	print "New Student:"
	
	# First the easy stuff:
	name = input("\n  Name?")
	email = input("  Email?")

	# Next, choose a career from the list of available careers:
	print "\n  Choose a career:"
	
	careers = Career.select()
	
	i = 1
	for career in careers:
		print "    " + str(i) + ".", career.name
		i += 1

	career_number = input("  ?")
	career = careers[career_number-1]

	# Now choose an income level:
	income_levels = ["0-30,000", "30,001-48,000", "48,001-75,000", "75,001-110,000", "over 110,000"]
	print "\n  Income level?"
	i = 1
	for level in income_levels:
		print "    " + str(i) + ".", level
		i += 1

	level_number = input("  ?")
	income = income_levels[level_number-1]

	# Set a budget:
	budget = int(input("\n  Budget?"))

	# Set a location:
	city = input("\n  City?")
	state = input ("  State?")

	# Now save the student:
	student = Student()

	student.name = name
	student.email = email
	
	student.career = career
	student.income = income
	student.budget = budget
	
	student.city = city
	student.state = state

	student.save()

