from rest_framework import serializers
from mail.models import Mail, LicenceUpdate, UsageUpdate
from mail.services.logging_decorator import lite_log
import logging

logger = logging.getLogger(__name__)


class LicenceUpdateSerializer(serializers.ModelSerializer):
    mail = serializers.PrimaryKeyRelatedField(
        queryset=Mail.objects.all(), required=False
    )

    class Meta:
        model = LicenceUpdate
        fields = "__all__"

    def create(self, validated_data):
        instance, _ = LicenceUpdate.objects.get_or_create(**validated_data)
        return instance


class LicenceUpdateMailSerializer(serializers.ModelSerializer):
    licence_update = LicenceUpdateSerializer(write_only=True)

    class Meta:
        model = Mail
        fields = [
            "id",
            "edi_filename",
            "edi_data",
            "extract_type",
            "raw_data",
            "licence_update",
        ]

    def create(self, validated_data):
        licence_update_data = validated_data.pop("licence_update")
        mail, _ = Mail.objects.get_or_create(**validated_data)

        licence_update_data["mail"] = mail.id

        licence_update_serializer = LicenceUpdateSerializer(data=licence_update_data)
        if licence_update_serializer.is_valid():
            licence_update_serializer.save()
        else:
            lite_log(logger, logging.ERROR, licence_update_serializer.errors)
            raise serializers.ValidationError(licence_update_serializer.errors)

        return mail


class UpdateResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mail
        fields = ["status", "response_filename", "response_data", "response_subject"]

        def update(self, instance, validated_data):
            instance.status = validated_data["status"]
            instance.response_file = validated_data["response_filename"]
            instance.response_data = validated_data["response_data"]
            instance.response_subject = validated_data["response_subject"]

            instance.save()

            return instance


class UsageUpdateSerializer(serializers.ModelSerializer):
    mail = serializers.PrimaryKeyRelatedField(
        queryset=Mail.objects.all(), required=False
    )

    class Meta:
        model = UsageUpdate
        fields = "__all__"

    def create(self, validated_data):
        instance, _ = UsageUpdate.objects.get_or_create(**validated_data)
        return instance


class UsageUpdateMailSerializer(serializers.ModelSerializer):
    usage_update = UsageUpdateSerializer(write_only=True)

    class Meta:
        model = Mail
        fields = [
            "id",
            "edi_filename",
            "edi_data",
            "extract_type",
            "raw_data",
            "usage_update",
        ]

    def create(self, validated_data):
        usage_update_data = validated_data.pop("usage_update")
        mail, _ = Mail.objects.get_or_create(**validated_data)

        usage_update_data["mail"] = mail.id

        usage_update_serializer = UsageUpdateSerializer(data=usage_update_data)
        if usage_update_serializer.is_valid():
            usage_update_serializer.save()
        else:
            raise serializers.ValidationError(usage_update_serializer.errors)

        return mail


class InvalidEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mail
        fields = "__all__"

    def create(self, validated_data):
        mail, _ = Mail.objects.get_or_create(**validated_data)

        return mail


class GoodSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=2000, allow_blank=False)
    quantity = serializers.DecimalField(decimal_places=3, max_digits=13)
    unit = serializers.CharField()

    class Meta:
        fields = ("description", "quantity", "unit")


class TraderSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=80, allow_blank=False)
    address_1 = serializers.CharField(max_length=35)
    address_2 = serializers.CharField(max_length=35, required=False)
    address_3 = serializers.CharField(max_length=35, required=False)
    address_4 = serializers.CharField(max_length=35, required=False)
    address_5 = serializers.CharField(max_length=35, required=False)
    postcode = serializers.CharField()

    class Meta:
        fields = (
            "name",
            "address_1",
            "address_2",
            "address_3",
            "address_4",
            "address_5",
            "postcode",
        )


class ForiegnTraderSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=80, allow_blank=False)
    address_1 = serializers.CharField(max_length=35)
    address_2 = serializers.CharField(max_length=35, required=False)
    address_3 = serializers.CharField(max_length=35, required=False)
    address_4 = serializers.CharField(max_length=35, required=False)
    address_5 = serializers.CharField(max_length=35, required=False)
    postcode = serializers.CharField()
    country = serializers.CharField(allow_blank=False)

    class Meta:
        fields = (
            "name",
            "address_1",
            "address_2",
            "address_3",
            "address_4",
            "address_5",
            "postcode",
            "country",
        )


class LiteLicenceUpdateSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=35)
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    class Meta:
        fields = (
            "id",
            "start_date",
            "end_date",
        )
