# Code for sending mail.

from hiuni_reports import application, mail, ts

from flask import render_template, url_for
from flask.ext.mail import Message

from decorators import async



@async
def send_email_async(application, msg):
	with application.app_context():
		mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
	msg = Message(subject, sender = sender, recipients = recipients)
	msg.body = text_body
	msg.html = html_body
	send_email_async(application, msg)


def report_notification(student, report):
	user = student.customer.user.get()
	send_email(
			"%s, your HiUni Report is ready" % student.first_name, 
			application.config["ADMINEMAIL"],
			[user.email],
			render_template("email_report_ready.txt", student = student, report = report),
			render_template("email_report_ready.html", student = student, report = report)
		)


def questionnaire_notification(student, report):
	send_email(
			"A new report requires editing",
			application.config["ADMINEMAIL"],
			[application.config["ADMINEMAIL"]],
			render_template("email_questionnaire.txt", student = student, report = report),
			render_template("email_questionnaire.html", student = student, report = report)
		)


def confirm_email(user):
	token = ts.dumps(user.email, salt = application.config["EMAIL_CONFIRM_KEY"])
	confirm_url = url_for("confirm_email", token = token, _external = True)

	send_email(
			"Please confirm your email",
			application.config["ADMINEMAIL"],
			[user.email],
			render_template("email_confirm.txt", confirm_url = confirm_url),
			render_template("email_confirm.html", confirm_url = confirm_url)
		)