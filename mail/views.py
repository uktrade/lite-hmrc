import logging
from typing import TYPE_CHECKING, Type

from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from conf.authentication import HawkOnlyAuthentication
from mail.celery_tasks import send_licence_details_to_hmrc
from mail.enums import LicenceActionEnum, LicenceTypeEnum, ReceptionStatusEnum
from mail.models import LicenceData, LicenceIdMapping, LicencePayload, Mail
from mail.serializers import (
    LiteOpenIndividualExportLicenceDataSerializer,
    LiteStandardIndividualExportLicenceDataSerializer,
    MailSerializer,
)

if TYPE_CHECKING:
    from rest_framework.serializers import Serializer  # noqa


logger = logging.getLogger(__name__)


class LicenceDataIngestView(APIView):
    authentication_classes = (HawkOnlyAuthentication,)

    def post(self, request):
        try:
            data = request.data["licence"]
        except KeyError:
            errors = [{"licence": "This field is required."}]
            logger.error(
                "Failed to create licence data for %s due to %s",
                request.data,
                errors,
            )
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data={"errors": errors})

        serializer_cls = self.get_serializer_cls(data["type"])
        serializer = serializer_cls(data=data)

        if not serializer.is_valid():
            errors = [{"licence": serializer.errors}]
            logger.error(
                "Failed to create licence data for %s due to %s",
                data,
                errors,
            )
            return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data={"errors": errors})

        if data["action"] == LicenceActionEnum.UPDATE:
            data["old_reference"] = LicenceIdMapping.objects.get(lite_id=data["old_id"]).reference
        else:
            data.pop("old_id", None)

        licence, created = LicencePayload.objects.get_or_create(
            lite_id=data["id"],
            reference=data["reference"],
            action=data["action"],
            old_lite_id=data.get("old_id"),
            old_reference=data.get("old_reference"),
            skip_process=False,
            defaults=dict(
                lite_id=data["id"],
                reference=data["reference"],
                data=data,
                old_lite_id=data.get("old_id"),
                old_reference=data.get("old_reference"),
            ),
        )

        logger.info("Created LicencePayload [%s, %s, %s]", licence.lite_id, licence.reference, licence.action)

        return JsonResponse(
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            data={"licence": licence.data},
        )

    def get_serializer_cls(self, app_type: str) -> Type["Serializer"]:
        app_type_to_serializer = {
            str(LicenceTypeEnum.SIEL): LiteStandardIndividualExportLicenceDataSerializer,
            str(LicenceTypeEnum.OIEL): LiteOpenIndividualExportLicenceDataSerializer,
        }
        if app_type in app_type_to_serializer.keys():
            serializer = app_type_to_serializer[app_type]
            return serializer
        raise NotImplementedError(f"Application type {app_type} not supported.")


class SendLicenceUpdatesToHmrc(APIView):
    authentication_classes = (HawkOnlyAuthentication,)

    def get(self, _):
        """Force the task of sending licence data to HMRC (I assume for testing?)"""

        success = send_licence_details_to_hmrc.delay()
        if success:
            return JsonResponse({}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SetAllToReplySent(APIView):
    """Updates status of all emails to REPLY_SENT"""

    authentication_classes = (HawkOnlyAuthentication,)

    def get(self, _):
        Mail.objects.all().update(status=ReceptionStatusEnum.REPLY_SENT)
        return JsonResponse({}, status=status.HTTP_200_OK)


class Licence(APIView):
    authentication_classes = (HawkOnlyAuthentication,)

    def get(self, request):
        """Fetch existing licence"""
        license_ref = request.GET.get("id", "")

        matching_licences = LicenceData.objects.filter(licence_ids__contains=license_ref)
        matching_licences_count = matching_licences.count()

        if matching_licences_count > 1:
            logger.warning("Too many matches for licence '%s'", license_ref)
            return JsonResponse({}, status=status.HTTP_400_BAD_REQUEST)

        elif matching_licences_count == 0:
            logger.warning("No matches for licence '%s'", license_ref)
            return JsonResponse({}, status=status.HTTP_404_NOT_FOUND)

        # Return single matching licence
        mail = matching_licences.first().mail
        serializer = MailSerializer(mail)

        return JsonResponse(serializer.data)
