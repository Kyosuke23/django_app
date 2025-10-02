from django.db import models
from config.base import BaseModel
from django.urls import reverse


class Product(BaseModel):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product_name', 'tenant'],
                name='uq_product_name_period'
            )
        ]
        ordering = ['product_name']

    product_name = models.CharField(max_length=255, verbose_name='商品名称')
    product_category = models.ForeignKey(
        'ProductCategory',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='商品カテゴリ'
    )
    price = models.IntegerField(blank=True, null=True, verbose_name='価格')
    description = models.TextField(blank=True, null=True, verbose_name='商品説明')

    def __str__(self):
        return f'{self.product_name}'

    def get_absolute_url(self):
        return reverse('product_mst:product_update', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        # save の前に clean を呼んでバリデーション
        self.full_clean()
        super().save(*args, **kwargs)

class ProductCategory(BaseModel):
    class Meta:
        ordering = ['product_category_name']
        unique_together = ('tenant', 'product_category_name')

    product_category_name = models.CharField(max_length=255, unique=True, verbose_name='商品カテゴリ')

    def __str__(self):
        return self.product_category_name