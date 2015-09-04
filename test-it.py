# Let's test it!

import hiuni_data

data_helper = hiuni_data.data_helper()
schools = data_helper.load_schools_from_xls("PayScale Sample (altered).xlsx")

print "\nLoaded schools, here they are: \n"

for school in schools:
	print school.name
	for major in school.majors:
		print "	- ", major.name
		# print "		- median salary:", major.median_salary
		# print "		- CIP code:", major.cip
		# print ""
	print ""