# Generated by Django 4.1 on 2024-12-24 00:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='gender',
            field=models.CharField(choices=[('0', 'MEALE'), ('1', 'FEMEALE'), ('2', 'OTHER')], default='0', max_length=1),
        ),
    ]
