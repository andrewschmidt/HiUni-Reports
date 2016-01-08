# Configure the database.

from flask import Flask, g

from peewee import *
from playhouse.postgres_ext import *


DATABASE = "hiuni_database"
USER = "Andrew"
DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)

database = PostgresqlExtDatabase(DATABASE)


# Request handlers
# Apparently this is all I really needed from flask-peewee.
@app.before_request
def before_request():
	g.db = database
	g.db.connect()

@app.after_request
def after_request(response):
	g.db.close()
	return response