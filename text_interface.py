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
	report = student.reports[0]
	if report.career is not None:
		print Style.DIM + "  Career:", report.career.name
	if student.income != "over 110,000":
		income_string = "$" + student.income
	else:
		income_string = student.income
	print Style.DIM + "  Income:", income_string
	print Style.DIM + "  Budget: ", "$" + str(student.budget)
	print Style.DIM + "  Database ID:", str(student.id)
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
		print "-", Style.BRIGHT + career.name, "with", Style.BRIGHT + str(career.recipes.count()), "recipes."

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
	
	student.income = income
	student.budget = budget
	
	student.city = city
	student.state = state

	student.save()

	# And save an empty report w/ the career of choice:
	report = Report()

	report.student = student
	report.career = career
	report.published = False

	report.save()

	print "\nSuccessfully saved the student! Details:\n"
	print_student_info(student)

	raw_input("\nPress enter to return to the menu.")
	menu()


def import_recipes_for_career_named(name):
	i = 1
	recipes_made = 0
	
	while True:
		file_name = name + " Recipe " + str(i) # Recipes should follow the naming convention "Career Recipe 1.csv"
		
		try:
			data_helper.import_recipe_from_file(file_name)
			recipes_made += 1
		except Exception:
			break
		
		i += 1

	if recipes_made > 0:
		return True
	else:
		return False


def make_career():
	clear()
	print Style.BRIGHT + Fore.GREEN + "\nADD CAREER"
	print "----------"

	career_name = raw_input("\nCareer name? ")

	print "\nSearching for recipes for '" + career_name + "'..."
	
	recipes_found = import_recipes_for_career_named(career_name)

	if not recipes_found:
		print "\nCouldn't find any recipes for the career '" + career_name + "'."
		print "Keep in mind, the Career Recipes folder needs to be in the same directory you're running text_interface.py from."
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

	pathways_needed_string = raw_input("\nHow many pathways would you like to make? ")
	try: 
		pathways_needed = int(pathways_needed_string)
	except Exception: 
		menu()

	# Get a report to make pathways for.
	# Right now this just uses the first report that returns.
	# In the future I should make it so you can select which report to use.
	report = Report.select().join(Student).where((Student.id == student.id)).get()

	print "\nOK! Generating pathways for", student.name + "."
	print "\nSearching", str(School.select().count()), "schools offering", str(Program.select().count()), "programs...\n"

	# try:
	solver.make_pathways_for_student(student, report = report, how_many = pathways_needed)
	# except Exception:
	# 	print "\nFailed to make pathways, error in solver.make_pathways_for_student()."

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
	
	report = student.reports[0]
	pathways = report.sorted_pathways()

	i = 1
	for pathway in pathways:
		print Style.BRIGHT + "\n  PATHWAY #" + str(i)
		print "\n    Total Cost:", "$" + Style.BRIGHT + str(pathway.cost())
		print "    Total Duration:", Style.BRIGHT + str(pathway.duration()) + " years"
		print "    Median Salary:", "$" + Style.BRIGHT + str(pathway.median_salary())
		print "    ROI:", Style.BRIGHT + str(pathway.roi()) + "%"

		pathway_steps = pathway.sorted_steps()

		for step in pathway_steps:
			print "\n      " + Style.BRIGHT + "Step " + str(step.number) + ": " + step.title()
			# print Style.NORMAL + "        Study " + step.program.name, Style.DIM + "at", Style.NORMAL + step.program.school.name
			print Style.DIM + "          Study:", Style.NORMAL + step.program.name
			print Style.DIM + "          School:", Style.NORMAL + step.program.school.name
			print Style.DIM + "          Acceptance rate:", Style.NORMAL + str(step.program.school.admission_rate) + "%"
			# print Style.DIM + "          Kind:", Style.NORMAL + step.program.school.kind
			# print Style.DIM + "          Located:", Style.NORMAL + step.program.school.city + ", " + step.program.school.state
			print Style.DIM + "          Cost:", Style.NORMAL + "$" + str(step.cost)
			print Style.DIM + "          Duration:", Style.NORMAL + str(step.duration()) + " years"
			description = step.description()
			print Style.DIM + "          Description: "
			print Style.NORMAL + textwrap.fill(description, width = 120, initial_indent = "                ", subsequent_indent = "             ")
			print ""

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
	print Style.BRIGHT + Fore.RED + "\nDELETE REPORTS"
	print "-------------------"

	print "\nDelete reports for which student?"
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
			to_delete = Report.select()
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
			for report in student.reports:
				to_delete.append(report)

		else:
			raw_input("\nPress enter to return to the menu.")
			menu()
	
	count = len(to_delete)	
	for item in to_delete:
		item.delete_instance(recursive = True)

	print "Deleted", count, "objects."

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


