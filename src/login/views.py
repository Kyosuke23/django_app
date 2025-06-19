from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.views import generic
from .models import AccessLog
from .const import *
from config.common import Common


class Login(LoginView):
    """
    ログイン処理
    """
    fields = '__all__'
    template_name = 'login/login.html'

    def get_success_url(self):
        return reverse_lazy('dashboard:top')

class Logout(LogoutView):
    """
    ログアウト処理
    """
    template_name = 'login/login.html'

class PasswordReset(PasswordResetView):
    """
    パスワードリセット画面表示
    """
    subject_template_name = 'mail/password_reset/password_reset_subject.txt'
    email_template_name = 'mail/password_reset/password_reset_email.txt'
    template_name = 'login/password_reset_form.html'
    success_url = reverse_lazy('login:password_reset_done')

class PasswordResetDone(PasswordResetDoneView):
    """
    パスワードリセットメール送信後の画面
    """
    template_name = 'login/password_reset_done.html'

class PasswordResetConfirm(PasswordResetConfirmView):
    """
    パスワード再設定画面
    （パスワードリセットURLを踏んだ直後の画面）
    """
    success_url = reverse_lazy('login:password_reset_complete')
    template_name = 'login/password_reset_confirm.html'

class PasswordResetComplete(PasswordResetCompleteView):
    """
    パスワード再設定の完了画面
    """
    template_name = 'login/password_reset_complete.html'

class AccessLogListView(generic.ListView):
    model = AccessLog
    context_object_name = 'access_logs'
    template_name = 'login/index.html'
    paginate_by = 50

    def get_queryset(self):
        # query setを取得
        query_set = super().get_queryset()
        # 検索条件を取得
        username = self.request.GET.get('search_username') or ''
        accesstype = self.request.GET.get('search_accesstype')
        accessat_from = self.request.GET.get('search_accessat_from')
        accessat_to = self.request.GET.get('search_accessat_to')
        # query setをフィルタ
        if username:
            query_set = query_set.filter(username__icontains=username)
        if accesstype:
            query_set = query_set.filter(access_type=accesstype)
        if accessat_from:
            query_set = query_set.filter(access_at__gte=accessat_from)
        if accessat_to:
            query_set = query_set.filter(access_at__lte=accessat_to)
        # query setを返却
        return query_set

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 検索フォーム設定
        context['search_username'] = self.request.GET.get('search_username') or ''
        context['search_accesstype'] = self.request.GET.get('search_accesstype')
        context['search_accessat_from'] = self.request.GET.get('search_accessat_from')
        context['search_accessat_to'] = self.request.GET.get('search_accessat_to')
        context['accesstype_list'] = ACCESSTYPE_CHOICES # アクセス種別リスト
        # ページネーション設定
        context = Common.set_pagination(context, self.request.GET.urlencode())
        # コンテキストを返却
        return context
    