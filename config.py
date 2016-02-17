# CONFIGURATION

DATABASE = {
	"name": "hiuni_database",
	"engine": "playhouse.postgres_ext.PostgresqlExtDatabase",
	"host": "hiuni.cygnxnxnzo7j.us-west-1.rds.amazonaws.com",
	"port": "5432",
	"user": "andrew",
	"password": "ihPCU6gX2YipqAq"
}

DEBUG = True

BCRYPT_LOG_ROUNDS = 15

# Forms config:
WTF_CSRF_ENABLED = True
SECRET_KEY = 'secret'