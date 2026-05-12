from django.conf import settings
from rest_framework import serializers

from .models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id',
            'full_name',
            'first_name',
            'last_name',
            'middle_name',
            'hire_date',
            'status',
            'photo',
            'photo_url',
        ]

    def get_full_name(self, obj):
        return obj.full_name()

    def get_photo_url(self, obj):
        from .views import get_minio_url

        return get_minio_url(obj.photo)
