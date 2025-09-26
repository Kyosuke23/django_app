from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from config.base import BaseModel
from config.common import Common
import re

# ip アドレスのバリデーション用
pattern = '([0-9]{3}\.){3}\.[0-9]{3}'
matcher = re.compile(pattern)

def validate_ip(value):
    if not matcher.match(value):
        raise ValidationError(
            ('%{value} is not valid ip!'),
            params={'value', value}
        )

class AccessLog(BaseModel):
    """
    アクセス履歴
    - BaseModel 継承により tenant / 作成者 / 更新者 / 作成日時 / 更新日時 を統一
    """
    class Meta:
        app_label = 'login'
        ordering = ['access_at', 'username']

    username = models.CharField(max_length=50, verbose_name='ユーザーコード')
    ip=models.CharField(max_length=255, validators=[validate_ip], verbose_name='IPアドレス')
    access_type = models.CharField(max_length=50, verbose_name='アクセス種別')
    access_at = models.DateTimeField(auto_now=True, verbose_name='アクセス日時')

    def __str__(self):
        return f'ip : {self.ip} / access at : {self.access_at}'


@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    """
    ログイン時の履歴登録
    """
    ip = Common.get_ip_address(request) or '0.0.0.0'
    AccessLog.objects.create(
        tenant=user.tenant,
        username=user.get_username(),
        ip=ip,
        access_type='login',
        create_user=user,
        update_user=user,
    )


@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    """
    ログアウト時の履歴登録
    """
    ip = Common.get_ip_address(request) or '0.0.0.0'
    AccessLog.objects.create(
        tenant=user.tenant,
        username=user.username,
        ip=ip,
        access_type='logout',
        create_user=user,
        update_user=user,
    )
