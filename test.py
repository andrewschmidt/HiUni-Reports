# Let's test it!


from data_model import *
import data_helper
import solver


def print_number_of_schools():
	print "\nThere are", str(School.select().count()), "schools in the database, offering", str(Program.select().count()), "programs."


def print_schools():
	print "\nThere are", str(School.select().count()), "schools in the database:"
	for school in School.select():
		print "\n    -", school.name + ", with", school.programs.count(), "programs."
		print "        Location:", school.city + ", " + school.state
		# print "        Location:", school.location["latitude"] + ",", school.location["longitude"]
		print "        Admission rate:", str(school.admission_rate) + "%"
		print "        IPEDS ID:", str(school.ipeds_id)

		try:
			check_total_price = school.total_price["in-state students living on campus"]
			print "        Total prices:"
			print "            In-state, on campus:    ", "$" + str(school.total_price["in-state students living on campus"])
			print "            In-state, with family:  ", "$" + str(school.total_price["in-state students living off campus (with family)"])
			print "            Out-of-state, on campus:", "$" + str(school.total_price["out-of-state students living on campus"])
		except Exception:
			pass
	
		try:
			check_net_price = school.net_price["average"]
			print "        Net prices:"
			print "            Average:           ", "$" + str(school.net_price["average"])
			print "            Income below $30K: ", "$" + str(school.net_price["0-30,000"])
			print "            Income $30K - $48K:", "$" + str(school.net_price["30,001-48,000"])
			print "            Income $48K - 75K: ", "$" + str(school.net_price["48,001-75,000"])
			print "            Income $75K - $110:", "$" + str(school.net_price["75,001-110,000"])
			print "            Income over $110K: ", "$" + str(school.net_price["over 110,000"])
		except Exception:
			pass


def print_programs():
	print "\nPrograms in the database:"
	for program in Program.select():
		print "    -", program.name, "at", program.school.name
		print "        CIP: " + str(program.cip)
		print "        Median Salary: $" + str(program.median_salary)
		print "        Reportable? " + str(program.reportable)
		roi = solver.roi_for_program(program, duration = 4, income_level = "30,001-48,000")
		if roi:
			print "        Typical ROI: " + str(roi) + "%"
		print ""
		
		
def test_roi():
	program_name = "Economics" # CIP: 45.06
	school_name = "University of Southern California"
	program = Program.select().join(School).where((Program.name == program_name) & (School.name == school_name)).get()
	
	roi = solver.roi_for_program(program, duration = 4, income_level = "30,001-48,000")
	
	print "\nThe 20-year ROI for studying", program.name, "at USC is", str(roi)+"%"


def get_best_roi_schools_for_cip(cip, how_many, home_state):
	print ""
	state = home_state

	programs = solver.programs_by_roi_for_cip(cip, duration = 4, income_level = "30,001-48,000", home_state = state, only_reportable = True)
	
	if len(programs) == 0:
		print "\nCouldn't find 'reportable' programs, trying without that restriction..."
		programs = solver.programs_by_roi_for_cip(cip, duration = 4, income_level = "30,001-48,000", home_state = state, only_reportable = False)
	
	if len(programs) > 0:

		print "\nTop", str(how_many), "schools for CIP:", cip + ", sorted by ROI:\n"
		
		schools_found = 0
		i = 0

		while schools_found < how_many:
			program = programs[i]
			i += 1

			# if program.reportable:
			print "   #" + str(schools_found+1) + ":", program.name, "at", program.school.name
			print "        Median Salary: $" + str(program.median_salary)
			
			roi = solver.roi_for_program(program, duration = 4, income_level = "30,001-48,000", home_state = state)
			if roi:
				print "        ROI: " + str(roi) + "%"
		
			print ""

			schools_found += 1
			# else:
				# print "Found unreportable program, shouldn't have."

	else:
		print "Couldn't find any reportable programs for that CIP."


def import_sample_template():
	# sheet = data_helper.get_csv_sheet("Sample Template.csv")
	# data_helper.import_template_from_sheet(sheet)
	data_helper.import_template_from_file("Sample Template.csv")


