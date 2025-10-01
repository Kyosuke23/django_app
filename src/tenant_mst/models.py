import uuid
from django.conf import settings
from django.db import models
from django.urls import reverse

class Tenant(models.Model):
    """
    企業・組織情報を管理するモデル
    """
    class Meta:
        ordering = ['tenant_code']

    tenant_code = models.UUIDField(
        default=uuid.uuid4,
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
    postal_code = models.CharField(
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
    
    # Tenantモデルだけは共通クラスの継承をしない
    is_deleted = models.BooleanField(default=False, verbose_name='削除フラグ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    create_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_creator",
        verbose_name='作成者'
    )
    update_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_updater",
        verbose_name='更新者'
    )

    def __str__(self):
        return f'{self.tenant_name} ({self.tenant_code})'

    def get_absolute_url(self):
        return reverse('tenant_mst:edit', kwargs={'pk': self.pk})