from rest_framework import serializers

from mail.models import Mail, LicenceUpdate


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
            raise serializers.ValidationError(licence_update_serializer.errors)

        return mail


class UpdateResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mail
        fields = ["status", "response_file", "response_data"]

        def update(self, instance, validated_data):
            instance.status = validated_data["status"]
            instance.response_file = validated_data["response_file"]
            instance.response_data = validated_data["response_data"]


class UsageUpdateSerializer(serializers.ModelSerializer):
    mail = serializers.PrimaryKeyRelatedField(
        queryset=Mail.objects.all(), required=False
    )

    class Meta:
        model = LicenceUpdate
        fields = "__all__"

    def create(self, validated_data):
        instance, _ = LicenceUpdate.objects.get_or_create(**validated_data)
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


class InvalidEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mail
        fields = "__all__"
