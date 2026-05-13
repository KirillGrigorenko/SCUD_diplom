from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0005_alter_employeecard_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='accesshistory',
            name='camera_source',
            field=models.CharField(
                blank=True,
                choices=[('laptop', 'Ноутбук'), ('external', 'Камера УК')],
                max_length=20,
                null=True,
                verbose_name='Источник камеры',
            ),
        ),
        migrations.AddField(
            model_name='accesshistory',
            name='confidence',
            field=models.IntegerField(
                blank=True,
                null=True,
                verbose_name='Уверенность ИИ (%)',
            ),
        ),
        migrations.AlterField(
            model_name='accesshistory',
            name='result',
            field=models.CharField(
                choices=[
                    ('allowed', 'Разрешён'),
                    ('denied', 'Запрещён'),
                    ('warning', 'Предупреждение'),
                ],
                max_length=20,
                verbose_name='Результат',
            ),
        ),
    ]
