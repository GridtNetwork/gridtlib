import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_email(to_emails, template_id, template_data):
    """
    Send a predefined email to email adresses.

    :param to_emails Email adresses to be reached
    :param template_id Sendgrid template to be used
    :param template_data Data to provide to the sendgrid template
    """
    msg = Mail(
        from_email="info@gridt.org", to_emails=to_emails
    )

    msg.template_id = template_id
    msg.template_data = template_data

    sg = SendGridAPIClient(os.environ["EMAIL_API_KEY"])
    resp = sg.send(msg)
    return resp.status_code, resp.body, resp.headers
