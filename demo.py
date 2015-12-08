# A text-based demo of the HiUni Reports backend.

import os

from data_model import *
import data_helper
import solver


def clear():
	os.system('cls' if os.name == 'nt' else 'clear')


def print_student_info(student):
	print ""
	print student.name, "in", student.city + ",", student.state
	print "  Career:", student.career.name
	if student.income != "over 110,000":
		income_string = "$" + student.income
	else:
		income_string = student.income
	print "  Income:", income_string
	print "  Budget: $" + str(student.budget)
	print ""


def show_students():
	clear()
	print "\nSTUDENTS"
	print "--------"

	students = Student.select()

	for student in students:
		print_student_info(student)

	raw_input("\nPress enter return to the menu.")
	menu()


def show_careers():
	clear()
	print "\nCAREERS"
	print "-------\n"

	careers = Career.select()

	for career in careers:
		print "-", career.name

	raw_input("\nPress enter return to the menu.")
	menu()


def make_student():
	clear()
	print "\nADD STUDENT"
	print "-----------"
	
	# First the easy stuff:
	print "\n  First, the easy stuff:"
	
	first_name = raw_input("    First name? ")
	last_name = raw_input("    Last name? ")
	name = first_name + " " + last_name
	
	email = raw_input("    Email? ")

	# Next, choose a career from the list of available careers:
	print "\n  Next, choose a career:"
	
	careers = Career.select()
	
	i = 1
	for career in careers:
		print "    " + str(i) + ".", career.name
		i += 1

	try: 
		career_number = int(raw_input("    "))
		career = careers[career_number-1]
	except Exception:
		menu()

	# Now choose an income level:
	income_levels = ["0-30,000", "30,001-48,000", "48,001-75,000", "75,001-110,000", "over 110,000"]
	print "\n  What's your family's income level?"
	i = 1
	for level in income_levels:
		print "    " + str(i) + ".", level
		i += 1

	try:
		level_number = int(raw_input("    "))
		income = income_levels[level_number-1]
	except Exception:
		menu()

	# Set a budget:
	budget = int(raw_input("\n  What's your budget for higher education? "))

	# Set a location:
	print "\n  And finally, where are you located?"
	city = raw_input("    City? ")
	state = raw_input("    State? ")

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

	print "\nSuccessfully saved the student! Details:\n"
	print_student_info(student)

	raw_input("\nPress enter to return to the menu.")
	menu()


def import_templates_for_career_named(name):
	i = 1
	templates_made = 0
	
	while True:
		file_name = name + " Template " + str(i) # Templates should follow the naming convention "Career Template 1.csv"
		
		try:
			data_helper.import_template_from_file(file_name)
			templates_made += 1
		except Exception:
			break
		
		i += 1

	if templates_made > 0:
		return True
	else:
		return False


def make_career():
	clear()
	print "\nADD CAREER"
	print "-----------"

	career_name = raw_input("\nCareer name? ")

	print "\nSearching for templates for", career_name + "s..."
	
	templates_found = import_templates_for_career_named(career_name)

	if not templates_found:
		print "\nCouldn't find any templates for the career '" + career_name + "'."
	else:
		print "\nSuccessfully added the career '" + career_name + "'."
	
	raw_input("\nPress enter to return to the menu.")
	menu()


def make_pathways():
	clear()
	print "\nGENERATE PATHWAYS"
	print "-----------------"

	print "\nChoose a student:"
	students = Student.select()
	i = 1
	for student in students:
		print "  " + str(i) + ".", student.name
	
	try:
		student_number = int(raw_input("  "))
		student = students[student_number-1]
	except Exception:
		menu()

	pathways_needed = int(raw_input("\nAnd how many pathways would you like to make (per template)?"))

	print "\nOK! Generating pathways for", student.name + "."
	schools = School.select()
	programs = Program.select()
	print "Searching", str(len(schools)), "schools offering", str(len(programs)), "programs..."

	try:
		solver.make_pathways_for_student(student, how_many = pathways_needed)
	except Exception:
		print "\nFailed to make pathways.\n"

	raw_input("Press enter to return to the menu.")
	menu()


