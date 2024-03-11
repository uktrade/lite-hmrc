import factory

from uuid import uuid4

from mail.enums import LicenceActionEnum
from mail.models import LicencePayload, Mail


class MailFactory(factory.django.DjangoModelFactory):
    edi_filename = "message_filename"
    edi_data = "1\\fileHeader\\SPIRE\\CHIEF\\licenceData\\202104090304\\96839\\N"
    raw_data = "1\\fileHeader\\SPIRE\\CHIEF\\licenceData\\202104090304\\96839\\N"
    sent_data = "1\\fileHeader\\SPIRE\\CHIEF\\licenceData\\202104090304\\96839\\N"

    class Meta:
        model = Mail


class LicencePayloadFactory(factory.django.DjangoModelFactory):
    lite_id = uuid4()
    reference = factory.Faker("word")
    action = LicenceActionEnum.INSERT
    data = {"name": "exporter name"}

    class Meta:
        model = LicencePayload
