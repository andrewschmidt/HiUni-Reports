# A text-based demo of the HiUni Reports backend.

from data_model import *
import data_helper
import solver

import os
import textwrap
from colorama import init, Fore, Back, Style
init(autoreset = True)


def clear():
	os.system('cls' if os.name == 'nt' else 'clear')


def print_student_info(student):
	print ""
	print Style.BRIGHT + student.name, "in", student.city + ",", student.state
	if student.career is not None:
		print Style.DIM + "  Career:", student.career.name
	if student.income != "over 110,000":
		income_string = "$" + student.income
	else:
		income_string = student.income
	print Style.DIM + "  Income:", income_string
	print Style.DIM + "  Budget: ", "$" + str(student.budget)
	print ""


def show_students():
	clear()
	print Style.BRIGHT + Fore.CYAN + "\nSTUDENTS"
	print "--------"

	students = Student.select()

	for student in students:
		print_student_info(student)

	raw_input("\nPress enter return to the menu.")
	menu()


def show_careers():
	clear()
	print Style.BRIGHT + Fore.CYAN + "\nCAREERS"
	print "-------\n"

	careers = Career.select()

	for career in careers:
		print "-", Style.BRIGHT + career.name, "with", Style.BRIGHT + str(career.templates.count()), "templates."

	raw_input("\nPress enter return to the menu.")
	menu()


def make_student():
	clear()
	print Style.BRIGHT + Fore.GREEN + "\nADD STUDENT"
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
	print Style.BRIGHT + Fore.GREEN + "\nADD CAREER"
	print "----------"

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
	print Style.BRIGHT + Fore.GREEN + "\nGENERATE PATHWAYS"
	print "-----------------"

	print "\nChoose a student:"
	students = Student.select()
	i = 1
	for student in students:
		print Style.BRIGHT + "  " + str(i) + ". " + student.name
		i += 1
	
	try:
		student_number = int(raw_input("  "))
		student = students[student_number-1]
	except Exception:
		menu()

	pathways_needed_string = raw_input("\nAnd how many pathways would you like to make (per template)? ")
	try: 
		pathways_needed = int(pathways_needed_string)
	except Exception: 
		menu()

	print "\nOK! Generating pathways for", student.name + "."
	print "\nSearching", str(School.select().count()), "schools offering", str(Program.select().count()), "programs...\n"

	try:
		solver.make_pathways_for_student(student, how_many = pathways_needed)
	except Exception:
		print "\nFailed to make pathways."

	choice = raw_input("Do you want to see the pathways now? Y/N: ")
	if choice == "y" or choice == "Y":
		show_pathways_for_student(student)

	raw_input("\nPress enter to return to the menu.")
	menu()


def show_pathways():
	clear()
	print Style.BRIGHT + Fore.CYAN + "\nSHOW PATHWAYS"
	print "-------------"

	print "\nChoose a student:"
	students = Student.select()
	i = 1
	for student in students:
		print Style.BRIGHT + "  " + str(i) + ". " + student.name
		i += 1
	
	try:
		student_number = int(raw_input("  "))
		student = students[student_number-1]
	except Exception:
		menu()

	show_pathways_for_student(student)


def show_pathways_for_student(student):
	clear()
	print Style.BRIGHT + Fore.CYAN + "\nSHOW PATHWAYS"
	print "-------------"
	print_student_info(student)
	print ""

	pathways = Pathway.select().where(Pathway.student == student)

	i = 1
	for pathway in pathways:
		print Style.BRIGHT + "  PATHWAY #" + str(i)
		print "\n    Total Cost:", "$" + Style.BRIGHT + str(pathway.cost())
		print "    Total Duration:", Style.BRIGHT + str(pathway.duration()) + " years"
		print "    20-year Earnings:", "$" + Style.BRIGHT + str(pathway.median_salary()*20)
		print "    ROI:", Style.BRIGHT + str(pathway.roi()) + "%"

		pathway_steps = pathway.sorted_steps()

		for step in pathway_steps:
			print "\n      " + Style.BRIGHT + "STEP " + str(step.number) + ": '" + step.title() + "'", ""
			# print Style.NORMAL + "        Study " + step.program.name + " at " + step.program.school.name
			print Style.DIM + "          Major:", Style.NORMAL + step.program.name
			print Style.DIM + "          School:", Style.NORMAL + step.program.school.name
			print Style.DIM + "          Cost:", Style.NORMAL + "$" + str(step.cost)
			print Style.DIM + "          Duration:", Style.NORMAL + str(step.duration()) + " years"
			description = step.description()
			print Style.DIM + "          Description: " + Style.NORMAL + textwrap.fill(description, width = 80, initial_indent = "", subsequent_indent = "                       ")

		if len(pathways) > 1:
			raw_input("")
		else:
			print ""

		i += 1

	raw_input("\nPress enter to return to the menu.")
	menu()


