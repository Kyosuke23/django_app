import csv
from .forms import SignUpForm, EditForm, ChangePasswordForm
from register.models import CustomUser
from django.views import generic
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
from django.http import HttpResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.views import PasswordChangeView
from .const import *
from config.common import Common
from datetime import datetime
from openpyxl import Workbook
import json
import requests

# 出力データカラム
OUTPUT_DATA_COLUMNS = ['usernmae', 'first_name', 'last_name', 'email', 'gender', 'birthday', 'tel_number', 'postal_cd', 'state', 'city', 'address', 'address2', 'privilege']


class RegisterUserList(generic.ListView, generic.edit.ModelFormMixin):
    """
    ユーザーの一覧表示
    """
    model = CustomUser
    form_class = SignUpForm
    context_object_name = 'users'
    template_name = 'register/index.html'
    paginate_by = 50

    def get_queryset(self, **kwarg):
        # query_setをクレンジングして取得
        query_set = super().get_queryset(**kwarg)
        # 検索を実行
        return search_data(request=self.request, query_set=query_set)

    def get_context_data(self, **kwarg):
        # コンテキストデータの取得
        context = super().get_context_data(**kwarg)
        # 検索キーワードを取得（空白時に"None"と表示されるのを予防）
        search_key = self.request.GET.get('search_key') or ''
        search_gender = self.request.GET.get('search_gender')
        search_privilege = self.request.GET.get('search_privilege')
        # 検索フォームにキーワードを残す
        context['search_key'] = search_key
        context['search_gender'] = search_gender
        context['search_privilege'] = search_privilege
        # 各種リストのデータをフォームに適用
        context['gender_list'] = GENDER_CHOICES
        context['privilege_list'] = PRIVILEGE_CHOICES
        # ページネーション設定
        context = Common.set_pagination(context, self.request.GET.urlencode())
        # フォームの値を設定
        context['form'] = self.get_form
        return context

    def get(self, request, *args, **kwargs):
        self.object = None
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = None
        self.object_list = self.get_queryset()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        
def search_data(request, query_set):
    '''
    クエリセットに検索条件を適用
    '''
    # 検索キーワードを取得（空白時に"None"と表示されるのを予防）
    keyword = request.GET.get('search_key') or ''
    gender = request.GET.get('search_gender')
    privilege = request.GET.get('search_privilege')
    # 検索条件を適用
    if keyword: # キーワード
        query_set = query_set.filter(
            Q(username__icontains=keyword) | Q(first_name__icontains=keyword) | Q(last_name__icontains=keyword)
        )
    if gender: # 性別
        query_set = query_set.filter(gender=gender)
    if privilege: # 権限
        query_set = query_set.filter(privilege=privilege)
    # 結果を返却
    return query_set

class RegisterUserCreate(generic.edit.CreateView):
    """
    ユーザー情報の登録処理
    """
    class Meta:
        model = CustomUser
    template_name = 'register/create.html'
    context_object_name = 'user'
    form_class = SignUpForm
    
    def get_success_url(self):
        # 処理後は検索一覧画面に遷移
        return reverse('register:register_user_index')
    
    def post(self, request, *args, **kwargs):
        # フォームの入力データを取得
        form = self.get_form()
        # バリデーションを通過した場合のみフォームの情報を保存
        if form.is_valid():
            post = form.save(commit=False)
            # 作成者と更新者をログインユーザーで設定
            post.create_user = self.request.user
            post.update_user = self.request.user
            # 登録処理の実行
            post.save()
            # 処理成功のフラッシュメッセージを設定
            messages.success(request, '登録が完了しました')
        # 処理結果を格納
        result = JsonResponse(
            {
                'errors': form.errors  # エラーフィールド
                , 'success_url': self.get_success_url()  # 成功時の遷移先URL
            },
            json_dumps_params={'ensure_ascii': False}  # 文字化け対策
        )
        # 処理結果を返却
        return result
    
