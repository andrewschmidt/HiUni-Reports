# distance_test.py

from models import *

def find_programs_near(latitude, longitude, distance, kind, cip):
	print "\nHere we go!!!!!!!!!"

	latitude_str = str(latitude)
	longitude_str = str(longitude)

	long_lat = str(longitude_str + ", " + latitude_str)
	print "\nLong_lat:", long_lat

	distance = str(distance)
	print "\nDistance:", distance

	query_string = "SELECT * FROM school WHERE earth_box(ll_to_earth("+long_lat+"), "+distance+") @> ll_to_earth(longitude, latitude) AND kind = '"+kind+"' ORDER BY earth_distance(ll_to_earth("+long_lat+"), ll_to_earth(longitude, latitude));"

	print "\nAttempting query:", query_string
	print "\nPrograms found:"
	
	for school in School.raw(query_string):
		try:
			desired_program = Program.select().join(School).where((Program.cip == cip) & (School.ipeds_id == school.ipeds_id)).get()
			print "   -", program.name, "at", program.school.name
		except Exception:
			print "   - Didn't find the right program at nearby school", school.name

student_latitude = 32.7150
student_longitude = -117.1625
distance = 7500
school_kind = "Community College"

find_programs_near(latitude = student_latitude, longitude = student_longitude, distance = distance, kind = school_kind, cip = "24.0102")