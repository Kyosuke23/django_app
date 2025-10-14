from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from .constants import GENDER_CHOICES, PRIVILEGE_CHOICES
from config.base import BaseModel
import register.constants as Constant

class CustomUser(AbstractUser, BaseModel):
    '''
    独自ユーザーモデル
    '''
    USERNAME_FIELD = 'email'  # ← 認証に使うフィールドを email に変更
    REQUIRED_FIELDS = ['username']  # ← createsuperuser のとき追加で入力させるフィールド
    TEL_NUM_VALID = RegexValidator(regex=r'^[0-9]+$', message=('半角数字のみで入力してください'))
    postal_code_VALID = RegexValidator(regex=r'^\d{7}$', message=('半角数字7桁で入力してください'))
    
    username = models.CharField(
        max_length=50
        , unique=False
        , null=False
        , blank=False
        , verbose_name='ユーザー名'
    )
    username_kana = models.CharField(
        max_length=100
        , unique=False
        , null=True
        , blank=True
        , verbose_name='ユーザー名（カナ）'
    )
    email = models.EmailField(
        unique=True,
        null=False,
        blank=False,
        verbose_name='メールアドレス'
    )
    gender = models.CharField(null=True, blank=True, max_length=1, choices=GENDER_CHOICES, verbose_name='性別')
    tel_number = models.CharField(validators=[TEL_NUM_VALID], max_length=15, blank=True, null=True, verbose_name='電話番号')
    postal_code = models.CharField(validators=[postal_code_VALID], max_length=7, blank=True, null=True, verbose_name='郵便番号')
    state = models.CharField(max_length=5, blank=True, null=True, verbose_name='都道府県')
    city = models.CharField(max_length=255, blank=True, null=True, verbose_name='市区町村')
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name='住所')
    address2 = models.CharField(max_length=255, blank=True, null=True, verbose_name='住所2')
    birthday = models.DateField(null=True, blank=True, verbose_name='誕生日')
    employment_status = models.CharField(
        max_length=1,
        choices=Constant.EMPLOYMENT_STATUS_CHOICES,
        default='1',
        verbose_name='雇用状態'
    )
    employment_end_date = models.DateField(null=True, blank=True, verbose_name='退職日')
    privilege = models.CharField(max_length=3, choices=PRIVILEGE_CHOICES, default='3', verbose_name='権限')

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('register:list', kwargs={'pk': self.pk})
      
    @property
    def is_employed(self):
        return self.employment_status == '1' and (self.employment_end_date is None)