def show_pathways():
	clear()
	print "\nSHOW PATHWAYS"
	print "---------------"

	print "\nChoose a student:"
	students = Student.select()
	i = 1
	for student in students:
		print "  " + str(i) + ".", student.name
	
	try:
		student_number = int(raw_input("  "))
		student = students[student_number-1]
	except Exception:
		menu()

	clear()
	print "\nSHOW PATHWAYS"
	print "---------------"
	print_student_info(student)
	print ""

	pathways = Pathway.select().where(Pathway.student == student)

	i = 1
	for pathway in pathways:
		print "  PATHWAY #" + str(i)
		print "\n    Total Cost: $" + str(pathway.cost())
		print "    Total Duration:", str(pathway.duration()),  "years"
		print "    20-year Earnings: $" + str(pathway.median_salary()*20)
		print "    ROI:", str(pathway.roi()) + "%"

		pathway_steps = pathway.sorted_steps()

		for step in pathway_steps:
			print "\n      STEP", str(step.number) + ": '" + step.title() + "'"
			print "        Study", step.program.name, "at", step.program.school.name
			print "          Cost: $" + str(step.cost)
			print "          Duration:", str(step.duration()), "years"
			# print "          Description:"
			# print "            " + step.description()

		if len(pathways) > 1:
			raw_input("")
		else:
			print ""

		i += 1


	raw_input("\nPress enter to return to the menu.")
	menu()


def delete_students():
	clear()
	print "\nDELETE ALL STUDENTS"
	print "-------------------"

	choice = raw_input("\nAre you sure you want to delete all students? Y/N: ")
	
	if choice == "y" or choice == "Y":
		data_helper.delete_all_students()
		print "\nAll students deleted."

	raw_input("\nPress enter to return to the menu.")
	menu()


def delete_pathways():
	clear()
	print "\nDELETE ALL PATHWAYS"
	print "-------------------"

	choice = raw_input("\nAre you sure you want to delete all pathways? Y/N: ")
	
	if choice == "y" or choice == "Y":
		data_helper.delete_all_pathways()
		print "\nAll pathways deleted."

	raw_input("\nPress enter to return to the menu.")
	menu()


def delete_careers():
	clear()
	print "\nDELETE ALL CAREERS"
	print "-------------------"

	choice = raw_input("\nAre you sure you want to delete all careers? Y/N: ")
	
	if choice == "y" or choice == "Y":
		data_helper.delete_all_careers()
		print "\nAll careers deleted."

	raw_input("\nPress enter to return to the menu.")
	menu()


def delete():
	clear()
	print "\nDELETE"
	print "-------"

	print "\nWhat would you like to delete?"
	choices = ["Students", "Pathways", "Careers"]
	i = 1
	for c in choices:
		print "  " + str(i) + ".", c
		i += 1
	
	try: 
		choice_number = int(raw_input("\n  "))-1
		choice = choices[choice_number]
	except Exception:
		menu()

	if choice == "Students": delete_students()
	if choice == "Pathways": delete_pathways()
	if choice == "Careers": delete_careers()


def menu():
	clear()
	print "\nHIUNI REPORTS"
	print "-------------"

	number_schools = str(len(School.select()))
	number_careers = str(len(Career.select()))
	number_students = str(len(Student.select()))

	print "\nCurrently: ", number_schools,"schools,", number_careers, "careers, and", number_students, "students."

	print "\nWhat would you like to do?"

	choices = ["Add a career", "Show all careers", "Add a student", "Show all students", "Generate pathways", "Show pathways", "Delete", "Quit"]
	i = 1
	for c in choices:
		print "  " + str(i) + ".", c
		i += 1
	
	try: 
		choice_number = int(raw_input("\n  "))-1
		choice = choices[choice_number]
	except Exception:
		menu()

	if choice == "Add a career": make_career()
	if choice == "Show all careers": show_careers()

	if choice == "Add a student": make_student()
	if choice == "Show all students": show_students()
	
	if choice == "Generate pathways": make_pathways()
	if choice == "Show pathways": show_pathways()

	if choice == "Delete": delete()
	
	if choice == "Quit": 
		clear()
		quit()

	menu()


# Running the demo:
menu()


