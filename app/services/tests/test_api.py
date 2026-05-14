import pytest
from datetime import date
from django.contrib.auth.models import User

from services.models import (
    AccessHistory, AccessLevel, AccessRight, BiometricData, Employee
)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Auth — Login / Logout / Me
# ---------------------------------------------------------------------------

class TestLoginAPI:
    URL = '/api/auth/login/'

    def test_success(self, api_client, admin_user):
        r = api_client.post(self.URL, {'username': 'admin', 'password': 'admin123'})
        assert r.status_code == 200
        assert 'detail' in r.data

    def test_wrong_password(self, api_client, admin_user):
        r = api_client.post(self.URL, {'username': 'admin', 'password': 'bad'})
        assert r.status_code == 401

    def test_missing_fields(self, api_client):
        r = api_client.post(self.URL, {})
        assert r.status_code == 400

    def test_unknown_user(self, api_client):
        r = api_client.post(self.URL, {'username': 'nobody', 'password': 'pass'})
        assert r.status_code == 401


class TestLogoutAPI:
    URL = '/api/auth/logout/'

    def test_logout_returns_200(self, admin_client):
        r = admin_client.post(self.URL)
        assert r.status_code == 200


class TestMeAPI:
    URL = '/api/auth/me/'

    def test_unauthenticated_returns_403(self, api_client):
        r = api_client.get(self.URL)
        assert r.status_code == 403

    def test_superuser_is_admin(self, admin_client, admin_user):
        r = admin_client.get(self.URL)
        assert r.status_code == 200
        assert r.data['username'] == 'admin'
        assert r.data['is_admin'] is True
        assert r.data['employee_id'] is None

    def test_employee_not_admin(self, employee_client, employee):
        r = employee_client.get(self.URL)
        assert r.status_code == 200
        assert r.data['is_admin'] is False
        assert r.data['employee_id'] == employee.id


# ---------------------------------------------------------------------------
# Employee list
# ---------------------------------------------------------------------------

class TestEmployeeListAPI:
    URL = '/api/employees/'

    def test_unauthenticated_returns_403(self, api_client):
        r = api_client.get(self.URL)
        assert r.status_code == 403

    def test_admin_sees_all(self, admin_client, employee):
        r = admin_client.get(self.URL)
        assert r.status_code == 200
        ids = [e['id'] for e in r.data]
        assert employee.id in ids

    def test_employee_sees_only_self(self, employee_client, employee):
        other = User.objects.create_user(username='other_a', password='pass')
        other_emp = Employee.objects.create(
            user=other, last_name='Другой', first_name='А',
            hire_date=date(2023, 1, 1)
        )
        r = employee_client.get(self.URL)
        assert r.status_code == 200
        ids = [e['id'] for e in r.data]
        assert employee.id in ids
        assert other_emp.id not in ids


# ---------------------------------------------------------------------------
# Employee detail
# ---------------------------------------------------------------------------

class TestEmployeeDetailAPI:
    def test_admin_can_view(self, admin_client, employee):
        r = admin_client.get(f'/api/employees/{employee.id}/')
        assert r.status_code == 200
        assert r.data['id'] == employee.id

    def test_employee_can_view_self(self, employee_client, employee):
        r = employee_client.get(f'/api/employees/{employee.id}/')
        assert r.status_code == 200

    def test_employee_cannot_view_others(self, employee_client):
        other = User.objects.create_user(username='other_b', password='pass')
        other_emp = Employee.objects.create(
            user=other, last_name='Другой', first_name='Б',
            hire_date=date(2023, 1, 1)
        )
        r = employee_client.get(f'/api/employees/{other_emp.id}/')
        assert r.status_code == 403

    def test_not_found(self, admin_client):
        r = admin_client.get('/api/employees/99999/')
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Employee create
# ---------------------------------------------------------------------------

class TestEmployeeCreateAPI:
    URL = '/api/employees/create/'

    @staticmethod
    def _payload(username='newuser99'):
        return {
            'username': username,
            'password': 'Pass123!',
            'last_name': 'Новый',
            'first_name': 'Сотрудник',
            'hire_date': '2024-01-01',
        }

    def test_admin_creates_employee(self, admin_client):
        r = admin_client.post(self.URL, self._payload())
        assert r.status_code == 201
        assert User.objects.filter(username='newuser99').exists()
        assert 'id' in r.data

    def test_non_admin_forbidden(self, employee_client):
        r = employee_client.post(self.URL, self._payload('otheruser99'))
        assert r.status_code == 403

    def test_missing_required_fields(self, admin_client):
        r = admin_client.post(self.URL, {'username': 'x'})
        assert r.status_code == 400

    def test_duplicate_username(self, admin_client, admin_user):
        r = admin_client.post(self.URL, self._payload('admin'))
        assert r.status_code == 400

    def test_invalid_inn(self, admin_client):
        payload = self._payload('inntest99')
        payload['inn'] = '123'
        r = admin_client.post(self.URL, payload)
        assert r.status_code == 400

    def test_valid_inn_accepted(self, admin_client):
        payload = self._payload('inntest98')
        payload['inn'] = '123456789012'
        r = admin_client.post(self.URL, payload)
        assert r.status_code == 201


# ---------------------------------------------------------------------------
# Employee update
# ---------------------------------------------------------------------------

