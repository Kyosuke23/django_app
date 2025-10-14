from django.db import models
from config.base import BaseModel
from django.urls import reverse


class Product(BaseModel):
    class Meta:
        verbose_name = '商品'
        verbose_name_plural = '商品マスタ'
        constraints = [
            models.UniqueConstraint(
                fields=['product_name', 'tenant'],
                name='uq_product_name_tenant'
            )
        ]
        ordering = ['product_name']

    product_name = models.CharField(max_length=255, verbose_name='商品名称')
    product_category = models.ForeignKey(
        'ProductCategory',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='products',
        verbose_name='商品カテゴリ'
    )
    unit = models.CharField(max_length=20, verbose_name='単位')  # 数量に対する単位
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        blank=True, null=True, verbose_name='単価'
    )
    description = models.TextField(blank=True, null=True, verbose_name='商品説明')

    def __str__(self):
        return f'{self.product_name}'

    def get_absolute_url(self):
        return reverse('product_mst:update', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        # save の前に clean を呼んでバリデーション
        self.full_clean()
        super().save(*args, **kwargs)

class ProductCategory(BaseModel):
    class Meta:
        verbose_name = '商品カテゴリ'
        verbose_name_plural = '商品カテゴリマスタ'
        ordering = ['product_category_name']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'product_category_name'],
                name='uq_tenant_product_category_name'
            )
        ]

    product_category_name = models.CharField(max_length=255,    verbose_name='商品カテゴリ')

    def __str__(self):
        return self.product_category_name