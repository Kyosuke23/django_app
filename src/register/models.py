from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.contrib.auth.validators import ASCIIUsernameValidator
from .const import GENDER_CHOICES, PRIVILEGE_CHOICES

class CustomUser(AbstractUser):
    """
    独自ユーザーモデル
    """
    # バリデーション定義
    USERNAME_VALID = ASCIIUsernameValidator()
    TEL_NUM_VALID = RegexValidator(regex=r'^[0-9]+$', message=('半角数字のみで入力してください'))
    POSTAL_CD_VALID = RegexValidator(regex=r'^[0-9]+$', message=('半角数字7桁で入力してください'))
    # 既存カラムの上書き
    username = models.CharField(
        validators = [USERNAME_VALID]
        , max_length=50
        , unique=True
        , null=False
        , blank=False
        , error_messages={
            'unique': 'このユーザーコードは既に使用されています。',
        }
        , verbose_name='ユーザーコード'
    )
    # 追加フィールド
    gender = models.CharField(null=True, blank=True, max_length=1, choices=GENDER_CHOICES, verbose_name='性別')
    tel_number = models.CharField(validators=[TEL_NUM_VALID], max_length=15, blank=True, null=True, verbose_name='電話番号')
    postal_cd = models.CharField(validators=[POSTAL_CD_VALID], max_length=7, blank=True, null=True, verbose_name='郵便番号')
    state = models.CharField(max_length=5, blank=True, null=True, verbose_name='都道府県')
    city = models.CharField(max_length=255, blank=True, null=True, verbose_name='市区町村')
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name='住所')
    address2 = models.CharField(max_length=255, blank=True, null=True, verbose_name='住所2')
    birthday = models.DateField(null=True, blank=True, verbose_name='誕生日')
    privilege = models.CharField(max_length=1, choices=PRIVILEGE_CHOICES, default='3', verbose_name='権限')

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('register:register_user_index', kwargs={'pk': self.pk})