# Generated by Django 4.1 on 2024-12-25 04:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0005_alter_customuser_birthday_alter_customuser_gender_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='birthday',
            field=models.DateField(blank=True, null=True, verbose_name='誕生日'),
        ),
    ]
