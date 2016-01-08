from flask import Flask, g


# Configure the database.
# data_model currently pulls from this, probably should be in a config file.
from peewee import *
from playhouse.postgres_ext import *

DATABASE = 'example.db'
DEBUG = True
SECRET_KEY = 'my favorite food is walrus mix'

app = Flask(__name__)
app.config.from_object(__name__)

database = PostgresqlExtDatabase("hiuni_database", user = "Andrew")

# Request handlers - I don't really understand these, but I'm hoping they'll let me avoid installing flask-peewee.
@app.before_request
def before_request():
	g.db = database
	g.db.connect()

@app.after_request
def after_request(response):
	g.db.close()
	return response


from data_model import *
from views import *


# def create_tables():
#     Post.create_table(True)
#     Comment.create_table(True)

if __name__ == '__main__':
    # create_tables()
    app.run()