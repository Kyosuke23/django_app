import uuid
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.core.validators import RegexValidator

class Tenant(models.Model):
    '''
    企業・組織情報を管理するモデル
    '''
    class Meta:
        ordering = ['tenant_code']

    tenant_code = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='テナントコード'
    )

    tenant_name = models.CharField(
        max_length=100,
        verbose_name='テナント名称',
        help_text='企業名や団体名'
    )

    representative_name = models.CharField(
        max_length=100,
        verbose_name='代表者名',
        help_text='企業や団体の代表者名'
    )

    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='メールアドレス',
        error_messages={
            'unique': '同じメールアドレスが既に登録されています。',
            'invalid': '有効なメールアドレスを入力してください。',
        }
    )

    tel_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^[0-9\-]+$', '数字とハイフンのみ使用できます。')],
        blank=True,
        null=True,
        verbose_name='電話番号',
        help_text='半角数字とハイフンのみ使用できます。例：090-1234-5678（任意）'
    )

    postal_code = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^[0-9\-]+$', '郵便番号の形式が正しくありません。')],
        blank=True,
        null=True,
        verbose_name='郵便番号',
        help_text='ハイフンあり、またはなしで入力可能です。例：123-4567（任意）'
    )

    state = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='都道府県',
        help_text='都道府県名を10文字以内で入力してください。（任意）'
    )

    city = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='市区町村',
        help_text='市区町村名を50文字以内で入力してください。（任意）'
    )

    address = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='住所',
        help_text='番地などを100文字以内で入力してください。（任意）'
    )

    address2 = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='住所2',
        help_text='建物名・部屋番号などを150文字以内で入力してください。（任意）'
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