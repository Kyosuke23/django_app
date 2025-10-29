from django.db import models
from config.base import BaseModel
from django.urls import reverse
from django.core.exceptions import ValidationError

class Product(BaseModel):
    '''
    商品マスタ
    - 各商品情報を管理
    '''
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

    product_name = models.CharField(
        max_length=100,
        verbose_name='商品名称',
        help_text='100文字以内で入力してください。重複登録はできません。'
    )

    product_category = models.ForeignKey(
        'ProductCategory',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='products',
        verbose_name='商品カテゴリ',
        help_text='商品のカテゴリを選択してください。（任意）'
    )

    unit = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='単位',
        help_text='数量に対する単位を20文字以内で入力してください。例：個、箱、kgなど'
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='単価',
        help_text='数値で入力してください。小数第2位まで指定できます。（任意）'
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='商品説明',
        help_text='商品の仕様や補足情報などを255文字以内で記入できます。（任意）'
    )

    def __str__(self):
        return f'{self.product_name}（{self.product_category}）'

    def clean(self):
        super().clean()
        if self.description and len(self.description) > 255:
            raise ValidationError({'description': 'この値は 255 文字以下でなければなりません( 256 文字になっています)。'})

    def get_absolute_url(self):
        return reverse('product_mst:update', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        # save の前に clean を呼んでバリデーション
        self.full_clean()
        super().save(*args, **kwargs)


class ProductCategory(BaseModel):
    '''
    商品カテゴリマスタ
    - 商品の分類情報を管理
    '''
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

    product_category_name = models.CharField(
        max_length=100,
        verbose_name='商品カテゴリ名称',
        help_text='100文字以内で入力してください。'
    )

    def __str__(self):
        return self.product_category_name
