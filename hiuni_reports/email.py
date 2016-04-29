# Code for sending mail.

from hiuni_reports import application, mail

from flask import render_template
from flask.ext.mail import Message

from decorators import async


def send_email(subject, sender, recipients, text_body, html_body):
	msg = Message(subject, sender = sender, recipients = recipients)
	msg.body = text_body
	msg.html = html_body
	mail.send(msg)


@async
def send_email_async(subject, sender, recipients, text_body, html_body):
	with application.app_context():
		send_email(subject, sender, recipients, text_body, html_body)


def report_notification(student, report):
	user = student.customer.user.get()
	send_email_async(
			"%s, your HiUni Report is ready" % student.first_name, 
			application.config["ADMINEMAIL"],
			[user.email],
			render_template("email_report_ready.txt", template_folder = "emails", student = student, report = report),
			render_template("email_report_ready.html", template_folder = "emails", student = student, report = report)
		)