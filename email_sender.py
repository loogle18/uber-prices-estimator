from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import email_sender_address, email_sender_password


def send_email_message(mailto, message):
    msg = MIMEMultipart()
    msg["From"] = email_sender_address
    msg["To"] = mailto
    msg["Subject"] = "Uber Prices Estimator"
    msg.attach(MIMEText(message, "plain"))

    server = SMTP("smtp.gmail.com:587")
    server.starttls()
    server.login(email_sender_address, email_sender_password)
    text = msg.as_string()
    server.sendmail(email_sender_address, mailto, text)
    server.quit()
    print("Sent email to %s. Message: \n %s" % (mailto, message))
