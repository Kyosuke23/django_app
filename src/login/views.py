from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.views import generic
from .models import AccessLog
from .const import *
from config.common import Common
from datetime import datetime


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
        actype = self.request.GET.get('search_accesstype')
        acat_from = self.request.GET.get('search_accessat_from')
        acat_to = self.request.GET.get('search_accessat_to')
        query_set = self.search_data(qs=query_set, username=username, actype=actype, acat_from=acat_from, acat_to=acat_to)
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
    
    def search_data(self, qs, username, actype, acat_from, acat_to):
        # query setをフィルタ
        if username:
            qs = qs.filter(username__icontains=username)
        if actype:
            qs = qs.filter(access_type=actype)
        if acat_from:
            qs = qs.filter(access_at__gte=acat_from)
        if acat_to:
            qs = qs.filter(access_at__lte=acat_to)
        # 結果を返却
        return qs

class ExportExcel(generic.TemplateView):
    def get(self, request, *args, **kwargs):
        # 出力ファイル名を設定
        file_name = f'access_log_{datetime.now().replace(microsecond=0)}.xlsx'
        # queryセットを取得
        query_set = AccessLog.objects.all()
        # 検索処理を実行
        username = self.request.GET.get('search_username') or ''
        actype = self.request.GET.get('search_accesstype')
        acat_from = self.request.GET.get('search_accessat_from')
        acat_to = self.request.GET.get('search_accessat_to')
        query_set = AccessLogListView.search_data(self=self, qs=query_set, username=username, actype=actype, acat_from=acat_from, acat_to=acat_to)
        # Excel出力用のレスポンスを取得
        result = Common.export_excel(model=AccessLog, data=query_set, file_name=file_name)
        # 処理結果を返却
        return result

class ExportCSV(generic.TemplateView):
    def get(self, request, *args, **kwargs):
        # 出力ファイル名を設定
        file_name = f'access_log_{datetime.now().replace(microsecond=0)}.csv'
        # queryセットを取得
        query_set = AccessLog.objects.all()
        # 検索処理を実行
        username = self.request.GET.get('search_username') or ''
        actype = self.request.GET.get('search_accesstype')
        acat_from = self.request.GET.get('search_accessat_from')
        acat_to = self.request.GET.get('search_accessat_to')
        query_set = AccessLogListView.search_data(self=self, qs=query_set, username=username, actype=actype, acat_from=acat_from, acat_to=acat_to)
        # Excel出力用のレスポンスを取得
        result = Common.export_csv(model=AccessLog, data=query_set, file_name=file_name)
        # 処理結果を返却
        return result
    