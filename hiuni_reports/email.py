# Code for sending mail.

from hiuni_reports import application, mail

from flask import render_template
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
			render_template("email_report_ready.txt", template_folder = "emails", student = student, report = report),
			render_template("email_report_ready.html", template_folder = "emails", student = student, report = report)
		)