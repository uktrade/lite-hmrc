from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from conf.authentication import HawkOnlyAuthentication
from mail.models import LicencePayload
from mail.serializers import (
    LiteLicenceUpdateSerializer,
    ForiegnTraderSerializer,
    GoodSerializer,
)


class UpdateLicence(APIView):
    authentication_classes = (HawkOnlyAuthentication,)

    def post(self, request):
        data = request.data.get("licence")

        errors = []

        serializer = LiteLicenceUpdateSerializer(data=data)

        if not serializer.is_valid():
            errors += serializer.errors

        if data:
            end_user = data.get("end_user")
            serializer = ForiegnTraderSerializer(data=end_user)
            if not serializer.is_valid():
                errors.append({"end_user_errors": serializer.errors})

            if data.get("goods") and data.get("type") == "siel":
                goods = data.get("goods")
                for good in goods:
                    serializer = GoodSerializer(data=good)
                    if not serializer.is_valid():
                        errors.append({"good_errors": serializer.errors})

            if not errors:
                LicencePayload.objects.create(lite_id=data["id"], reference=data["reference"], data=data)

                return JsonResponse(status=status.HTTP_201_CREATED, data={"data": data})

        return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data={"errors": errors})