class TestEmployeeUpdateAPI:
    def test_admin_can_update_name(self, admin_client, employee):
        r = admin_client.patch(
            f'/api/employees/{employee.id}/update/',
            {'last_name': 'Обновлён'},
        )
        assert r.status_code == 200
        employee.refresh_from_db()
        assert employee.last_name == 'Обновлён'

    def test_admin_can_update_status(self, admin_client, employee):
        r = admin_client.patch(
            f'/api/employees/{employee.id}/update/',
            {'status': 'blocked'},
        )
        assert r.status_code == 200
        employee.refresh_from_db()
        assert employee.status == 'blocked'

    def test_non_admin_forbidden(self, employee_client, employee):
        r = employee_client.patch(
            f'/api/employees/{employee.id}/update/',
            {'last_name': 'Попытка'},
        )
        assert r.status_code == 403

    def test_invalid_inn_rejected(self, admin_client, employee):
        r = admin_client.patch(
            f'/api/employees/{employee.id}/update/',
            {'inn': 'bad'},
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# Access history (global)
# ---------------------------------------------------------------------------

class TestAllHistoryAPI:
    URL = '/api/history/'

    @staticmethod
    def _hist(employee, **kw):
        return AccessHistory.objects.create(
            employee=employee,
            access_point=kw.get('access_point', 'main'),
            result=kw.get('result', 'allowed'),
            method=kw.get('method', 'password'),
        )

    def test_admin_can_view(self, admin_client, employee):
        self._hist(employee)
        r = admin_client.get(self.URL)
        assert r.status_code == 200
        assert len(r.data) >= 1

    def test_non_admin_forbidden(self, employee_client):
        r = employee_client.get(self.URL)
        assert r.status_code == 403

    def test_filter_by_result_allowed(self, admin_client, employee):
        self._hist(employee, result='allowed')
        self._hist(employee, result='denied')
        r = admin_client.get(self.URL + '?result=allowed')
        assert r.status_code == 200
        assert all(h['result'] == 'allowed' for h in r.data)

    def test_filter_by_employee_name(self, admin_client, employee):
        self._hist(employee)
        r = admin_client.get(self.URL + '?employee=Тестов')
        assert r.status_code == 200
        assert len(r.data) >= 1

    def test_unknown_result_filter_ignored(self, admin_client, employee):
        self._hist(employee, result='allowed')
        r = admin_client.get(self.URL + '?result=invalid')
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Employee history
# ---------------------------------------------------------------------------

class TestEmployeeHistoryAPI:
    @staticmethod
    def _hist(employee):
        return AccessHistory.objects.create(
            employee=employee,
            access_point='main',
            result='allowed',
            method='biometric',
        )

    def test_admin_can_view(self, admin_client, employee):
        self._hist(employee)
        r = admin_client.get(f'/api/employees/{employee.id}/history/')
        assert r.status_code == 200
        assert len(r.data) >= 1

    def test_employee_can_view_self(self, employee_client, employee):
        self._hist(employee)
        r = employee_client.get(f'/api/employees/{employee.id}/history/')
        assert r.status_code == 200

    def test_employee_cannot_view_others(self, employee_client):
        other = User.objects.create_user(username='other_c', password='pass')
        other_emp = Employee.objects.create(
            user=other, last_name='Другой', first_name='В',
            hire_date=date(2023, 1, 1)
        )
        r = employee_client.get(f'/api/employees/{other_emp.id}/history/')
        assert r.status_code == 403

    def test_response_fields(self, admin_client, employee):
        self._hist(employee)
        r = admin_client.get(f'/api/employees/{employee.id}/history/')
        assert r.status_code == 200
        first = r.data[0]
        assert 'datetime' in first
        assert 'access_point' in first
        assert 'result' in first
        assert 'method' in first


# ---------------------------------------------------------------------------
# Biometric status
# ---------------------------------------------------------------------------

class TestBiometricStatusAPI:
    def test_not_registered(self, admin_client, employee):
        r = admin_client.get(f'/api/biometric/{employee.id}/status/')
        assert r.status_code == 200
        assert r.data['registered'] is False
        assert r.data['registered_at'] is None

    def test_registered(self, admin_client, employee):
        BiometricData.objects.create(
            employee=employee,
            palm_hash='fakehash',
            palm_registered_at=date(2024, 6, 1),
            status=True,
        )
        r = admin_client.get(f'/api/biometric/{employee.id}/status/')
        assert r.status_code == 200
        assert r.data['registered'] is True
        assert r.data['registered_at'] == '2024-06-01'

    def test_employee_can_view_self(self, employee_client, employee):
        r = employee_client.get(f'/api/biometric/{employee.id}/status/')
        assert r.status_code == 200

    def test_employee_cannot_view_others(self, employee_client):
        other = User.objects.create_user(username='other_d', password='pass')
        other_emp = Employee.objects.create(
            user=other, last_name='Другой', first_name='Г',
            hire_date=date(2023, 1, 1)
        )
        r = employee_client.get(f'/api/biometric/{other_emp.id}/status/')
        assert r.status_code == 403

    def test_not_found(self, admin_client):
        r = admin_client.get('/api/biometric/99999/status/')
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Positions and departments
# ---------------------------------------------------------------------------

class TestPositionDepartmentAPI:
    def test_positions_list(self, admin_client):
        r = admin_client.get('/api/positions/')
        assert r.status_code == 200
        assert isinstance(r.data, list)

    def test_departments_list(self, admin_client):
        r = admin_client.get('/api/departments/')
        assert r.status_code == 200
        assert isinstance(r.data, list)

    def test_unauthenticated_positions(self, api_client):
        r = api_client.get('/api/positions/')
        assert r.status_code == 403

    def test_unauthenticated_departments(self, api_client):
        r = api_client.get('/api/departments/')
        assert r.status_code == 403
