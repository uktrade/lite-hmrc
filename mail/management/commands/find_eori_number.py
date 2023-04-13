from django.core.management import BaseCommand

from mail.enums import ReceptionStatusEnum, ReplyStatusEnum
from mail.models import Mail


class LicenceNotFoundError(Exception):
    pass


class Command(BaseCommand):
    help = """Given a licence number will find the EORI number that we sent to
    HMRC
    """

    def add_arguments(self, parser):
        parser.add_argument(
            dest="licence_number",
            type=str,
            help="Licence number to find EORI number",
        )

    def get_formatted_licence_number(self, licence_number):
        return "".join(licence_number.split("/")[1:])

    def get_trade_number(self, sent_data, licence_number):
        lines = iter(sent_data.split("\n"))
        line = next(lines)
        while line:
            formatted_licence_number = self.get_formatted_licence_number(licence_number)
            if f"licence\\{formatted_licence_number}" not in line:
                line = next(lines)
                continue
            licence_line = next(lines)
            while licence_line:
                tokens = licence_line.split("\\")
                if tokens[1] != "trader":
                    licence_line = next(lines)
                    continue
                if tokens[1] == "end":
                    break
                return tokens[3]
            line = next(line)
        raise LicenceNotFoundError("Trader number not found")

    def get_licence_reply_status(self, response_data, licence_number):
        formatted_licence_number = self.get_formatted_licence_number(licence_number)
        for line in response_data.split("\n"):
            tokens = line.strip().split("\\")
            if tokens[2] != formatted_licence_number:
                continue
            return tokens[1]
        raise LicenceNotFoundError("HMRC reply not found")

    def handle(self, licence_number, *args, **kwargs):
        self.stdout.write(f"Finding EORI number for {licence_number}")

        try:
            mail = Mail.objects.get(sent_data__contains=licence_number)
        except Mail.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No mail object found for {licence_number}"))
            return
        except Mail.MultipleObjectsReturned:
            self.stdout.write(self.style.ERROR(f"Found multiple mail objects referring to {licence_number}"))
            return

        try:
            trade_number = self.get_trade_number(mail.sent_data, licence_number)
        except LicenceNotFoundError:
            self.stdout.write(f"Licence not found for {licence_number}")
        else:
            self.stdout.write(self.style.SUCCESS(f"EORI number: {trade_number}"))

        if mail.status != ReceptionStatusEnum.REPLY_SENT:
            self.stdout.write(self.style.ERROR(f"The mail has status {mail.status}"))
            return

        response_data = mail.response_data
        if not mail.response_data:
            self.stdout.write(self.style.ERROR("No response_data in mail object"))

        hmrc_reply_status = self.get_licence_reply_status(response_data, licence_number)
        if hmrc_reply_status != ReplyStatusEnum.ACCEPTED:
            self.stdout.write(self.style.ERROR(f"The reponse had status {hmrc_reply_status}"))
            return
        self.stdout.write(self.style.SUCCESS(f"The response had status {hmrc_reply_status}"))
