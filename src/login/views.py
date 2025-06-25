import csv
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.views import generic
from .models import AccessLog
from .const import *
from config.common import Common
from datetime import datetime
from django.http import HttpResponse
from openpyxl import Workbook

# 出力データカラム
OUTPUT_DATA_COLUMNS = ['usernmae', 'ip', 'access_type', 'access_at'] + Common.COMMON_DATA_COLUMNS


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
        # 検索を実行
        return search_data(request=self.request, query_set=query_set)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 検索フォーム設定
        context['search_username'] = self.request.GET.get('search_username') or ''
        context['search_accesstype'] = self.request.GET.get('search_accesstype')
        context['search_access_at_from'] = self.request.GET.get('search_access_at_from')
        context['search_access_at_to'] = self.request.GET.get('search_access_at_to')
        context['accesstype_list'] = ACCESSTYPE_CHOICES # アクセス種別リスト
        # ページネーション設定
        context = Common.set_pagination(context, self.request.GET.urlencode())
        # コンテキストを返却
        return context
    
def search_data(request, query_set):
    '''
    クエリセットに検索条件を適用
    '''
    # 検索条件を取得
    username = request.GET.get('search_username') or ''
    access_type= request.GET.get('search_accesstype')
    access_at_from = request.GET.get('search_access_at_from')
    access_at_to = request.GET.get('search_access_at_to')
    # 検索条件を適用
    if username: # ユーザーコード
        query_set = query_set.filter(username__icontains=username)
    if access_type: # アクセス種別
        query_set = query_set.filter(access_type=access_type)
    if access_at_from: # アクセス日時(From)
        query_set = query_set.filter(access_at__gte=access_at_from)
    if access_at_to: # アクセス日時(To)
        query_set = query_set.filter(access_at__lte=access_at_to)
    # 結果を返却
    return query_set

class ExportExcel(generic.TemplateView):
    def get(self, request, *args, **kwargs):
        """
        Excelデータの出力処理
        """
        # 出力ファイル名を設定
        file_name = f'access_log_{datetime.now().replace(microsecond=0)}.xlsx'
        # queryセットを取得
        data = AccessLog.objects.all()
        # 検索条件を適用
        data = search_data(request=request, query_set=data)
        # Excel出力用のレスポンスを取得
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        # Excelオブジェクト（ワークブック）を取得
        wb = Workbook()
        ws = wb.active
        # 列名をワークブックに適用
        ws.append(OUTPUT_DATA_COLUMNS)
        # ワークブックにデータを追加
        for rec in data:
            # ワークブックにデータを追加
            ws.append([
                rec.username
                , rec.ip
                , rec.access_type
                , rec.access_at.replace(tzinfo=None)
            ] + Common.get_common_columns(rec=rec))
        # 保存したワークブックをレスポンスに格納
        wb.save(response)
        # 処理結果を返却
        return response

class ExportCSV(generic.TemplateView):
    def get(self, request, *args, **kwargs):
        """
        CSVデータの出力処理
        """
        # 出力ファイル名を設定
        file_name = f'access_log_{datetime.now().replace(microsecond=0)}.csv'
        # queryセットを取得
        data = AccessLog.objects.all()
        # 検索条件を適用
        data = search_data(request=request, query_set=data)
        # CSV出力用のレスポンスを取得
        response = HttpResponse(content_type='text/csv; charset=Shift-JIS')
        response['Content-Disposition'] = 'attachment; filename*=UTF-8\'\'{}'.format(file_name)
        # ヘッダの書き込み
        writer = csv.writer(response)
        writer.writerow(OUTPUT_DATA_COLUMNS)
        # データの書き込み
        for rec in data:
            writer.writerow([
                rec.username
                , rec.ip
                , rec.access_type
                , rec.access_at.replace(tzinfo=None)
            ] + Common.get_common_columns(rec=rec))
        # 処理結果を返却
        return response
    