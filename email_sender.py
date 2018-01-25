from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Email, Content, Mail
from config import sendgrid_api_key


def send_email_message(mailto, message):
    try:
        sendgrid_client = SendGridAPIClient(apikey=sendgrid_api_key)
        from_email = Email("noreply@uberestimator.com")
        subject = "Uber Prices Estimator"
        to_email = Email(mailto)
        content = Content("text/plain", message)
        mail = Mail(from_email, subject, to_email, content)
        response = sendgrid_client.client.mail.send.post(request_body=mail.get())
        print("Sent email to %s with status_code: %s. Message: \n %s" % (mailto, response.status_code, message))
    except Exception as e:
        print(e)
