# Let's test it!


from data_model import *
import data_helper


def print_schools():
	print "\nSchools in the database:"
	for school in School.select():
		print "    -", school.name, "with", school.programs.count(), "programs."

def print_programs():
	print "\nPrograms in the database:"
	for program in Program.select():
		print "    -", program.name, "at", program.school.name


# Commands for data_helper:
# data_helper.delete_schools()
data_helper.load_schools_and_programs()
# data_helper.drop_tables()
# data_helper.create_tables()
# data_helper.populate_tables()


# Local commands:
# print_schools()
# print_programs()


print ""