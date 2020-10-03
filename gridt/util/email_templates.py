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
