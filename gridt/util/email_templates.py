"""Gridt email templates."""
from .send_email import send_email
import os


def send_password_reset_email(email, token):
    """
    Send a predefined email template with reset token to email adress.

    note::
      Function depends on the $PASSWORD_RESET_TEMPLATE and the $EMAIL_API_KEY
      environment variables to have been set.

    :param email Email adress that will be sent to
    :param token Token to be sent
    """
    template_id = os.environ["PASSWORD_RESET_TEMPLATE"]
    template_data = {
        "link": (
            "https://app.gridt.org/user/reset_password/confirm"
            f"?token={token}"
        )
    }

    send_email(email, template_id, template_data)


def send_password_change_notification(email):
    """
    Send a predefined email template with reset token to email adress.

    note::
      Function depends on the $PASSWORD_CHANGE_NOTIFICATION_TEMPLATE and
      the $EMAIL_API_KEY environment variables to have been set.

    :param email Email adress that will be sent to
    :param token Token to be sent
    """
    template_id = os.environ["PASSWORD_CHANGE_NOTIFICATION_TEMPLATE"]
    template_data = {
        "link": "https://app.gridt.org/user/reset_password/request"
    }

    send_email(email, template_id, template_data)


def send_email_change_email(email, username, token):
    """Send a predefined email template with link to change email."""
    template_id = os.environ["EMAIL_CHANGE_TEMPLATE"]
    template_data = {
        "username": username,
        "link": (
            f"https://app.gridt.org/user/change_email/confirm?token={token}"
        ),
    }

    send_email(email, template_id, template_data)


def send_email_change_notification(email, username):
    """Send a predefined emaill template to send a new email adress."""
    template_id = os.environ["EMAIL_CHANGE_NOTIFICATION_TEMPLATE"]
    template_data = {"username": username}

    send_email(email, template_id, template_data)
