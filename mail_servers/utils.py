from django.conf import settings
from django.utils.module_loading import import_string

from mail_servers.servers import MailServer


def get_mail_server(config_key):
    config = settings.MAIL_SERVERS[config_key]

    Auth = import_string(config["AUTHENTICATION_CLASS"])
    auth = Auth(**config["AUTHENTICATION_OPTIONS"])
    mail_server = MailServer(
        auth,
        hostname=config["HOSTNAME"],
        pop3_port=config["POP3_PORT"],
    )

    return mail_server
