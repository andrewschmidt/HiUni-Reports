# Let's test it!


from data_model import *
import data_helper
import solver


def print_schools():
	print "\nSchools in the database:"
	for school in School.select():
		print "\n    -", school.name + ", with", school.programs.count(), "programs."

		print "        Location:", school.city + ", " + school.state
		# print "        Location:", school.location["latitude"] + ",", school.location["longitude"]

		print "        Admission rate:", str(school.admission_rate) + "%"

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
		print "        Median Salary: $" + str(program.median_salary)
		
		
def test_roi():
	program_name = "Economics"
	school_name = "University of Southern California"
	program = Program.select().join(School).where((Program.name == program_name) & (School.name == school_name)).get()
	
	roi = solver.roi_for_program(program, duration = 4, income_level = "30,001-48,000")
	
	print "\nThe 20-year ROI for studying", program.name, "at USC is", str(roi)+"%"


# Commands for data_helper:

# data_helper.drop_tables()
# data_helper.create_tables()
# data_helper.populate_tables()
# data_helper.delete_all_schools()
# data_helper.import_data()


# Local commands:
# print_schools()
# print_programs()
# test_roi()


print ""