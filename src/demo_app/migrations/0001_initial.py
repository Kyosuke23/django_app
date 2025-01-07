# Generated by Django 4.1 on 2024-12-26 07:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryMst',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=255, verbose_name='カテゴリ')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='削除フラグ')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日時')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
                ('created_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sample_categorymst_creater', to=settings.AUTH_USER_MODEL, verbose_name='作成者')),
                ('updated_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sample_categorymst_updater', to=settings.AUTH_USER_MODEL, verbose_name='更新者')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='ItemMst',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_cd', models.CharField(max_length=255, unique=True, verbose_name='アイテムコード')),
                ('item_nm', models.CharField(max_length=255, verbose_name='アイテム名称')),
                ('description', models.TextField(blank=True, null=True, verbose_name='説明')),
                ('price', models.IntegerField(blank=True, null=True, verbose_name='価格')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='削除フラグ')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日時')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='demo_app.categorymst', verbose_name='カテゴリ')),
                ('created_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sample_itemmst_creater', to=settings.AUTH_USER_MODEL, verbose_name='作成者')),
                ('updated_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sample_itemmst_updater', to=settings.AUTH_USER_MODEL, verbose_name='更新者')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]