def import_schools():
	clear()
	print Style.BRIGHT + Fore.GREEN + "\nIMPORT SCHOOLS"
	print "--------------"

	choice = raw_input("\nThis takes a while. Are you ready to wait? Y/N: ")
	
	if choice == "y" or choice == "Y":
		raw_input("\nPress enter to begin.")
		data_helper.import_school_data()

	raw_input("\nPress enter to return to the menu.")
	menu()


def delete_students():
	clear()
	print Style.BRIGHT + Fore.RED + "\nDELETE STUDENTS"
	print "---------------"

	print "\nDelete which student?"
	students = Student.select()
	i = 1
	for student in students:
		print Style.BRIGHT + "  " + str(i) + ". " + Fore.RED + student.name
		i += 1
	print Style.BRIGHT + "  " + str(i) + ". " + Fore.RED + "Delete all"
	print Style.BRIGHT + "  " + str(i+1) + ". Exit"
	
	choice = raw_input("  ")
	try:
		number = int(choice)
	except Exception:
		menu()

	if number == i+1:
		menu()
	
	elif number == i:
		confirm = raw_input(Style.BRIGHT + "\nAre you sure you want to delete all students? Y/N: ")
		if confirm == "y" or confirm == "Y":
			to_delete = Student.select()
		else:
			raw_input("\nPress enter to return to the menu.")
			menu()

	else:
		try:
			student = students[number-1]
		except Exception:
			print "\nGot the input:", str(number) + ", didn't know what to do with it."
			raw_input("\nPress enter to return to the menu.")
			menu()
		
		confirm = raw_input(Style.BRIGHT + "\nAre you sure you want to delete " + student.name + "? Y/N: ")
		if confirm == "y" or confirm == "Y":
			to_delete = [student]
		else:
			raw_input("\nPress enter to return to the menu.")
			menu()
	
	count = len(to_delete)	
	for item in to_delete:
		item.delete_instance(recursive = True)

	print "Deleted", count, "students."

	raw_input("\nPress enter to return to the menu.")
	menu()


def delete_pathways():
	clear()
	print Style.BRIGHT + Fore.RED + "\nDELETE ALL PATHWAYS"
	print "-------------------"

	print "\nDelete pathways for which student?"
	students = Student.select()
	i = 1
	for student in students:
		print Style.BRIGHT + "  " + str(i) + ". " + Fore.RED + student.name
		i += 1
	print Style.BRIGHT + "  " + str(i) + ". " + Fore.RED + "Delete all"
	print Style.BRIGHT + "  " + str(i+1) + ". Exit"
	
	choice = raw_input("  ")
	try:
		number = int(choice)
	except Exception:
		menu()

	if number == i+1:
		menu()
	
	elif number == i:
		confirm = raw_input(Style.BRIGHT + "\nAre you sure you want to delete all pathways? Y/N: ")
		if confirm == "y" or confirm == "Y":
			to_delete = Pathway.select()
		else:
			raw_input("\nPress enter to return to the menu.")
			menu()

	else:
		try:
			student = students[number-1]
		except Exception:
			print "\nGot the input:", str(number) + ", didn't know what to do with it."
			raw_input("\nPress enter to return to the menu.")
			menu()
		
		confirm = raw_input(Style.BRIGHT + "\nAre you sure you want to delete " + student.name + "'s pathways? Y/N: ")
		if confirm == "y" or confirm == "Y":
			to_delete = []
			for pathway in student.pathways:
				to_delete.append(pathway)
		else:
			raw_input("\nPress enter to return to the menu.")
			menu()
	
	count = len(to_delete)	
	for item in to_delete:
		item.delete_instance(recursive = True)

	print "Deleted", count, "pathways."

	raw_input("\nPress enter to return to the menu.")
	menu()


