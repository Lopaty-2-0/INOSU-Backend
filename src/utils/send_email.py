import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email(receiver_email, subject, html, plain_text):
    sender_email = os.getenv("SENDER_EMAIL")
    password = os.getenv("APP_TOKEN")
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    message.attach(MIMEText(plain_text, "plain"))
    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