def print_careers():
	print "\nThere are", str(Career.select().count()), "careers in the database:"

	careers = Career.select()
	for career in careers:
		print "\n    - " + career.name + ", with", career.templates.count(), "templates."


def print_students():
	number_of_students = Student.select().count()
	print "\nThere are", str(number_of_students), "students in the database:"

	if number_of_students > 0:
		students = Student.select()
		for student in students:
			print "\n    - " + student.name + "."


def print_templates():
	print "\nThere are", str(Template.select().count()), "templates in the database."

	
def print_steps():
	print "\nThere are", str(Step.select().count()), "steps in the database."
	
	steps = Step.select()
	for step in steps:
		print step.title
		print str(step.number)
		print step.template.career.name
		print str(step.duration) + "years"


def print_fake_pathways_for_sample_student():
	student = Student.get(Student.name == "Lindsay Santiago")
	solver.print_pathways_for_student(student)


def make_pathways_for_sample_student():
	student = Student.get(Student.name == "Lindsay Santiago")
	solver.make_pathways_for_student(student, how_many = 3)


def print_pathways_for_sample_student():
	student = Student.get(Student.name == "Lindsay Santiago")
	pathways = Pathway.select().where(Pathway.student == student)

	print "\nPathways for", student.name + ":"

	i = 1
	for pathway in pathways:
		print "\n\n  PATHWAY #" + str(i)
		print "\n    Total Cost: $" + str(pathway.cost())
		print "    Total Duration:", str(pathway.duration()),  "years"
		print "    20-year Earnings: $" + str(pathway.median_salary()*20)
		print "    ROI:", str(pathway.roi()) + "%"

		pathway_steps = pathway.sorted_steps()

		for step in pathway_steps:
			print "\n      Step", str(step.number) + ": '" + step.title() + "'"
			print "        Study", step.program.name, "at", step.program.school.name
			print "          Cost: $" + str(step.cost)
			print "          Duration:", str(step.duration()), "years"
			# print "          Description:"
			# print "            " + step.description()

		i += 1


def create_sample_student():
	name = "Lindsay Santiago"
	email = "me@lindsaysantiago.com"
	career = Career.get(Career.name == "Barista")
	income = "30,001-48,000"
	budget = 120000
	city = "Los Angeles"
	state = "California"

	create_student(name, email, career, income, budget, city, state)


def create_student(name, email, career, income, budget, city, state):
	student = Student()
	
	student.name = name
	student.email = email
	
	student.career = career
	student.income = income
	student.budget = budget
	
	student.city = city
	student.state = state

	student.save()


def destroy_and_rebuild_tables():
	data_helper.drop_tables()
	data_helper.create_tables()


def repopulate_everything():
	data_helper.import_school_data()
	import_sample_template()


def print_community_colleges(city, state):
	community_colleges = School.select().where((School.kind == "Degree-granting, associate's and certificates") & (School.city == city) & (School.state == state))
	
	print "\nThere are", len(community_colleges), "community colleges in", city + ",", state + ":"

	for college in community_colleges:
		print "  -", college.name
		print "      Total Prices:", str(college.total_price)
		print "      Net Price:", str(college.net_price)



# Commands for data_helper:

# data_helper.drop_tables()
# data_helper.create_tables()
# data_helper.delete_all_schools()
# data_helper.delete_all_careers()
# data_helper.delete_all_pathways()
# data_helper.delete_all_students()
# data_helper.import_school_data()
# import_sample_template()


# Local commands:

# print_number_of_schools()
# print_schools()
# print_programs()
# import_sample_template()
# create_sample_student()
# print_students()
# print_careers()
# print_templates()
# print_steps()
# print_community_colleges(city = "Los Angeles", state = "California")

get_best_roi_schools_for_cip("50.04", how_many = 5, home_state = "New York") # Economics = 45.06, Design = 50.04, Biology = 26.01, Drama = 50.05, Journalism = 09.04, Architecture = 04.02
# test_roi()
# swap_cip_for_test_purposes()
# make_pathways_for_sample_student()
# print_pathways_for_sample_student()

# destroy_and_rebuild_tables()
# repopulate_everything()

print ""