from django.db import models
from config.base import BaseModel
from django.utils import timezone
from django.db.models import Max
from django.utils import timezone
from django.db.models import Max
from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING, ROUND_HALF_UP
from .constants import STATUS_CHOICES
from django.contrib.auth import get_user_model
from register.models import UserGroup

User = get_user_model()

def generate_sales_order_no(tenant):
    year = timezone.now().strftime('%Y')
    prefix = f'SO-{year}-'

    # 同一テナント＆同じ年の最大番号を取得
    last_order = (
        SalesOrder.objects
        .filter(tenant=tenant, sales_order_no__startswith=prefix)
        .aggregate(max_no=Max('sales_order_no'))
    )

    if last_order['max_no']:
        # 既存の最大番号を取り出して +1
        last_seq = int(last_order['max_no'].replace(prefix, ''))
        new_seq = last_seq + 1
    else:
        new_seq = 1

    # 桁数は柔軟に、ゼロパディングは任意（例では6桁）
    return f'{prefix}{new_seq:06d}'

class SalesOrder(BaseModel):
    '''
    受注ヘッダ
    '''
    ROUNDING_CHOICES = [
        ('floor', '切り捨て'),
        ('ceil', '切り上げ'),
        ('round', '四捨五入'),
    ]

    sales_order_no = models.CharField(
        max_length=20,
        verbose_name='受注番号',
    )

    status_code = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='DRAFT',
        verbose_name='ステータス',
    )

    sales_order_date = models.DateField(
        default=timezone.now,
        verbose_name='受注日',
        help_text='受注日を指定してください。'
    )
    
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_sales_orders',
        verbose_name='担当者',
        help_text='この受注を担当する社内ユーザーを選択してください。（任意）'
    )

    delivery_due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='納入予定日',
        help_text='納入予定日を指定してください。（任意）'
    )

    delivery_place = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='納入場所',
        help_text='納入先の住所や場所名を100文字以内で入力してください。（任意）'
    )

    partner = models.ForeignKey(
        'partner_mst.Partner',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='取引先',
    )

    remarks = models.TextField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='備考',
        help_text='特記事項や注意点を100文字以内で入力してください。（任意）'
    )

    quotation_manager_comment = models.TextField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='見積書_承認者コメント',
        help_text='社内承認者が見積書に対して残すコメント（任意）'
    )

    quotation_customer_comment = models.TextField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='見積書_顧客コメント',
        help_text='顧客からの見積書へのコメント（任意）'
    )

    order_manager_comment = models.TextField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='注文書_承認者コメント',
        help_text='社内承認者が注文書に対して残すコメント（任意）'
    )

    order_customer_comment = models.TextField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='注文書_顧客コメント',
        help_text='顧客からの注文書へのコメント（任意）'
    )

    rounding_method = models.CharField(
        max_length=10,
        choices=ROUNDING_CHOICES,
        default='floor',
        verbose_name='丸め方法',
        help_text='明細金額の端数処理方法を選択してください。'
    )

    reference_users = models.ManyToManyField(
        User,
        related_name='referenced_sales_orders',
        blank=True,
        verbose_name='参照ユーザー',
        help_text='この受注を参照できる社内ユーザーを選択してください。（任意）'
    )

    reference_groups = models.ManyToManyField(
        UserGroup,
        related_name='referenced_sales_orders',
        blank=True,
        verbose_name='参照グループ',
        help_text='この受注を参照できるユーザーグループを選択してください。（任意）'
    )

    class Meta:
        db_table = 'sales_order'
        verbose_name = '受注ヘッダ'
        verbose_name_plural = '受注ヘッダ'
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'sales_order_no'], name='unique_sales_order_per_tenant')
        ]

    def save(self, *args, **kwargs):
        if not self.sales_order_no:
            self.sales_order_no = generate_sales_order_no(self.tenant)
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        if not self.pk:
            return 0
        return sum([(d.quantity or 0) * (d.billing_unit_price or 0) for d in self.details.all()])

    @property
    def tax_total(self):
        if not self.pk:
            return 0
        return sum([0 if d.is_tax_exempt else (d.quantity or 0) * (d.billing_unit_price or 0) * float(d.tax_rate) for d in self.details.all()])

    @property
    def grand_total(self):
        if not self.pk:
            return 0
        return self.subtotal + self.tax_total

class SalesOrderDetail(BaseModel):
    '''
    受注明細（受注ヘッダにぶら下がる商品単位の情報）
    '''
    TAX_RATE_CHOICES = [
        (Decimal('0.10'), '10%'),
        (Decimal('0.08'), '8%'),
    ]
    sales_order = models.ForeignKey(
        SalesOrder,
        related_name='details',
        on_delete=models.CASCADE,
        verbose_name='受注ヘッダ'
    )
    line_no = models.IntegerField(verbose_name='行番号')
    product = models.ForeignKey(
        'product_mst.Product',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='商品'
    )
    quantity = models.IntegerField(verbose_name='数量')
    master_unit_price = models.IntegerField(verbose_name='マスタ単価')  # 商品マスタの単価コピー
    billing_unit_price = models.IntegerField(verbose_name='請求単価')  # 受注明細フォームで入力した単価
    tax_rate = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        choices=TAX_RATE_CHOICES,
        default=Decimal('0.10'),
        verbose_name='消費税率'
    )
    is_tax_exempt = models.BooleanField(default=False, verbose_name='消費税対象外')

    class Meta:
        db_table = 'sales_order_detail'
        verbose_name = '受注明細'
        verbose_name_plural = '受注明細'
        unique_together = ('sales_order', 'line_no')

    def __str__(self):
        return f'{self.sales_order.sales_order_no} - {self.line_no}: {self.product.product_name}'
    
    @property
    def amount(self):
        # 商品のない行は処理しない
        if not self.product:
            return ''

        # 数量 * 単価
        base = Decimal(self.quantity or 0) * Decimal(self.billing_unit_price or 0)

        # 消費税率を加味
        if not self.is_tax_exempt:
            base = base * (1 + self.tax_rate)

        # 小数点以下の処理を実施
        if self.sales_order.rounding_method == 'floor':
            value = base.to_integral_value(rounding=ROUND_FLOOR)
        elif self.sales_order.rounding_method == 'ceil':
            value = base.to_integral_value(rounding=ROUND_CEILING)
        else:
            value = base.to_integral_value(rounding=ROUND_HALF_UP)

        # 整数値にして返却
        return f'¥{int(value):,}'

class ApprovalToken(models.Model):
    token = models.CharField(max_length=255, unique=True)
    sales_order = models.ForeignKey('sales_order.SalesOrder', on_delete=models.CASCADE)
    partner_email = models.EmailField()
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def mark_used(self):
        self.used = True
        self.used_at = timezone.now()
        self.save(update_fields=['used', 'used_at'])