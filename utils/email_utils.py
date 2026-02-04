"""
Email utilities using SMTP.
Configure via environment variables:
- SMTP_HOST
- SMTP_PORT (default 587)
- SMTP_USER
- SMTP_PASS
- SMTP_FROM (optional; defaults to SMTP_USER)
"""

import os
import smtplib
import ssl
from email.message import EmailMessage


def send_email(to_email: str, subject: str, body: str, html_body: str | None = None) -> None:
	host = os.getenv('SMTP_HOST')
	port = int(os.getenv('SMTP_PORT') or 587)
	user = os.getenv('SMTP_USER')
	password = os.getenv('SMTP_PASS')
	sender = os.getenv('SMTP_FROM') or user

	if not host or not user or not password or not sender:
		raise RuntimeError('SMTP is not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASS (and optional SMTP_FROM).')

	msg = EmailMessage()
	msg['Subject'] = subject
	msg['From'] = sender
	msg['To'] = to_email
	msg.set_content(body)
	if html_body:
		msg.add_alternative(html_body, subtype='html')

	if port == 465:
		context = ssl.create_default_context()
		with smtplib.SMTP_SSL(host, port, context=context) as server:
			server.login(user, password)
			server.send_message(msg)
	else:
		with smtplib.SMTP(host, port) as server:
			server.ehlo()
			server.starttls(context=ssl.create_default_context())
			server.ehlo()
			server.login(user, password)
			server.send_message(msg)
