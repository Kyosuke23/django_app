from django.db import models
from config.base import BaseModel
from config.common import Common
from django.core.validators import RegexValidator

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
        max_length=100,
        verbose_name='取引先名称'
    )

    partner_name_kana = models.CharField(
        max_length=100,
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

    contact_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='担当者名')
    
    tel_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^[0-9\-]+$', '数字とハイフンのみ使用できます。')],
        blank=True,
        null=True,
        verbose_name='電話番号'
    )

    email = models.EmailField(
        verbose_name='メールアドレス',
        unique=True,
        error_messages={
            'invalid': 'メールアドレスの形式が正しくありません。',
            'unique': 'このメールアドレスは既に登録されています。',
            'blank': 'メールアドレスを入力してください。',
            'null': 'メールアドレスを入力してください。',
        }
    )

    postal_code = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{3}-?\d{4}$', '郵便番号の形式が正しくありません。')],
        blank=True,
        null=True,
        verbose_name='郵便番号'
    )

    state = models.CharField(max_length=10, blank=True, null=True, verbose_name='都道府県')
    city = models.CharField(max_length=50, blank=True, null=True, verbose_name='市区町村')
    address = models.CharField(max_length=100, blank=True, null=True, verbose_name='住所')
    address2 = models.CharField(max_length=150, blank=True, null=True, verbose_name='住所2')

    class Meta:
        verbose_name = '取引先'
        verbose_name_plural = '取引先マスタ'
        ordering = ['partner_name']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'partner_name', 'email'],
                name='unique_tenant_partner_email'
            )
        ]

    def __str__(self):
        display_type = dict(self.PARTNER_TYPE_CHOICES).get(self.partner_type, '')
        return f'{self.partner_name}（{display_type}）'
