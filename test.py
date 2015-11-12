# Let's test it!


from data_model import *
import data_helper
import solver


def print_schools():
	print "\nSchools in the database:"
	for school in schools:
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
		print "        CIP: " + str(program.cip)
		print "        Median Salary: $" + str(program.median_salary)
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


def test_best_roi_for_cip():
	cip = "45.06"
	programs = solver.programs_by_roi_for_cip(cip, duration = 4, income_level = "30,001-48,000")
	
	print "\nBest schools for CIP " + cip + ", sorted by ROI:\n"
	for program in programs:
		print "    -", program.name, "at", program.school.name
		print "        CIP: " + str(program.cip)
		print "        Median Salary: $" + str(program.median_salary)
		roi = solver.roi_for_program(program, duration = 4, income_level = "30,001-48,000")
		if roi:
			print "        ROI: " + str(roi) + "%"
		print ""
		

def swap_cip_for_test_purposes():
	usc = School.get(School.name == "University of Southern California")
	program = Program.select().join(School).where(Program.name == "Entrepreneurial Studies", School.name == "University of Southern California").get()
	print "Found the program " + program.name + " at the " + program.school.name + "."
	if program.cip == "52.07":
		program.cip = "45.06" # The CIP for...
		program.save()
		print "Changed its CIP to: " + program.cip
	else:
		program.cip = "52.07" # The original CIP.
		print "Reverted its CIP to: " + program.cip
		program.save()

	
# Commands for data_helper:

# data_helper.drop_tables()
# data_helper.delete_all_schools()
# data_helper.create_tables()
# data_helper.populate_tables()
# data_helper.import_data()


# Local commands:
<<<<<<< HEAD
print_schools()
# print_programs()
# test_roi()
# swap_cip_for_test_purposes()
# test_best_roi_for_cip()
=======
# print_schools()
# swap_cip_for_test_purposes()
# print_programs()
# test_roi()
test_best_roi_for_cip()
>>>>>>> origin/building-the-solver

print ""