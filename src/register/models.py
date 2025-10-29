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

    username = models.CharField(
        max_length=100,
        unique=False,
        null=False,
        blank=False,
        verbose_name='ユーザー名',
        help_text='100文字以内で入力してください。'
    )

    username_kana = models.CharField(
        max_length=100,
        unique=False,
        null=True,
        blank=True,
        verbose_name='ユーザー名（カナ）',
        help_text='カタカナ100文字以内で入力してください。（任意）'
    )

    email = models.EmailField(
        max_length=254,
        unique=True,
        null=False,
        blank=False,
        verbose_name='メールアドレス',
        help_text='半角英数字で正しいメール形式を入力してください。'
    )

    gender = models.CharField(
        null=True,
        blank=True,
        max_length=1,
        choices=GENDER_CHOICES,
        verbose_name='性別',
        help_text='該当する性別を選択してください。（任意）'
    )

    tel_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^[0-9\-]+$', '数字とハイフンのみ使用できます。')],
        blank=True,
        null=True,
        verbose_name='電話番号',
        help_text='数字とハイフンのみ使用できます。'
    )

    employment_status = models.CharField(
        max_length=1,
        choices=Constant.EMPLOYMENT_STATUS_CHOICES,
        default='1',
        verbose_name='雇用状態',
        help_text='現在の雇用状態を選択してください。'
    )

    privilege = models.CharField(
        max_length=3,
        choices=PRIVILEGE_CHOICES,
        default='3',
        verbose_name='権限',
        help_text='ユーザーの操作権限を選択してください。'
    )

    groups_custom = models.ManyToManyField(
        'UserGroup',
        related_name='users',
        blank=True,
        verbose_name='所属グループ',
        help_text='ユーザーが所属するグループを選択してください。（複数選択可）'
    )

    class Meta:
        verbose_name = 'ユーザー'
        verbose_name_plural = 'ユーザーマスタ'
        ordering = ['username']

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('register:list', kwargs={'pk': self.pk})

    @property
    def group_names_display(self):
        """所属グループ名をカンマ区切りで表示"""
        return ", ".join(self.groups_custom.values_list('group_name', flat=True))

class UserGroup(BaseModel):
    '''
    ユーザーグループマスタ
    '''
    group_name = models.CharField(
        max_length=100,
        unique=False,
        verbose_name='グループ名',
        help_text='100文字以内で入力してください。'
    )

    class Meta:
        verbose_name = 'ユーザーグループ'
        verbose_name_plural = 'ユーザーグループマスタ'
        ordering = ['group_name']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'group_name'], name='unique_tenant_groupname'
            ),
        ]

    def __str__(self):
        return self.group_name