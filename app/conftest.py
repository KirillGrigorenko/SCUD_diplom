import pytest
from datetime import date
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from services.models import Employee


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username='admin', password='admin123', email='admin@test.com'
    )


@pytest.fixture
def emp_user(db):
    return User.objects.create_user(username='emp1', password='pass123')


@pytest.fixture
def employee(db, emp_user):
    return Employee.objects.create(
        user=emp_user,
        last_name='Тестов',
        first_name='Тест',
        middle_name='Тестович',
        hire_date=date(2023, 1, 1),
        status='active',
    )


@pytest.fixture
def admin_client(db, admin_user):
    client = APIClient()
    client.force_login(admin_user)
    return client


@pytest.fixture
def employee_client(db, emp_user, employee):
    client = APIClient()
    client.force_login(emp_user)
    return client
