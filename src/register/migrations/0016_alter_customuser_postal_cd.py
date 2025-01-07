# Generated by Django 4.1 on 2024-12-26 22:30

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0015_alter_customuser_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='postal_cd',
            field=models.CharField(blank=True, max_length=8, validators=[django.core.validators.RegexValidator(message='xxx-xxxx形式で入力してください', regex='/^[0-9]{3}-[0-9]{4}$/')], verbose_name='郵便番号'),
        ),
    ]
