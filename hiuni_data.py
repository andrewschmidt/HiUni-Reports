# The data model, and classes related to managing data in and out.


class School:
	def __init__(self, name, IPEDS_id, majors):
		self.name = name
		self.IPEDS_id = IPEDS_id
		self.majors = majors


class Major:
	def __init__(self, name, cip, median_salary):
		self.name = name
		self.cip = cip
		self.median_salary = median_salary



import xlrd

class data_helper:
	
	def __init__(self):
		return

	def get_school_names_from_sheet(self, sheet):
		school_names = []
		
		number_of_rows = sheet.nrows - 1

		cell_values = sheet.col_values(1, start_rowx = 1, end_rowx = None)

		for value in cell_values:
			if not value in school_names:
				school_names.append(value)

		return school_names


	def get_school_ids_from_sheet(self, sheet):
		school_ids = []
		
		number_of_rows = sheet.nrows - 1

		cell_values = sheet.col_values(0, start_rowx = 1, end_rowx = None)

		for value in cell_values:
			if not value in school_ids:
				school_ids.append(value)

		return school_ids


	def get_majors_for_school_with_id(self, school_id, from_sheet):
		majors = []

		sheet = from_sheet
		number_of_rows = sheet.nrows

		for row in range(number_of_rows):
			row_id = sheet.cell_value(rowx = row, colx = 0)
			major_name = sheet.cell_value(rowx = row, colx = 2)
			cip_code = sheet.cell_value(rowx = row, colx = 3)
			median_salary = sheet.cell_value(rowx = row, colx = 5)

			if row_id == school_id:
				major = Major(name = major_name, cip = cip_code, median_salary = median_salary)
				majors.append(major)

		return majors


	def load_schools_from_xls(self, xls_name):
		# Load the workbook & sheet:
		book = xlrd.open_workbook(xls_name)
		sheet = book.sheet_by_name("4-Digit CIP - Experienced Pay")

		# First, let's get basic info about the schools.
		school_names = self.get_school_names_from_sheet(sheet)
		school_ids = self.get_school_ids_from_sheet(sheet)

		# Next, let's get each school's majors as an array of Major objects, and we'll make School objects in the process.
		schools = []

		for i in range(len(school_ids)):
			majors = self.get_majors_for_school_with_id(school_ids[i], from_sheet = sheet)
			school = School(name = school_names[i], IPEDS_id = school_ids[i], majors = majors)
			schools.append(school)

		return schools
