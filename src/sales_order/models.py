from django.db import models
from config.base import BaseModel
from django.utils import timezone


class SalesOrder(BaseModel):
    """
    受注ヘッダ（1つの受注伝票）
    """
    order_no = models.CharField(max_length=20, unique=True, verbose_name="受注番号")
    order_date = models.DateField(default=timezone.now, verbose_name="受注日")
    partner = models.ForeignKey(
        "partner_mst.Partner",
        on_delete=models.PROTECT,
        verbose_name="取引先"
    )
    remarks = models.TextField(blank=True, null=True, verbose_name="備考")
    total_amount = models.IntegerField(default=0, verbose_name="受注合計金額")

    class Meta:
        db_table = "sales_order"
        verbose_name = "受注ヘッダ"
        verbose_name_plural = "受注ヘッダ"

    def __str__(self):
        return f"{self.order_no} ({self.partner.partner_name})"

class SalesOrderDetail(BaseModel):
    """
    受注明細（受注ヘッダにぶら下がる商品単位の情報）
    """
    ROUNDING_CHOICES = [
        ("floor", "切り捨て"),
        ("ceil", "切り上げ"),
        ("round", "四捨五入"),
    ]

    sales_order = models.ForeignKey(
        SalesOrder,
        related_name="details",
        on_delete=models.CASCADE,
        verbose_name="受注ヘッダ"
    )
    line_no = models.IntegerField(verbose_name="行番号")
    product = models.ForeignKey(
        "product_mst.Product",
        on_delete=models.PROTECT,
        verbose_name="商品"
    )
    quantity = models.IntegerField(verbose_name="数量")
    unit = models.CharField(max_length=20, verbose_name="単位")  # 数量に対する単位
    unit_price = models.IntegerField(verbose_name="単価")
    amount = models.IntegerField(verbose_name="金額")
    is_tax_exempt = models.BooleanField(default=False, verbose_name="消費税対象外")  
    tax_rate = models.DecimalField(  # ★ 消費税率（例: 0.1 = 10%）
        max_digits=3, decimal_places=2, default=0.10, verbose_name="消費税率"
    )
    rounding_method = models.CharField(  # ★ 小数点以下の丸め方
        max_length=10,
        choices=ROUNDING_CHOICES,
        default="floor",
        verbose_name="丸め方法"
    )

    class Meta:
        db_table = "sales_order_detail"
        verbose_name = "受注明細"
        verbose_name_plural = "受注明細"
        unique_together = ("sales_order", "line_no")

    def __str__(self):
        return f"{self.sales_order.order_no} - {self.line_no}: {self.product.product_nm}"
