# Generated by Django 5.1.4 on 2025-01-06 09:51

import django.contrib.auth.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0019_alter_customuser_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='username',
            field=models.CharField(max_length=50, null=True, unique=True, validators=[django.contrib.auth.validators.ASCIIUsernameValidator()], verbose_name='ユーザーコード'),
        ),
    ]
