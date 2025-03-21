# Generated by Django 4.1 on 2024-12-26 12:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('demo_app', '0002_rename_categorymst_category_rename_itemmst_item'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='created_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sample_category_creater', to=settings.AUTH_USER_MODEL, verbose_name='作成者'),
        ),
        migrations.AlterField(
            model_name='category',
            name='updated_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sample_category_updater', to=settings.AUTH_USER_MODEL, verbose_name='更新者'),
        ),
        migrations.AlterField(
            model_name='item',
            name='created_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sample_item_creater', to=settings.AUTH_USER_MODEL, verbose_name='作成者'),
        ),
        migrations.AlterField(
            model_name='item',
            name='updated_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sample_item_updater', to=settings.AUTH_USER_MODEL, verbose_name='更新者'),
        ),
    ]
