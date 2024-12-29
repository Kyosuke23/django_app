from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.validators import ASCIIUsernameValidator

class Item(models.Model):
    """
    アイテム（Demo App用）
    """
    class Meta:
        app_label = 'demo_app'
        ordering = ['id']

    item_cd = models.CharField(max_length=255, unique=True, validators=[ASCIIUsernameValidator()],  verbose_name='アイテムコード')
    item_nm = models.CharField(max_length=255, verbose_name='アイテム名称')
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='カテゴリ')
    description = models.TextField(blank=True, null=True, verbose_name='説明')
    price = models.IntegerField(blank=True, null=True, verbose_name='価格')
    is_deleted = models.BooleanField(default=False, verbose_name='削除フラグ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    created_user = models.ForeignKey(get_user_model(), to_field='id', on_delete=models.SET_NULL, null=True, related_name='sample_item_creater', verbose_name='作成者')
    updated_user = models.ForeignKey(get_user_model(), to_field='id', on_delete=models.SET_NULL, null=True, related_name='sample_item_updater', verbose_name='更新者')

    def __str__(self):
        return f'{self.item_nm}({self.item_cd})'

    def get_absolute_url(self):
        return reverse('demo_app:item_mst_update', kwargs={'pk': self.pk})
    
class Category(models.Model):
    """
    カテゴリ（Demo App用）
    """
    class Meta:
        app_label = 'demo_app'
        ordering = ['id']

    category = models.CharField(max_length=255, verbose_name='カテゴリ')
    is_deleted = models.BooleanField(default=False, verbose_name='削除フラグ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    created_user = models.ForeignKey(get_user_model(), to_field='id', on_delete=models.SET_NULL, null=True, related_name='sample_category_creater', verbose_name='作成者')
    updated_user = models.ForeignKey(get_user_model(), to_field='id', on_delete=models.SET_NULL, null=True, related_name='sample_category_updater', verbose_name='更新者')

    def __str__(self):
        return self.category

    def get_absolute_url(self):
        return reverse('demo_app:item_mst_update', kwargs={'pk': self.pk})