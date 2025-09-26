import uuid
from django.db import models
from config.base import BaseModel

class Tenant(BaseModel):
    """
    企業・組織情報を管理するモデル
    （CustomUser が所属する単位）
    """
    class Meta:
        ordering = ['tenant_cd']

    tenant_cd = models.UUIDField(
        default=uuid.uuid4,   # 新規作成時に自動でUUIDを生成
        unique=True,
        editable=False,
        verbose_name='テナントコード'
    )
    tenant_name = models.CharField(
        max_length=255,
        verbose_name='テナント名',
        help_text='企業名や団体名'
    )
    representative_name = models.CharField(
        max_length=255,
        verbose_name='代表者名',
        help_text='企業や団体の代表者名'
    )
    contact_email = models.EmailField(
        verbose_name='代表メールアドレス'
    )
    tel_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='代表電話番号'
    )
    postal_cd = models.CharField(
        max_length=7,
        blank=True,
        null=True,
        verbose_name='郵便番号'
    )
    state = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        verbose_name='都道府県'
    )
    city = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='市区町村'
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='住所'
    )
    address2 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='住所2'
    )

    def __str__(self):
        return f'{self.tenant_name} ({self.tenant_cd})'
