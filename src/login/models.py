from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from config.common import Common
import re

# ip アドレスのバリデーション用
pattern = '([0-9]{3}\.){3}\.[0-9]{3}'
matcher = re.compile(pattern)

def validate_ip(value):
    if not matcher.match(value):
        raise ValidationError(
            _('%{value} is not valid ip!'),
            params={'value', value}
        )

class AccessLog(models.Model):
    '''
    アクセス履歴
    '''
    class Meta:
        app_label = 'login'
        ordering = ['access_at', 'username']

    # データの設定
    username = models.CharField(max_length=50, verbose_name='ユーザーコード')
    ip=models.CharField(max_length=255, validators=[validate_ip], verbose_name='IPアドレス')
    access_type = models.CharField(max_length=50, verbose_name='アクセス種別')
    access_at=models.DateTimeField(auto_now=True, verbose_name='アクセス日時')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    created_user = models.ForeignKey(get_user_model(), to_field='id', on_delete=models.SET_NULL, null=True, related_name='accesslog_creater', verbose_name='作成者')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    updated_user = models.ForeignKey(get_user_model(), to_field='id', on_delete=models.SET_NULL, null=True, related_name='accesslog_updater', verbose_name='更新者')

    def __str__(self) -> str:
        return 'ip : %s / access at : %s' % (self.ip,self.access_at)

@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    '''
    ログイン時の履歴登録
    '''
    # ユーザー情報を取得
    username = request.POST.get('username')
    ip = Common.get_ip_address(request)

    # DBへ登録
    AccessLog.objects.create(
        username=username
        , ip=ip
        , access_type = 'login'
        , created_user = user
        , updated_user =  user
    )

@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    '''
    ログアウト時の履歴登録
    '''
    # ユーザー情報を取得
    username = user.username
    ip = Common.get_ip_address(request)

    # DBへ登録
    AccessLog.objects.create(
        username=username
        , ip=ip
        , access_type = 'logout'
        , created_user = user
        , updated_user =  user
    )