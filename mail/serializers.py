from rest_framework import serializers

from mail.models import LicenseUpdate


class LicenseUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicenseUpdate
        fields = "__all__"
