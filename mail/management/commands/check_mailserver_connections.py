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
                pop3_connection = mailserver.connect_to_pop3()
            except poplib.error_proto as e:
                response, *_ = e.args
                self.stdout.write(self.style.ERROR(response))
            else:
                self.stdout.write(pop3_connection.welcome.decode("ascii"))
            finally:
                mailserver.quit_pop3_connection()