def delete_careers():
	clear()
	print Style.BRIGHT + Fore.RED + "\nDELETE CAREERS"
	print "------------------"

	print "\nDelete which career?"
	careers = Career.select()
	i = 1
	for career in careers:
		print Style.BRIGHT + "  " + str(i) + ". " + Fore.RED + career.name
		i += 1
	print Style.BRIGHT + "  " + str(i) + ". " + Fore.RED + "Delete all"
	print Style.BRIGHT + "  " + str(i+1) + ". Exit"
	
	choice = raw_input("  ")
	try:
		number = int(choice)
	except Exception:
		menu()

	if number == i+1:
		menu()
	
	elif number == i:
		confirm = raw_input(Style.BRIGHT + "\nAre you sure you want to delete all careers? Y/N: ")
		if confirm == "y" or confirm == "Y":
			to_delete = Career.select()
		else:
			raw_input("\nPress enter to return to the menu.")
			menu()

	else:
		try:
			career = careers[number-1]
		except Exception:
			print "\nGot the input:", str(number) + ", didn't know what to do with it."
			raw_input("\nPress enter to return to the menu.")
			menu()
		
		confirm = raw_input(Style.BRIGHT + "\nAre you sure you want to delete " + career.name + "? Y/N: ")
		if confirm == "y" or confirm == "Y":
			to_delete = [career]
		else:
			raw_input("\nPress enter to return to the menu.")
			menu()
	
	count = len(to_delete)	
	for item in to_delete:
		item.delete_instance(recursive = True, delete_nullable = False)

	print "Deleted", count, "careers."

	raw_input("\nPress enter to return to the menu.")
	menu()


def delete_schools():
	clear()
	print Style.BRIGHT + Fore.RED + "\nDELETE ALL SCHOOLS"
	print "------------------"

	choice = raw_input(Style.BRIGHT + Fore.RED + "\nAre you sure you want to delete all schools? Y/N: ")
	
	if choice == "y" or choice == "Y":
		data_helper.delete_all_schools()
		print "\nAll schools deleted."

	raw_input("\nPress enter to return to the menu.")
	menu()


def delete():
	clear()
	print Style.BRIGHT + Fore.RED + "\nDELETE"
	print "------"

	print "\nWhat would you like to delete?"
	choices = ["Students", "Pathways", "Careers", "Exit"]
	i = 1
	for c in choices:
		if "Exit" in c: 
			text_style = Style.BRIGHT
		else:
			text_style = Fore.RED

		print Style.BRIGHT + "  " + str(i) + ". " + text_style + c
		i += 1
	
	try: 
		choice_number = int(raw_input("\n  "))-1
		choice = choices[choice_number]
	except Exception:
		menu()

	if choice == "Students": delete_students()
	if choice == "Pathways": delete_pathways()
	if choice == "Careers": delete_careers()
	if choice == "Exit": menu()


def hidden_menu():
	clear()
	print Style.BRIGHT + "\nHIDDEN MENU"
	print "-----------"

	print "\nWhat would you like to do?"

	choices = ["Import schools", "Delete all schools", "Exit"]
	i = 1
	for c in choices:
		if "Import" in c: 
			text_style = Fore.GREEN
		elif "Delete" in c:
			text_style = Fore.RED
		else:
			text_style = Style.BRIGHT
		
		print Style.BRIGHT + "  " + str(i) + ". " + text_style + c
		i += 1
	
	try: 
		choice_number = int(raw_input("\n  "))-1
		choice = choices[choice_number]
	except Exception:
		menu()

	if choice == "Import schools": import_schools()
	if choice == "Delete all schools": delete_schools()
	if choice == "Exit": menu()


def menu():
	clear()
	print Style.BRIGHT + "\nHIUNI REPORTS"
	print "-------------"

	number_schools = str(School.select().count())
	number_careers = str(Career.select().count())
	number_students = str(Student.select().count())

	print "\nCurrently: ", Style.BRIGHT + number_schools, "schools,", Style.BRIGHT + number_careers, "careers, and", Style.BRIGHT + number_students, "students."

	print "\nWhat would you like to do?"

	choices = ["Add a career", "Add a student", "Generate pathways", "Show all careers", "Show all students", "Show pathways", "Delete", "Quit"]
	
	i = 1
	for c in choices:
		if "Add" in c or "Generate" in c: 
			text_style = Fore.GREEN
		elif "Show" in c:
			text_style = Fore.CYAN
		elif "Delete" in c:
			text_style = Fore.RED
		else:
			text_style = Style.BRIGHT

		print Style.BRIGHT + "  " + str(i) + ". " + text_style + c
		i += 1
	
	selection = raw_input("\n  ")

	if selection == "hidden": hidden_menu() # This menu's hidden because it's dangerous.

	try: 
		choice_number = int(selection)-1
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


