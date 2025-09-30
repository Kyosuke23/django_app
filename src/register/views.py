import secrets
from django.contrib.auth.hashers import make_password
from django.views import generic
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from .models import CustomUser
from .forms import SignUpForm, ChangePasswordForm
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView
from django.contrib.auth.views import PasswordChangeView
from django.http import HttpResponseForbidden
from .constants import PRIVILEGE_EDITOR, PRIVILEGE_CHOICES, EMPLOYMENT_STATUS_CHOICES


# CSV/Excel の共通出力カラム
DATA_COLUMNS = [
    'username', 'email', 'gender', 'tel_number'
    'employment_status', 'employment_end_date', 'privilege'
] + Common.COMMON_DATA_COLUMNS

FILENAME_PREFIX = 'user_mst'

class PrivilegeRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        # privilege 1=管理者, 2=編集者, 3=一般, それ以降はアクセス不可
        if int(request.user.privilege) > int(PRIVILEGE_EDITOR):
            return HttpResponseForbidden("ユーザーマスタへのアクセス権限がありません")
        return super().dispatch(request, *args, **kwargs)

# -----------------------------
# User CRUD
# -----------------------------

class UserListView(PrivilegeRequiredMixin, generic.ListView):
    """ユーザー一覧画面"""
    model = CustomUser
    template_name = 'register/list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        qs = CustomUser.objects.filter(is_deleted=False, tenant=self.request.user.tenant)
        qs = filter_data(self.request, qs)
        return qs.order_by('username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_keyword'] = self.request.GET.get('search_keyword') or ''
        context['search_privilege'] = self.request.GET.get('search_privilege') or ''
        context['search_employment_status'] = self.request.GET.get('search_employment_status') or ''
        context['PRIVILEGE_CHOICES'] = PRIVILEGE_CHOICES
        context['EMPLOYMENT_STATUS_CHOICES'] = EMPLOYMENT_STATUS_CHOICES
        context = Common.set_pagination(context, self.request.GET.urlencode())
        return context


class UserCreateView(PrivilegeRequiredMixin, generic.CreateView):
    """ユーザー登録（モーダル対応）"""
    model = CustomUser
    form_class = SignUpForm
    template_name = 'register/form.html'

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        html = render_to_string(
            self.template_name,
            {
                'form': form,
                'form_action': reverse('register:create'),
                'modal_title': 'ユーザー新規登録',
            },
            request
        )
        return JsonResponse({'success': True, 'html': html})

    def form_valid(self, form):
        raw_password = secrets.token_urlsafe(8)  # 8文字程度の安全な文字列でランダムパスワード
        print(f'----- random password: {raw_password} -----')
        self.object = form.save(commit=False)
        self.object.password = make_password(raw_password)
        self.object.create_user = self.request.user
        self.object.update_user = self.request.user
        self.object.tenant = self.request.user.tenant
        self.object.save()
        set_message(self.request, '登録', self.object.username)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(
                self.template_name,
                {
                    'form': form,
                    'form_action': reverse('register:create'),
                    'modal_title': 'ユーザー新規登録',
                },
                self.request
            )
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)


class UserUpdateView(PrivilegeRequiredMixin, generic.UpdateView):
    """ユーザー更新（モーダル対応）"""
    model = CustomUser
    form_class = SignUpForm
    template_name = 'register/form.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(instance=self.object)
        html = render_to_string(
            self.template_name,
            {
                'form': form,
                'form_action': reverse('register:update', kwargs={'pk': self.object.pk}),
                'modal_title': f'ユーザー更新: {self.object.username}',
            },
            request
        )
        return JsonResponse({'success': True, 'html': html})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            self.object = form.save(commit=False)
            self.object.update_user = request.user
            self.object.save()
            set_message(request, '更新', self.object.username)
            return JsonResponse({'success': True})
        else:
            print("form errors:", form.errors)
            print("non_field_errors:", form.non_field_errors())
            html = render_to_string(
                self.template_name,
                {
                    'form': form,
                    'form_action': reverse('register:update', kwargs={'pk': self.object.pk}),
                    'modal_title': f'ユーザー更新: {self.object.username}',
                },
                request
            )
            return JsonResponse({'success': False, 'html': html})


