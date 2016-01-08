# Run this!

# from flask import Flask

from config import *
from views import *


def create_tables():
	School.create_table(True)
	Program.create_table(True)
	Career.create_table(True)
	Student.create_table(True)
	Recipe.create_table(True)
	Step.create_table(True)
	Pathway.create_table(True)
	Pathway_Step.create_table(True)

if __name__ == '__main__':
    create_tables()
    app.run()