def delete_customers():
	clear()
	print Style.BRIGHT + Fore.RED + "\nDELETE CUSTOMERS"
	print "---------------"

	print "\nDelete which customer?"
	customers = Customer.select()
	i = 1
	for customer in customers:
		user = customer.users[0]
		print Style.BRIGHT + "  " + str(i) + ". " + Fore.RED + user.email
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
		confirm = raw_input(Style.BRIGHT + "\nAre you sure you want to delete all customers? Y/N: ")
		if confirm == "y" or confirm == "Y":
			to_delete = Customer.select()

		else:
			raw_input("\nPress enter to return to the menu.")
			menu()

	else:
		try:
			customer = customers[number-1]
		except Exception:
			print "\nGot the input:", str(number) + ", didn't know what to do with it."
			raw_input("\nPress enter to return to the menu.")
			menu()
		
		user = customer.users[0]
		confirm = raw_input(Style.BRIGHT + "\nAre you sure you want to delete " + user.email + "? Y/N: ")
		if confirm == "y" or confirm == "Y":
			to_delete = [customer]
		else:
			raw_input("\nPress enter to return to the menu.")
			menu()
	
	count = len(to_delete)	
	for item in to_delete:
		user = item.users[0]
		user.delete_instance()
		item.delete_instance(recursive = True)

	print "Deleted", count, "customers and their associated user accounts."

	raw_input("\nPress enter to return to the menu.")
	menu()


def delete_employees():
	clear()
	print Style.BRIGHT + Fore.RED + "\nDELETE EMPLOYEES"
	print "---------------"

	print "\nDelete which employee?"
	employees = Employee.select()
	i = 1
	for employee in employees:
		user = employee.users[0]
		print Style.BRIGHT + "  " + str(i) + ". " + Fore.RED + user.email
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
		confirm = raw_input(Style.BRIGHT + "\nAre you sure you want to delete all employees? Y/N: ")
		if confirm == "y" or confirm == "Y":
			to_delete = Employee.select()

		else:
			raw_input("\nPress enter to return to the menu.")
			menu()

	else:
		try:
			employee = employees[number-1]
		except Exception:
			print "\nGot the input:", str(number) + ", didn't know what to do with it."
			raw_input("\nPress enter to return to the menu.")
			menu()
		
		user = employee.users[0]
		confirm = raw_input(Style.BRIGHT + "\nAre you sure you want to delete " + user.email + "? Y/N: ")
		if confirm == "y" or confirm == "Y":
			to_delete = [employee]
		else:
			raw_input("\nPress enter to return to the menu.")
			menu()
	
	count = len(to_delete)	
	for item in to_delete:
		user = item.users[0]
		user.delete_instance()
		item.delete_instance(recursive = True)

	print "Deleted", count, "employees and their associated user accounts."

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


def delete_users():
	clear()
	print Style.BRIGHT + Fore.RED + "\nDELETE ALL USERS"
	print "------------------"

	choice = raw_input(Style.BRIGHT + Fore.RED + "\nAre you sure you want to delete all users? Y/N: ")
	
	if choice == "y" or choice == "Y":
		users = User.select()
		customers = Customer.select()
		employees = Employee.select()

		for user in users: user.delete_instance(recursive = True)
		for customer in customers: customer.delete_instance(recursive = True)
		for employee in employees: employee.delete_instance(recursive = True)
		
		print "\nAll users, customers, and employees deleted."

		print "Creating an admin..."
		employee = Employee()
		employee.save()
		user = User.create(
			email = "admin@gohiuni.com",
			password = "admin",
			employee = employee
		)
		user.save()

	raw_input("\nPress enter to return to the menu.")
	menu()


def delete():
	clear()
	print Style.BRIGHT + Fore.RED + "\nDELETE"
	print "------"

	print "\nWhat would you like to delete?"
	choices = ["Students", "Pathways", "Careers", "Customers", "Employees", "All users", "Exit"]
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
	if choice == "Customers": delete_customers()
	if choice == "Employees": delete_employees()
	if choice == "All users": delete_users()
	if choice == "Exit": menu()


def hidden_menu():
	clear()
	print Style.BRIGHT + "\nHIDDEN MENU"
	print "-----------"

	print "\nWhat would you like to do?"

	if solver.unsafe_search_allowed:
		unsafe_search_toggle = "Turn off unsafe searches"
	else:
		unsafe_search_toggle = "Turn on unsafe searches"

	choices = [unsafe_search_toggle, "Import schools", "Delete all schools", "Exit"]
	i = 1
	for c in choices:
		if "Import" in c: 
			text_style = Fore.GREEN
		elif "Delete" in c:
			text_style = Fore.RED
		elif "unsafe" in c:
			text_style = Fore.BLUE
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
	if "unsafe" in choice:
		if solver.unsafe_search_allowed:
				solver.unsafe_search_allowed = False
		else:
			solver.unsafe_search_allowed = True
	if choice == "Exit": menu()


def menu():
	clear()
	print Style.BRIGHT + "\nHIUNI REPORTS"
	print "-------------"

	number_schools = str(School.select().count())
	number_careers = str(Career.select().count())
	number_customers = str(Customer.select().count())
	number_students = str(Student.select().count())
	number_users = str(User.select().count())
	number_employees = str(Employee.select().count())
	number_reports = str(Report.select().count())

	print "\nCurrently: ", Style.BRIGHT + number_schools, "schools,", Style.BRIGHT + number_careers, "careers, and", Style.BRIGHT + number_customers, "customers with", Style.BRIGHT + number_students, "students."
	print Style.DIM + "\n  Total users:", number_users
	print Style.DIM + "  Employees:  ", number_employees
	print Style.DIM + "  Reports:    ", number_reports

	print "\n\nWhat would you like to do?"

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