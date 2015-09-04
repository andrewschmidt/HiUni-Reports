# Let's test it!

from hiuni_data import *

data_helper = data_helper()


# Commands:
data_helper.load_schools_and_majors()
# data_helper.delete_schools()


# Proving the concept:
print "\nSchools in the database:"
for school in School.select():
	print "    -", school.name, "with", school.majors.count(), "majors."
print ""