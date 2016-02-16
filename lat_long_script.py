# Moving schools' location values into separate latitude and longitude points.
# This will make sorting easier.

from peewee import *
from playhouse.migrate import *

from data_model import *

students = Student.select()
for student in students:
	student.save()

# migrator = PostgresqlMigrator(database)

# migrate(
# 	migrator.add_column("student", "latitude", FloatField(null = True)),
# 	migrator.add_column("student", "longitude", FloatField(null = True)),
# 	migrator.drop_column("school", "location")
# )

# students = Student.select()

# for student in students:
# 	student.latitude = student.location["latitude"]
# 	student.longitude = student.location["longitude"]
# 	print str(school.latitude), ", ", str(school.longitude)
# 	school.save()