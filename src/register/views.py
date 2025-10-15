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
from .models import CustomUser, UserGroup
from .forms import UserSearchForm, SignUpForm, ChangePasswordForm, UserGroupForm
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView, PrivilegeRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from .constants import  PRIVILEGE_CHOICES, EMPLOYMENT_STATUS_CHOICES, GENDER_CHOICES


# CSV/Excel の共通出力カラム
DATA_COLUMNS = [
    'username', 'email', 'gender', 'tel_number'
    'employment_status', 'employment_end_date', 'privilege'
]

FILENAME_PREFIX = 'user_mst'

#--------------------------
# User CRUD
#--------------------------
class UserListView(PrivilegeRequiredMixin, generic.ListView):
    '''
    ユーザー一覧画面
    '''
    model = CustomUser
    template_name = 'register/list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        req = self.request
        form = UserSearchForm(req.GET or None)
        
        # クエリセットを初期化（削除フラグ：False, 所属テナント限定）
        queryset = CustomUser.objects.filter(is_deleted=False, tenant=req.user.tenant)
        
        # フォームが有効なら検索条件を反映
        if form.is_valid():
            queryset = filter_data(cleaned_data=form.cleaned_data, queryset=queryset)

        # 並び替え
        sort = form.cleaned_data.get('sort') if form.is_valid() else ''
        queryset = set_table_sort(queryset=queryset, sort=sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = UserSearchForm(self.request.GET or None)
        context['form'] = form
        context['user_group_form'] = UserGroupForm(self.request.GET or None)
        context['GENDER_CHOICES'] = GENDER_CHOICES
        context['EMPLOYMENT_STATUS_CHOICES'] = EMPLOYMENT_STATUS_CHOICES
        context['PRIVILEGE_CHOICES'] = PRIVILEGE_CHOICES
        return context


class UserCreateView(PrivilegeRequiredMixin, generic.CreateView):
    '''
    ユーザー登録
    '''
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
        self.object = form.save(commit=False)
        self.object.password = make_password(raw_password)
        self.object.create_user = self.request.user
        self.object.update_user = self.request.user
        self.object.tenant = self.request.user.tenant
        self.object.save()
        form.save_m2m()
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
    '''
    ユーザー更新
    '''
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
            form.save_m2m()
            set_message(request, '更新', self.object.username)
            return JsonResponse({'success': True})
        else:
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
    '''
    パスワードの変更処理
    '''
    form_class = ChangePasswordForm
    template_name = 'register/password_change.html'

    def get_success_url(self):
        messages.success(self.request, 'パスワードが変更されました')
        return reverse('dashboard:top')


class UserDeleteView(PrivilegeRequiredMixin, generic.View):
    '''
    ユーザー削除（物理削除）
    '''
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
    '''
    ユーザー一括削除
    '''
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


class UserGroupManageView(generic.FormView):
    '''
    ユーザーグループ管理（新規作成・更新・削除）
    '''
    template_name = 'register/user_group_mst.html'
    form_class = UserGroupForm
    success_url = reverse_lazy('register:group_manage')
    
    def post(self, request, *args, **kwargs):
        '''グループ名がnullでもバリデーションを通すための処理'''
        if request.POST.get('action') == 'delete':
            form = self.get_form()
            if not form.is_valid():
                form.cleaned_data = form.cleaned_data if hasattr(form, 'cleaned_data') else {}
            return self.form_valid(form)
        else:
            return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        req = self.request
        action = req.POST.get('action')
        selected_group = form.cleaned_data.get('selected_group')
        name = form.cleaned_data.get('group_name')

        if action == 'save':
            if not name:
                messages.warning(req, 'グループ名を入力してください。')
            elif selected_group:
                selected_group.group_name = name
                selected_group.update_user = req.user
                selected_group.save(update_fields=['group_name', 'update_user', 'updated_at'])
                messages.success(req, f'グループ「{name}」を更新しました。')
            else:
                UserGroup.objects.create(group_name=name, tenant_id=req.user.tenant.id, create_user=req.user, update_user=req.user)
                messages.success(req, f'グループ「{name}」を新規作成しました。')

        elif action == 'delete' and selected_group:
            selected_group.delete()
            messages.success(req, f'グループ「{selected_group.group_name}」を削除しました。')

        return redirect(f"{reverse('register:list')}?group_open=1")

    def form_invalid(self, form):
        messages.error(self.request, '入力内容に誤りがあります。')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()  # ← これで初期表示にもフォームが確実に渡る
        context['groups'] = UserGroup.objects.filter(is_deleted=False).order_by('group_name')
        return context


#--------------------------
# Export / Import
#--------------------------
class ExportExcel(PrivilegeRequiredMixin, ExcelExportBaseView):
    model_class = CustomUser
    filename_prefix = FILENAME_PREFIX
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return filter_data(request, queryset).order_by('username')

    def row(self, rec):
        return get_row(rec)


class ExportCSV(PrivilegeRequiredMixin, CSVExportBaseView):
    model_class = CustomUser
    filename_prefix = FILENAME_PREFIX
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return filter_data(request, queryset).order_by('username')

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


#--------------------------
# 共通関数
#--------------------------
def get_row(rec):
    return [
        rec.username,
        rec.email,
        rec.gender,
        rec.tel_number,
        rec.employment_status,
        rec.employment_end_date,
        rec.privilege,
    ]

def filter_data(cleaned_data, queryset):
    ''' ユーザーマスタ一覧の検索条件付与 '''
    #------------------------
    # キーワード検索
    #------------------------
    keyword = cleaned_data.get('search_keyword', '').strip()
    if keyword:
        queryset = queryset.filter(
            Q(username__icontains=keyword)
            | Q(username_kana__icontains=keyword)
            | Q(email__icontains=keyword)
        )

    #------------------------
    # 詳細検索
    #------------------------
    if cleaned_data.get('search_username'):
        queryset = queryset.filter(username__icontains=cleaned_data['search_username'])

    if cleaned_data.get('search_email'):
        queryset = queryset.filter(email__icontains=cleaned_data['search_email'])

    if cleaned_data.get('search_gender'):
        queryset = queryset.filter(gender=cleaned_data['search_gender'])

    if cleaned_data.get('search_tel_number'):
        queryset = queryset.filter(tel_number__icontains=cleaned_data['search_tel_number'])

    if cleaned_data.get('search_employment_status'):
        queryset = queryset.filter(employment_status=cleaned_data['search_employment_status'])

    if cleaned_data.get('search_privilege'):
        queryset = queryset.filter(privilege=cleaned_data['search_privilege'])

    return queryset

def set_table_sort(queryset, sort):
    '''
    クエリセットにソート順を設定
    '''
    if sort in ['username_kana', '-username_kana', 'email', '-email']:
        return queryset.order_by(sort)
    return queryset.order_by('id')

def set_message(request, action, username):
    messages.success(request, f'ユーザー「{username}」を{action}しました。')
