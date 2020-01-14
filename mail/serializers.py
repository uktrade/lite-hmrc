from rest_framework import serializers

from mail.models import Mail


class LicenceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mail
        fields = [
            "id",
            "created_at",
            "edi_filename",
            "edi_data",
            "extract_type",
            "raw_data",
        ]


class LicenceUpdateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mail
        fields = ["last_submitted_on", "status", "response_file", "response_data"]


class InvalidEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mail
        fields = "__all__"
