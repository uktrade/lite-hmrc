import poplib

from django.core.management import BaseCommand

from mail.libraries.routing_controller import get_hmrc_to_dit_mailserver, get_spire_to_dit_mailserver


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write("Checking mailserver connections")

        mailservers_to_check_factories = (
            get_hmrc_to_dit_mailserver,
            get_spire_to_dit_mailserver,
        )
        for mailserver_to_check_factory in mailservers_to_check_factories:
            self.stdout.write(f"Checking {mailserver_to_check_factory.__name__}")
            mailserver = mailserver_to_check_factory()
            try:
                with mailserver.connect_to_pop3() as pop3_connection:
                    self.stdout.write(pop3_connection.welcome.decode("ascii"))
            except poplib.error_proto as e:
                response, *_ = e.args
                self.stdout.write(self.style.ERROR(response))
