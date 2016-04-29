# Code for sending mail.

from hiuni_reports import application, mail

from flask import render_template
from flask.ext.mail import Message



def send_email(subject, sender, recipients, text_body, html_body):
	msg = Message(subject, sender = sender, recipients = recipients)
	msg.body = text_body
	msg.html = html_body
	mail.send(msg)


def report_notification(student, report):
	user = student.customer.user.get()
	send_email(
			"%s, your HiUni Report is ready" % student.first_name, 
			application.config["ADMINEMAIL"],
			[user.email],
			render_template("email_report_ready.txt", template_folder = "emails", student = student, report = report),
			render_template("email_report_ready.html", template_folder = "emails", student = student, report = report)
		)