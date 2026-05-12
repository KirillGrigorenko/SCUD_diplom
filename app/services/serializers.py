from rest_framework import serializers
from .models import Employee, EmployeeCard


class EmployeeCardSerializer(serializers.ModelSerializer):
    position_id = serializers.SerializerMethodField()
    position_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeCard
        fields = [
            'passport_series', 'passport_number', 'citizenship',
            'address', 'snils', 'inn',
            'position_id', 'position_name', 'department_name',
        ]

    def get_position_id(self, obj):
        return obj.position.pk if obj.position else None

    def get_position_name(self, obj):
        return obj.position.name if obj.position else None

    def get_department_name(self, obj):
        if obj.position and obj.position.department:
            return obj.position.department.name
        return None


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()
    position_id = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    employee_card = EmployeeCardSerializer(source='employeecard', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'full_name', 'first_name', 'last_name', 'middle_name',
            'hire_date', 'status', 'photo', 'photo_url',
            'position', 'position_id', 'department', 'employee_card',
        ]

    def get_full_name(self, obj):
        return obj.full_name()

    def get_photo_url(self, obj):
        from .views import get_minio_url
        return get_minio_url(obj.photo)

    def get_position(self, obj):
        card = getattr(obj, 'employeecard', None)
        return card.position.name if card and card.position else None

    def get_position_id(self, obj):
        card = getattr(obj, 'employeecard', None)
        return card.position.pk if card and card.position else None

    def get_department(self, obj):
        card = getattr(obj, 'employeecard', None)
        if card and card.position and card.position.department:
            return card.position.department.name
        return None
