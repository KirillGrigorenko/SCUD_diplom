from django.db import models
from django.contrib.auth.models import User


class Department(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название отдела')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'

    def __str__(self):
        return self.name


class Position(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название должности')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, verbose_name='Отдел')
    team_name = models.CharField(max_length=200, blank=True, verbose_name='Название команды')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'

    def __str__(self):
        return self.name


class AccessLevel(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название уровня')
    code = models.CharField(max_length=50, verbose_name='Код уровня')
    zone = models.CharField(max_length=200, verbose_name='Зона доступа')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Уровень доступа'
        verbose_name_plural = 'Уровни доступа'

    def __str__(self):
        return self.name


class Employee(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активен'),
        ('fired', 'Уволен'),
        ('blocked', 'Заблокирован'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    hire_date = models.DateField(verbose_name='Дата найма')
    fire_date = models.DateField(null=True, blank=True, verbose_name='Дата увольнения')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Статус')
    photo = models.CharField(max_length=200, blank=True, verbose_name='Ключ фото (MinIO)')

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

    def __str__(self):
        return f'{self.last_name} {self.first_name}'

    def full_name(self):
        return f'{self.last_name} {self.first_name} {self.middle_name}'


class Administrator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    hire_date = models.DateField(verbose_name='Дата найма')
    fire_date = models.DateField(null=True, blank=True, verbose_name='Дата увольнения')

    class Meta:
        verbose_name = 'Администратор'
        verbose_name_plural = 'Администраторы'

    def __str__(self):
        return f'{self.last_name} {self.first_name}'


class EmployeeCard(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, verbose_name='Сотрудник')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, verbose_name='Должность')
    administrator = models.ForeignKey(Administrator, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Администратор')
    passport_series = models.CharField(max_length=10, blank=True, verbose_name='Серия паспорта')
    passport_number = models.CharField(max_length=10, blank=True, verbose_name='Номер паспорта')
    passport_date = models.DateField(null=True, blank=True, verbose_name='Дата выдачи паспорта')
    passport_issued_by = models.CharField(max_length=300, blank=True, verbose_name='Кем выдан')
    citizenship = models.CharField(max_length=100, blank=True, verbose_name='Гражданство')
    address = models.TextField(blank=True, verbose_name='Адрес прописки')
    snils = models.CharField(max_length=20, blank=True, verbose_name='СНИЛС')
    inn = models.CharField(max_length=20, blank=True, verbose_name='ИНН')
    education_year = models.IntegerField(null=True, blank=True, verbose_name='Год окончания учебного заведения')
    specialty = models.CharField(max_length=200, blank=True, verbose_name='Специальность')
    education_name = models.CharField(max_length=200, blank=True, verbose_name='Название образования')
    diploma_number = models.CharField(max_length=100, blank=True, verbose_name='Номер диплома')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата удаления')

    class Meta:
        verbose_name = 'Карточка сотрудника'
        verbose_name_plural = 'Карточки сотрудников'

    def __str__(self):
        return f'Карточка — {self.employee}'


class BiometricData(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, verbose_name='Сотрудник')
    face_hash = models.CharField(max_length=500, blank=True, verbose_name='Hash лица')
    palm_hash = models.CharField(max_length=500, blank=True, verbose_name='Hash ладони')
    face_registered_at = models.DateField(null=True, blank=True, verbose_name='Дата регистрации hash лица')
    palm_registered_at = models.DateField(null=True, blank=True, verbose_name='Дата регистрации hash ладони')
    status = models.BooleanField(default=False, verbose_name='Статус биометрии')

    class Meta:
        verbose_name = 'Биометрические данные'
        verbose_name_plural = 'Биометрические данные'

    def __str__(self):
        return f'Биометрия — {self.employee}'


class AccessRight(models.Model):
    access_level = models.ForeignKey(AccessLevel, on_delete=models.CASCADE, verbose_name='Уровень доступа')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, verbose_name='Должность')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name='Сотрудник')
    assigned_at = models.DateField(verbose_name='Дата назначения')
    expires_at = models.DateField(null=True, blank=True, verbose_name='Дата окончания')

    class Meta:
        verbose_name = 'Право доступа'
        verbose_name_plural = 'Права доступа'

    def __str__(self):
        return f'{self.employee} — {self.access_level}'


class AccessHistory(models.Model):
    METHOD_CHOICES = [
        ('password', 'Пароль'),
        ('biometric', 'Биометрия'),
    ]
    RESULT_CHOICES = [
        ('allowed', 'Разрешён'),
        ('denied', 'Запрещён'),
        ('warning', 'Предупреждение'),
    ]
    CAMERA_CHOICES = [
        ('laptop', 'Ноутбук'),
        ('external', 'Камера УК'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name='Сотрудник')
    datetime = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время')
    access_point = models.CharField(max_length=200, verbose_name='Точка доступа')
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, verbose_name='Результат')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, verbose_name='Способ входа')
    camera_source = models.CharField(max_length=20, choices=CAMERA_CHOICES, null=True, blank=True, verbose_name='Источник камеры')
    confidence = models.IntegerField(null=True, blank=True, verbose_name='Уверенность ИИ (%)')

    class Meta:
        verbose_name = 'История проходов'
        verbose_name_plural = 'История проходов'
        ordering = ['-datetime']

    def __str__(self):
        return f'{self.employee} — {self.datetime}'