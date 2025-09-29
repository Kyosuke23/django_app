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
from .constants import *
from config.common import Common
from datetime import datetime
from openpyxl import Workbook

# 出力データカラム
OUTPUT_DATA_COLUMNS = ['usernmae', 'first_name', 'last_name', 'email', 'gender', 'birthday', 'tel_number', 'postal_cd', 'state', 'city', 'address', 'address2', 'privilege'] + Common.COMMON_DATA_COLUMNS


class RegisterUserList(generic.ListView, generic.edit.ModelFormMixin):
    """
    ユーザーの一覧表示
    """
    model = CustomUser
    form_class = SignUpForm
    context_object_name = 'users'
    template_name = 'register/list.html'
    paginate_by = 50

    def get_queryset(self, **kwarg):
        query_set = super().get_queryset(**kwarg)
        query_set = query_set.filter(tenant=self.request.user.tenant)
        return filter_data(request=self.request, query_set=query_set)

    def get_context_data(self, **kwarg):
        context = super().get_context_data(**kwarg)
        context['search_key'] = self.request.GET.get('search_key') or ''
        context['search_gender'] = self.request.GET.get('search_gender')
        context['search_privilege'] = self.request.GET.get('search_privilege')
        context['gender_list'] = GENDER_CHOICES
        context['privilege_list'] = PRIVILEGE_CHOICES
        context = Common.set_pagination(context, self.request.GET.urlencode())
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
        
def filter_data(request, query_set):
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
    model = CustomUser
    template_name = 'register/create.html'
    context_object_name = 'user'
    form_class = SignUpForm
    
    def get_success_url(self):
        return reverse('register:list')
    
    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            Common.save_data(selv=self, form=form, is_update=False)
            messages.success(request, '登録が完了しました')
        result = JsonResponse(
            {
                'errors': form.errors
                , 'success_url': self.get_success_url()
            },
            json_dumps_params={'ensure_ascii': False}
        )
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
        return reverse('register:list')
    
    def post(self, request, *args, **kwargs):
        user = get_object_or_404(CustomUser, pk=request.POST['pk'])
        form = EditForm(request.POST, instance=user)
        print(user.gender)
        if form.is_valid():
            Common.save_data(selv=self, form=form, is_update=True)
            messages.success(request, '更新が完了しました')
        result = JsonResponse(
            {
                'errors': form.errors
                , 'success_url': self.get_success_url()
            },
            json_dumps_params={'ensure_ascii': False}
        )
        return result
    
class RegisterUserDelete(generic.edit.DeleteView):
    """
    ユーザー情報の削除処理
    """
    model = CustomUser
    template_name = 'register/delete.html'

    def get_success_url(self):
        return reverse('register:list')

    def post(self, request, *args, **kwargs):
        CustomUser.objects.filter(pk=request.POST['pk']).delete()
        messages.success(request, '削除が完了しました')
        result = JsonResponse(
            {
                'errors': {}
                , 'success_url': self.get_success_url()
            },
            json_dumps_params={'ensure_ascii': False}
        )
        return result
    
class RegisterUserChangePassword(PasswordChangeView):
    """
    パスワードの変更処理
    """
    form_class = ChangePasswordForm
    template_name = 'register/password_change.html'

    def get_success_url(self):
        messages.success(self.request, 'パスワードが変更されました')
        return reverse('dashboard:top')
    
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
        data = filter_data(request=request, query_set=data)
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
        data = filter_data(request=request, query_set=data)
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