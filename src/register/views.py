from .forms import SignUpForm, EditForm, ChangePasswordForm
from register.models import CustomUser
from django.views import generic
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.views import PasswordChangeView
from .constants import *
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView

# CSV/Excel 共通カラム
DATA_COLUMNS = [
    'username', 'last_name', 'first_name', 'gender', 'email',
    'birthday', 'tel_number', 'postal_code', 'state', 'city',
    'address', 'address2', 'privilege', 'employment_status', 'employment_end_date'
] + Common.COMMON_DATA_COLUMNS

FILENAME_PREFIX = 'user_mst'

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
        context['search_keyword'] = self.request.GET.get('search_keyword') or ''
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
    keyword = request.GET.get('search_keyword') or ''
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
    
class ProfileUpdate(generic.UpdateView):
    '''
    ログイン中のユーザーが自分の情報を編集する画面
    '''
    model = CustomUser
    template_name = 'register/update_profile.html'
    form_class = EditForm
    context_object_name = 'user'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        messages.success(self.request, 'プロフィールを更新しました')
        return reverse('register:update_profile')

    def form_valid(self, form):
        Common.save_data(selv=self, form=form, is_update=True)
        return super().form_valid(form)
    
    def form_invalid(self, form):
        pass

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
    
# -----------------------------
# Export / Import
# -----------------------------

class ExportExcel(ExcelExportBaseView):
    '''
    ユーザーマスタのExcel出力
    '''
    model_class = CustomUser
    filename_prefix = FILENAME_PREFIX
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return filter_data(request=request, query_set=qs)

    def row(self, rec):
        return get_row(rec=rec)


class ExportCSV(CSVExportBaseView):
    '''
    ユーザーマスタのCSV出力
    '''
    model_class = CustomUser
    filename_prefix = FILENAME_PREFIX
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return filter_data(request=request, query_set=qs)

    def row(self, rec):
        return get_row(rec=rec)


class ImportCSV(CSVImportBaseView):
    '''
    ユーザーマスタのCSVインポート
    '''
    expected_headers = DATA_COLUMNS
    model_class = CustomUser
    unique_field = 'username'

    def validate_row(self, row, idx, existing, request):
        username = row.get('username')
        if not username:
            return None, f'{idx}行目: username が空です'
        if username in existing:
            return None, f'{idx}行目: username "{username}" は既に存在します'

        obj = CustomUser(
            username=username,
            last_name=row.get('last_name'),
            first_name=row.get('first_name'),
            gender=row.get('gender'),
            email=row.get('email'),
            birthday=row.get('birthday') or None,
            tel_number=row.get('tel_number'),
            postal_code=row.get('postal_code'),
            state=row.get('state'),
            city=row.get('city'),
            address=row.get('address'),
            address2=row.get('address2'),
            privilege=row.get('privilege') or '3',
            employment_status=row.get('employment_status') or '1',
            employment_end_date=row.get('employment_end_date') or None,
            create_user=request.user,
            update_user=request.user,
            tenant=request.user.tenant
        )
        return obj, None


# -----------------------------
# 共通関数
# -----------------------------

def get_row(rec):
    '''CSV/Excel出力用: 1行分のリストを返す'''
    return [
        rec.username,
        rec.last_name,
        rec.first_name,
        rec.gender,
        rec.email,
        rec.birthday,
        rec.tel_number,
        rec.postal_code,
        rec.state,
        rec.city,
        rec.address,
        rec.address2,
        rec.privilege,
        rec.employment_status,
        rec.employment_end_date,
    ] + Common.get_common_columns(rec=rec)


def filter_data(request, query_set):
    ''' 検索条件付与 '''
    keyword = request.GET.get('search_keyword') or ''
    if keyword:
        query_set = query_set.filter(
            Q(username__icontains=keyword) |
            Q(last_name__icontains=keyword) |
            Q(first_name__icontains=keyword) |
            Q(email__icontains=keyword)
        )
    return query_set