from django.db import models
from config.base import BaseModel
from config.common import Common

class Partner(BaseModel):
    '''
    取引先マスタ
    - 顧客・仕入先などを管理
    '''
    PARTNER_TYPE_CHOICES = [
        ('customer', '顧客'),
        ('supplier', '仕入先'),
        ('both', '両方'),
    ]

    partner_name = models.CharField(
        max_length=255,
        verbose_name='取引先名称'
    )

    partner_name_kana = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='取引先名称（カナ）'
    )

    partner_type = models.CharField(
        max_length=20,
        choices=PARTNER_TYPE_CHOICES,
        default='customer',
        verbose_name='取引先区分'
    )

    contact_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='担当者名')
    tel_number = models.CharField(max_length=15, validators=[Common.numeric_validator], blank=True, null=True, verbose_name='電話番号')

    email = models.EmailField(
        verbose_name='メールアドレス',
        error_messages={
            'invalid': 'メールアドレスの形式が正しくありません。',
            'unique': 'このメールアドレスは既に登録されています。',
            'blank': 'メールアドレスを入力してください。',
            'null': 'メールアドレスを入力してください。',
        }
    )

    postal_code = models.CharField(max_length=7, validators=[Common.numeric_validator], blank=True, null=True, verbose_name='郵便番号')
    state = models.CharField(max_length=5, blank=True, null=True, verbose_name='都道府県')
    city = models.CharField(max_length=255, blank=True, null=True, verbose_name='市区町村')
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name='住所')
    address2 = models.CharField(max_length=255, blank=True, null=True, verbose_name='住所2')

    class Meta:
        ordering = ['partner_name']
        unique_together = ('tenant', 'partner_name', 'email')

    def __str__(self):
        return f'{self.partner_name}'
