from src.logger import Logger
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

def send_email(sender_email, sender_password, receiver_emails, subject, body):
    try:
        # Set up the SMTP server
        smtp_server = 'smtpauth.intel.com'
        smtp_port = 587
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)

        # Create the email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(receiver_emails)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        Logger().getLogger().info("Created the mail")

        # Send the email
        server.sendmail(sender_email, receiver_emails, msg.as_string())
        server.quit()
        Logger().getLogger().info("Email sent successfully")
    except Exception as e:
        Logger().getLogger().error(f"Failed to send email: {e}")