class ProfileUpdateView(generic.UpdateView):
    '''
    ログイン中のユーザーが自分の情報を編集する画面
    - これだけは権限制御なし
    '''
    model = CustomUser
    template_name = 'register/update_profile.html'
    form_class = SignUpForm
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

    
class UserChangePassword(PrivilegeRequiredMixin, PasswordChangeView):
    """
    パスワードの変更処理
    """
    form_class = ChangePasswordForm
    template_name = 'register/password_change.html'

    def get_success_url(self):
        messages.success(self.request, 'パスワードが変更されました')
        return reverse('dashboard:top')


class UserDeleteView(PrivilegeRequiredMixin, generic.View):
    """ユーザー削除"""
    success_url = reverse_lazy('register:list')

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(CustomUser, pk=kwargs['pk'])
        # 自分自身は削除不可
        if obj.pk == request.user.pk:
            return JsonResponse({
                'error': '自分自身のユーザーは削除できません',
                'details': ''
            }, status=400)
        try:
            obj.delete()
            set_message(request, '削除', obj.username)
            return JsonResponse({'success': True})
        except ProtectedError:
            return JsonResponse({
                'error': '使用中のユーザーは削除できません',
                'details': ''
            }, status=400)


class UserBulkDeleteView(PrivilegeRequiredMixin, generic.View):
    """ユーザー一括削除"""
    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('ids')
        if ids:
            if str(request.user.pk) in ids:
                return JsonResponse({
                    'error': '自分自身のユーザーは削除できません'
                }, status=400)
            try:
                CustomUser.objects.filter(id__in=ids).delete()
                return JsonResponse({'message': f'{len(ids)}件削除しました'})
            except ProtectedError:
                return JsonResponse({
                    'error': '使用中のユーザーは削除できません'
                }, status=400)
        else:
            messages.warning(request, '削除対象が選択されていません')
        return redirect('register:list')


# -----------------------------
# Export / Import
# -----------------------------

class ExportExcel(PrivilegeRequiredMixin, ExcelExportBaseView):
    model_class = CustomUser
    filename_prefix = FILENAME_PREFIX
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return filter_data(request, qs)

    def row(self, rec):
        return get_row(rec)


class ExportCSV(PrivilegeRequiredMixin, CSVExportBaseView):
    model_class = CustomUser
    filename_prefix = FILENAME_PREFIX
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return filter_data(request, qs)

    def row(self, rec):
        return get_row(rec)


class ImportCSV(PrivilegeRequiredMixin, CSVImportBaseView):
    expected_headers = DATA_COLUMNS
    model_class = CustomUser
    unique_field = 'email'

    def validate_row(self, row, idx, existing, request):
        email = row.get('email')
        if not email:
            return None, f'{idx}行目: メールアドレス が空です'
        if email in existing:
            return None, f'{idx}行目: メールアドレス "{email}" は既に存在します'

        obj = CustomUser(
            username=row.get('username'),
            email=email,
            gender=row.get('gender') or '',
            tel_number=row.get('tel_number') or '',
            employment_status=row.get('employment_status') or '1',
            employment_end_date=row.get('employment_end_date') or None,
            privilege=row.get('privilege') or '3',
            create_user=request.user,
            update_user=request.user
        )
        return obj, None


# -----------------------------
# 共通関数
# -----------------------------

def get_row(rec):
    return [
        rec.username,
        rec.email,
        rec.gender,
        rec.tel_number,
        rec.employment_status,
        rec.employment_end_date,
        rec.privilege,
    ] + Common.get_common_columns(rec=rec)


def filter_data(request, query_set):
    keyword = request.GET.get('search_keyword') or ''
    privilege = request.GET.get('search_privilege') or ''
    employment_status = request.GET.get('search_employment_status') or ''

    if keyword:
        query_set = query_set.filter(Q(username__icontains=keyword) | Q(email__icontains=keyword))
    if privilege:
        query_set = query_set.filter(privilege=privilege)
    if employment_status:
        query_set = query_set.filter(employment_status=employment_status)
    return query_set


def set_message(request, action, username):
    messages.success(request, f'ユーザー「{username}」を{action}しました。')
