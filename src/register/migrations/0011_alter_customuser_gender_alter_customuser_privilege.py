# Generated by Django 4.1 on 2024-12-25 09:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0010_alter_customuser_address_alter_customuser_address2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='gender',
            field=models.CharField(choices=[('0', '男性'), ('1', '女性'), ('2', 'その他')], default='0', max_length=1, verbose_name='性別'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='privilege',
            field=models.CharField(choices=[('0', '特権'), ('1', '一般'), ('2', '参照')], default='2', max_length=1, verbose_name='権限'),
        ),
    ]