class RegisterUserUpdate(generic.edit.UpdateView):
    """
    ユーザー情報の更新処理
    """
    class Meta:
        model = CustomUser
    template_name = 'register/edit.html'
    context_object_name = 'user'
    form_class = EditForm
    
    def get_success_url(self):
        # 処理後は検索一覧画面に遷移
        return reverse('register:register_user_index')
    
    def post(self, request, *args, **kwargs):
        # フォームのデータからモデルインスタンスを取得
        user = get_object_or_404(CustomUser, pk=request.POST['pk'])
        # モデルを基にしたフォームを作成
        form = EditForm(request.POST, instance=user)
        print(user.gender)
        # バリデーションを通過した場合のみフォームの情報を保存
        if form.is_valid():
            # 更新ユーザーをログインユーザーで設定
            form.update_user = self.request.user
            # 保存処理の実行
            form.save()
            # 処理成功のフラッシュメッセージを設定
            messages.success(request, '更新が完了しました')
        # 処理結果を格納
        result = JsonResponse(
            {
                'errors': form.errors  # エラーフィールド
                , 'success_url': self.get_success_url()  # 成功時の遷移先URL
            },
            json_dumps_params={'ensure_ascii': False}  # 文字化け対策
        )
        # 処理結果を返却
        return result
    
class RegisterUserDelete(generic.edit.DeleteView):
    """
    ユーザー情報の削除処理
    """
    model = CustomUser
    template_name = 'register/delete.html'

    def get_success_url(self):
        # 処理後は検索一覧画面に遷移
        return reverse('register:register_user_index')

    def post(self, request, *args, **kwargs):
        # 削除処理の実行
        CustomUser.objects.filter(pk=request.POST['pk']).delete()
        # 処理成功のフラッシュメッセージを設定
        messages.success(request, '削除が完了しました')
        # 処理結果を格納
        result = JsonResponse(
            {
                'errors': {}  # エラーフィールド
                , 'success_url': self.get_success_url()  # 成功時の遷移先URL
            },
            json_dumps_params={'ensure_ascii': False}  # 文字化け対策
        )
        # 処理結果を返却
        return result
    
class RegisterUserChangePassword(PasswordChangeView):
    """
    パスワードの変更処理
    """
    form_class = ChangePasswordForm
    template_name = 'register/password_change.html'

    def get_success_url(self):
        # 処理成功のフラッシュメッセージを設定
        messages.success(self.request, 'パスワードが変更されました')
        # 処理後は検索一覧画面に遷移
        return reverse('dashboard:top')

class GetPostalCode(generic.TemplateView):
    """
    郵便番号による住所検索処理（Ajax）
    """
    def post(self, request, *args, **kwargs):
        # 入力された郵便番号を取得
        postal_cd = request.POST.get('postal_cd')
        # APIで住所検索
        res = requests.get(
            POSTAL_API_URL
            , params=({'zipcode': postal_cd})
        )
        # 取得結果を返却
        return HttpResponse(json.dumps({
            'address_info': res.json()
        }))
    
class ExportExcel(generic.TemplateView):
    def get(self, request, *args, **kwargs):
        """
        Excelデータの出力処理
        """
        # 出力ファイル名を設定
        file_name = f'user_mst_{datetime.now().replace(microsecond=0)}.xlsx'
        # queryセットを取得
        data = CustomUser.objects.all()
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
                , rec.first_name
                , rec.last_name
                , rec.email
                , GENDER_CHOICES[int(rec.gender)][1]
                , rec.birthday
                , rec.tel_number
                , rec.postal_cd
                , rec.state
                , rec.city
                , rec.address
                , rec.address2
                , PRIVILEGE_CHOICES[int(rec.privilege)][1]
            ])
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
        file_name = f'user_mst_{datetime.now().replace(microsecond=0)}.csv'
        # queryセットを取得
        data = CustomUser.objects.all()
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
                , rec.first_name
                , rec.last_name
                , rec.email
                , GENDER_CHOICES[int(rec.gender)][1]
                , rec.birthday
                , rec.tel_number
                , rec.postal_cd
                , rec.state
                , rec.city
                , rec.address
                , rec.address2
                , PRIVILEGE_CHOICES[int(rec.privilege)][1]
            ])
        # 処理結果を返却
        return response