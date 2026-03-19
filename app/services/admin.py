from django.contrib import admin
from .models import (
    Department, Position, AccessLevel, Employee,
    Administrator, EmployeeCard, BiometricData,
    AccessRight, AccessHistory
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'team_name')
    search_fields = ('name',)


@admin.register(AccessLevel)
class AccessLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'zone')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'status', 'hire_date')
    search_fields = ('last_name', 'first_name')
    list_filter = ('status',)


@admin.register(Administrator)
class AdministratorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'hire_date')

@admin.register(EmployeeCard)
class EmployeeCardAdmin(admin.ModelAdmin):
    list_display = ('employee', 'position', 'citizenship')


@admin.register(BiometricData)
class BiometricDataAdmin(admin.ModelAdmin):
    list_display = ('employee', 'status', 'face_registered_at', 'palm_registered_at')


@admin.register(AccessRight)
class AccessRightAdmin(admin.ModelAdmin):
    list_display = ('employee', 'access_level', 'assigned_at', 'expires_at')


@admin.register(AccessHistory)
class AccessHistoryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'datetime', 'access_point', 'result', 'method')
    list_filter = ('result', 'method')