from django.db import models

class SalesOrderStatus(models.TextChoices):
    DRAFT = "DRAFT", "作成中"
    SUBMITTED = "SUBMITTED", "社内承認待ち"
    APPROVED_IN = "APPROVED_IN", "社内承認済"
    REJECTED_IN = "REJECTED_IN", "社内却下"
    APPROVED_OUT = "APPROVED_OUT", "顧客承諾"
    REJECTED_OUT = "REJECTED_OUT", "顧客却下"
    READY_SHIP = "READY_SHIP", "出荷待ち"
    SHIPPED = "SHIPPED", "出荷済"
    BILLED = "BILLED", "請求済"
    PAID = "PAID", "入金済"
    CANCEL = "CANCEL", "キャンセル"
