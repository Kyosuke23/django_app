# Generated by Django 4.1 on 2024-12-25 06:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0008_customuser_address2_customuser_city_customuser_state_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='state',
            field=models.CharField(blank=True, choices=[('0', '東京'), ('1', '大阪'), ('2', '福岡')], max_length=1, null=True, verbose_name='都道府県'),
        ),
    ]
