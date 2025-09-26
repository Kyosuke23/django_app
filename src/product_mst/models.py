from django.db import models
from config.base import BaseModel
from django.urls import reverse
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


class Product(BaseModel):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product_cd', 'start_date', 'end_date', 'tenant'],
                name='uq_product_cd_period'
            )
        ]
        ordering = ['product_cd', 'start_date']

    product_cd = models.CharField(
        max_length=255,
        validators=[RegexValidator(
            r'^[0-9A-Za-z_-]+$',
            '半角英数字・ハイフン・アンダースコアのみ使用できます。'
        )],
        verbose_name='商品コード'
    )
    product_nm = models.CharField(max_length=255, verbose_name='商品名称')
    start_date = models.DateField(verbose_name='適用開始日')
    end_date = models.DateField(verbose_name='適用終了日')
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
        return f'{self.product_nm}({self.product_cd})'

    def get_absolute_url(self):
        return reverse('product_mst:product_update', kwargs={'pk': self.pk})

    def clean(self):
        """
        バリデーション:
        ・適用終了日 < 適用開始日ならエラー
        """
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': '適用終了日は適用開始日以降の日付を指定してください。'})

    def save(self, *args, **kwargs):
        # save の前に clean を呼んでバリデーション
        self.full_clean()
        super().save(*args, **kwargs)

class ProductCategory(BaseModel):
    class Meta:
        ordering = ['product_category_nm']
        unique_together = ('tenant', 'product_category_nm')

    product_category_nm = models.CharField(max_length=255, unique=True, verbose_name='商品カテゴリ')

    def __str__(self):
        return self.product_category_nm
