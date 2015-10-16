# Let's test it!


from data_model import *
import data_helper


def print_schools():
	print "\nSchools in the database:"
	for school in School.select():
		print "\n    -", school.name + ", with", school.programs.count(), "programs."
		print "        Location:", school.location["latitude"] + ",", school.location["longitude"]

def print_programs():
	print "\nPrograms in the database:"
	for program in Program.select():
		print "    -", program.name, "at", program.school.name
		print "        Median Salary: $" + str(program.median_salary)


# Commands for data_helper:

data_helper.drop_tables()
data_helper.create_tables()
data_helper.populate_tables()
# data_helper.delete_all_schools()
# data_helper.import_data()


# Local commands:
# print_schools()
# print_programs()


print ""