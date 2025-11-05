import secrets
from django.contrib.auth.hashers import make_password
from django.views import generic
from django.db import transaction
from django.urls import reverse, reverse_lazy
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.template.loader import render_to_string
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Q
from .models import CustomUser, UserGroup
from .forms import UserSearchForm, SignUpForm, ChangePasswordForm, UserGroupForm, InitialUserForm, SignUpForm
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView, PrivilegeRequiredMixin, SystemUserOnlyMixin, ManagerOverMixin
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from tenant_mst.models import Tenant
from .constants import (
    PRIVILEGE_CHOICES
    , EMPLOYMENT_STATUS_CHOICES
    , GENDER_CHOICES
    , PRIVILEGE_MANAGER
    , GENDER_CHOICES_MAP
    , PRIVILEGE_CHOICES_MAP
    , EMPLOYMENT_STATUS_CHOICES_MAP
    , PRIVILEGE_SYSTEM
)


# 出力カラム定義
HEADER_MAP = {
    'ユーザー名': 'username',
    'ユーザー名（カナ）': 'username_kana',
    'メールアドレス': 'email',
    '性別': 'gender',
    '電話番号': 'tel_number',
    '雇用状態': 'employment_status',
    '権限': 'privilege',
    '所属グループ': 'groups_custom'
}

# 出力ファイル名定義
FILENAME_PREFIX = 'user_mst'

#--------------------------
# User CRUD
#--------------------------
class UserListView(LoginRequiredMixin, PrivilegeRequiredMixin, generic.ListView):
    '''
    ユーザー一覧画面
    '''
    model = CustomUser
    template_name = 'register/list.html'
    context_object_name = 'users'
    paginate_by = settings.DEFAULT_PAGE_SIZE

    def get_queryset(self):
        req = self.request
        user = req.user
        form = UserSearchForm(req.GET or None, user=user)

        # クエリセットを初期化（削除フラグ：False, 所属テナント限定）
        queryset = CustomUser.objects.filter(is_deleted=False, tenant=req.user.tenant)

        # システム権限以外のユーザーにはシステム権限ユーザーを見せない
        if user.privilege != PRIVILEGE_SYSTEM:
            queryset = queryset.exclude(privilege=PRIVILEGE_SYSTEM)

        # フォームが有効なら検索条件を反映
        if form.is_valid():
            queryset = filter_data(cleaned_data=form.cleaned_data, queryset=queryset)

        # 並び替え
        sort = form.cleaned_data.get('sort') if form.is_valid() else ''
        queryset = set_table_sort(queryset=queryset, sort=sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = UserSearchForm(self.request.GET or None, user=self.request.user)
        context['user_group_form'] = UserGroupForm(self.request.GET or None, user=self.request.user)
        context['GENDER_CHOICES'] = GENDER_CHOICES
        context['EMPLOYMENT_STATUS_CHOICES'] = EMPLOYMENT_STATUS_CHOICES
        context['PRIVILEGE_CHOICES'] = PRIVILEGE_CHOICES
        context = Common.set_pagination(context, self.request.GET.urlencode())
        return context


class UserCreateView(LoginRequiredMixin, ManagerOverMixin, generic.CreateView):
    '''
    ユーザー登録
    '''
    model = CustomUser
    form_class = SignUpForm
    template_name = 'register/form.html'

    def get(self, request, *args, **kwargs):

        form = self.get_form()

        # 権限選択肢を制限
        form.fields['privilege'].choices = filter_privilege(request.user)

        html = render_to_string(
            self.template_name,
            {
                'edit_form': form,
                'form_action': reverse('register:create'),
                'modal_title': 'ユーザー: 新規登録',
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
                    'edit_form': form,
                    'form_action': reverse('register:create'),
                    'modal_title': 'ユーザー: 新規登録',
                },
                self.request
            )
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class UserUpdateView(LoginRequiredMixin, ManagerOverMixin, generic.UpdateView):
    '''
    ユーザー更新
    '''
    model = CustomUser
    form_class = SignUpForm
    template_name = 'register/form.html'

    def get(self, request, *args, **kwargs):
        # 存在チェック
        try:
            self.object = self.get_object()
        except Http404:
            messages.error(request, 'このユーザーは既に削除されています。')
            return JsonResponse({'success': False}, status=404)

        form = self.get_form()

        # 権限選択肢を制限
        form.fields['privilege'].choices = filter_privilege(request.user)

        html = render_to_string(
            self.template_name,
            {
                'edit_form': form,
                'form_action': reverse('register:update', kwargs={'pk': self.object.pk}),
                'modal_title': f'ユーザー更新: {self.object.username}',
            },
            request
        )
        return JsonResponse({'success': True, 'html': html})

    def post(self, request, *args, **kwargs):
        # 存在チェック
        try:
            self.object = self.get_object()
        except Http404:
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                messages.error(request, 'このユーザーは既に削除されています。')
                return JsonResponse({'success': False}, status=404)
        # バリデーションチェック（Form）
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        # 更新対象フィールドは権限と所属グループのみ
        privilege = form.cleaned_data.get('privilege')
        employment_status = form.cleaned_data.get('employment_status')
        groups = form.cleaned_data.get('groups_custom')
        if privilege is not None:
            self.object.privilege = privilege
        if employment_status is not None:
            self.object.employment_status = employment_status
        if groups is not None:
            self.object.groups_custom.set(groups)
        # 更新者情報
        self.object.update_user = self.request.user
        self.object.save(update_fields=['employment_status', 'privilege', 'update_user', 'updated_at'])
        set_message(self.request, '更新', self.object.username)
        return JsonResponse({'success': True})

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(
                self.template_name,
                {
                    'edit_form': form,
                    'form_action': reverse('register:update', kwargs={'pk': self.object.pk}),
                    'modal_title': f'ユーザー更新: {self.object.username}',
                },
                self.request
            )
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['is_update'] = True
        return kwargs


class ProfileUpdateView(LoginRequiredMixin, generic.UpdateView):
    '''
    ログイン中のユーザーが自分の情報を編集する画面
    '''
    model = CustomUser
    template_name = 'register/update_profile.html'
    form_class = SignUpForm
    context_object_name = 'user'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        messages.success(self.request, 'プロフィールを更新しました。')
        return reverse('register:update_profile')

    def form_valid(self, form):
        Common.save_data(selv=self, form=form, is_update=True)
        return super().form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class UserChangePassword(LoginRequiredMixin, PasswordChangeView):
    '''
    パスワードの変更処理
    '''
    form_class = ChangePasswordForm
    template_name = 'register/password_change.html'

    def get_success_url(self):
        messages.success(self.request, 'パスワードが変更されました。')
        return reverse('dashboard:top')


class UserDeleteView(LoginRequiredMixin, PrivilegeRequiredMixin, generic.View):
    '''
    ユーザー削除（物理削除）
    '''
    success_url = reverse_lazy('register:list')

    def post(self, request, *args, **kwargs):
        # 存在チェック
        try:
            obj = get_object_or_404(CustomUser, pk=kwargs['pk'])
        except Http404:
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                messages.error(request, 'このユーザーは既に削除されています。')
                return JsonResponse({'success': False}, status=404)

        # 自分自身は削除不可
        if obj.pk == request.user.pk:
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                messages.error(request, 'ログイン中のユーザーは削除できません。')
                return JsonResponse({'success': False}, status=400)

        # 削除処理
        obj.delete()
        set_message(self.request, '削除', obj.username)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})


class UserBulkDeleteView(LoginRequiredMixin, ManagerOverMixin, generic.View):
    '''
    一括削除処理（物理削除）
    '''
    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('ids')

        if not ids:
            messages.warning(request, '削除対象が選択されていません')
            return redirect('register:list')

        try:
            with transaction.atomic():
                # 対象取得
                partners = CustomUser.objects.filter(id__in=ids)

                # ログイン中ユーザーは削除禁止
                if str(request.user.pk) in ids:
                    if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        messages.error(request, 'ログイン中のユーザーは削除できません。')
                        return JsonResponse({'success': False}, status=400)

                # 存在しないIDを検出
                found_ids = set(str(p.id) for p in partners)
                missing_ids = set(ids) - found_ids
                if missing_ids:
                    messages.error(request, 'すでに削除されているユーザーが含まれています。')
                    return JsonResponse({'success': False}, status=404)

                # 物理削除実行
                deleted_count, _ = partners.delete()

            return JsonResponse({'message': f'{deleted_count}件削除しました'})

        except ValueError as e:
            # トランザクションは自動ロールバック
            messages.error(request, str(e))
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': str(e)}, status=400)
            return redirect('register:list')

        except Exception:
            # 想定外エラー（DBエラーなど）
            messages.error(request, '削除処理中にエラーが発生しました。')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': '削除処理中にエラーが発生しました。'}, status=500)
            return redirect('register:list')


class UserGroupManageView(LoginRequiredMixin, ManagerOverMixin, generic.FormView):
    '''
    ユーザーグループ管理（新規作成・更新・削除）
    '''
    template_name = 'register/user_group_mst.html'
    form_class = UserGroupForm
    success_url = reverse_lazy('register:group_manage')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        """削除時など、名称未入力でもバリデーション通過させる"""
        if request.POST.get('action') == 'delete':
            form = self.get_form()
            if not form.is_valid():
                form.cleaned_data = form.cleaned_data if hasattr(form, 'cleaned_data') else {}
            return self.form_valid(form)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        req = self.request
        action = req.POST.get('action')
        selected_id = req.POST.get('selected_group')
        name = form.cleaned_data.get('group_name')

        # グループIDの存在チェック
        if selected_id:
            selected = UserGroup.objects.filter(id=int(selected_id), tenant=req.user.tenant).first()
        else:
            selected = None

        # 保存処理
        if action == 'save':
            # 更新
            if selected:
                selected.group_name = name
                selected.update_user = req.user
                selected.save(update_fields=['group_name', 'update_user', 'updated_at'])
                messages.success(req, f'ユーザーグループ「{name}」を更新しました。')
            # 新規登録
            else:
                UserGroup.objects.create(
                    group_name=name,
                    tenant=req.user.tenant,
                    create_user=req.user,
                    update_user=req.user,
                )
                messages.success(req, f'ユーザーグループ「{name}」を新規作成しました。')

        # 削除処理
        elif action == 'delete':
            # selected がない場合は即警告
            if not selected:
                messages.warning(req, '削除対象のユーザーグループを選択してください。')
                return redirect(f"{reverse('register:list')}?group_open=1")

            # 使用中チェック
            in_use = CustomUser.objects.filter(
                tenant=req.user.tenant,
                is_deleted=False,
                groups_custom=selected,
            ).exists()

            if in_use:
                messages.warning(req, f'ユーザーグループ「{selected.group_name}」は使用中のため、削除できません。')
                return redirect(f"{reverse('register:list')}?group_open=1")

            # 物理削除
            selected.delete()
            messages.success(req, f'ユーザーグループ「{selected.group_name}」を削除しました。')
            return redirect(f"{reverse('register:list')}?group_open=1")
        return redirect(f"{reverse('register:list')}?group_open=1")

    def form_invalid(self, form):
        """未入力などバリデーションエラー時のハンドリング"""
        if self.request.POST.get('action') == 'save':
            if 'selected_category' in form.errors:
                msg = form.errors['selected_category'][0]
            elif 'group_name' in form.errors:
                msg = form.errors['group_name'][0]
            else:
                msg = 'エラーが発生しました。'
            messages.error(self.request, msg)
        return redirect(f"{reverse('register:list')}?category_open=1")


#--------------------------
# Export / Import
#--------------------------
class ExportExcel(LoginRequiredMixin, ExcelExportBaseView):
    model_class = CustomUser
    filename_prefix = FILENAME_PREFIX
    headers = HEADER_MAP

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return filter_data(request, queryset).order_by('username')

    def row(self, rec):
        return get_row(rec)

class ExportCheckView(LoginRequiredMixin, generic.View):
    '''CSV出力前の件数チェック'''
    def get(self, request):
        form = UserSearchForm(request.GET or None)
        queryset = CustomUser.objects.filter(is_deleted=False, tenant=request.user.tenant)

        if form.is_valid():
            queryset = filter_data(cleaned_data=form.cleaned_data, queryset=queryset)

        count = queryset.count()
        if count > settings.MAX_EXPORT_ROWS:
            return JsonResponse({
                'warning': f"出力件数が上限（{settings.MAX_EXPORT_ROWS:,}件）を超えています。"
                           f"先頭{settings.MAX_EXPORT_ROWS:,}件のみを出力します。"
            })

        return JsonResponse({'ok': True})

class ExportCSV(LoginRequiredMixin, CSVExportBaseView):
    '''
    ユーザーマスタのCSV出力
    - 共通の get_row を利用
    - 検索条件を適用
    '''
    model_class = CustomUser
    filename_prefix = FILENAME_PREFIX
    headers = list(HEADER_MAP.keys())

    def get_queryset(self, request):
        req = self.request
        form = UserSearchForm(req.GET or None)

        # 初期クエリセット（削除フラグ：False, 所属テナント限定）
        queryset = CustomUser.objects.filter(is_deleted=False, tenant=req.user.tenant)

        # 検索フォーム有効時のフィルタ
        if form.is_valid():
            queryset = filter_data(cleaned_data=form.cleaned_data, queryset=queryset)

        # 並び替え処理
        sort = form.cleaned_data.get('sort') if form.is_valid() else ''
        queryset = set_table_sort(queryset=queryset, sort=sort)

        return queryset

    def row(self, rec):
        '''1行分のデータを返す'''
        return get_row(rec=rec)


class ImportCSV(LoginRequiredMixin, ManagerOverMixin, CSVImportBaseView):
    expected_headers = list(HEADER_MAP.keys())
    model_class = CustomUser
    unique_field = ('email')
    HEADER_MAP = HEADER_MAP

    def validate_row(self, row, idx, existing, request):
        data = row.copy()

        # ------------------------------------------------------
        # 日本語→コード変換
        # ------------------------------------------------------
        gender_map = dict(GENDER_CHOICES_MAP)
        val = data.get('gender')
        if val in gender_map:
            data['gender'] = gender_map[val]

        employment_map = dict(EMPLOYMENT_STATUS_CHOICES_MAP)
        val = data.get('employment_status')
        if val in employment_map:
            data['employment_status'] = employment_map[val]

        privilege_map = dict(PRIVILEGE_CHOICES_MAP)
        val = data.get('privilege')
        if val in privilege_map:
            data['privilege'] = privilege_map[val]

        # ------------------------------------------------------
        # 所属グループ（カンマ区切り）を ID リストに変換
        # ------------------------------------------------------
        group_value = data.get('groups_custom')
        group_ids = []
        if group_value:
            group_names = [g.strip() for g in group_value.split(',') if g.strip()]
            group_ids = list(
                UserGroup.objects.filter(
                    tenant=request.user.tenant,
                    group_name__in=group_names,
                    is_deleted=False
                ).values_list('id', flat=True)
            )
        data['groups_custom'] = group_ids

        # ------------------------------------------------------
        # 重複チェック（email）
        # ------------------------------------------------------
        email = data.get('email')
        if email in existing:
            return None, f'{idx}行目: メールアドレス「{email}」は既に存在します。'
        existing.add(email)

        # ------------------------------------------------------
        # Djangoフォームバリデーション
        # ------------------------------------------------------
        form = SignUpForm(data=data)
        if not form.is_valid():
            error_text = '; '.join(self._format_errors_with_verbose_name(form))
            return None, f'{idx}行目: {error_text}'

        # ------------------------------------------------------
        # オブジェクト作成
        # ------------------------------------------------------
        obj = form.save(commit=False)
        obj.tenant = request.user.tenant
        obj.create_user = request.user
        obj.update_user = request.user
        obj._form_instance = form
        return obj, None


# ------------------------------------------------------
# 初期ユーザー登録（システム管理者専用）
# ------------------------------------------------------
class InitialUserCreateView(LoginRequiredMixin, SystemUserOnlyMixin, generic.FormView):
    template_name = 'register/initial_user_form.html'
    form_class = InitialUserForm

    def form_valid(self, form):
        company_name = form.cleaned_data['company_name']
        username = form.cleaned_data['username']
        email = form.cleaned_data['email']

        # Tenant新規作成
        tenant = Tenant.objects.create(
            tenant_name=company_name,
            representative_name=username,   # 本人を代表者として仮登録
            email=email,
            create_user=self.request.user,
            update_user=self.request.user
        )

        # 初期ユーザー（仮登録）
        password = get_random_string(10)
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            tenant=tenant,
            is_active=False,
            privilege=PRIVILEGE_MANAGER,
            create_user=self.request.user,
            update_user=self.request.user,
        )
        user.is_active = True
        user.set_password(password)
        user.save()

        # ログインURLを生成
        login_url = self.request.build_absolute_uri('/login/')

        subject='【システム】初期ログイン情報のご案内',
        message = render_to_string(
            'register/mails/mail_initial_user.txt',
            {
                'username': username,
                'email': email,
                'password': password,
                'login_url': login_url,
            }
        )

        print('=======================')
        print(f'email: {email}')
        print(f'password: {password}')
        print(subject)
        print(message)
        print('=======================')

        # send_mail(
        #     subject=subject,
        #     message=message,
        #     from_email='noreply@example.com',
        #     recipient_list=[email],
        # )
        self.request.session['register_info'] = {
            'tenant_name': company_name,
            'user_name': username,
            'user_email': email,
        }

        return redirect(reverse('register:initial_done'))

class InitialUserRegisterDoneView(LoginRequiredMixin, SystemUserOnlyMixin, generic.TemplateView):
    template_name = 'register/initial_user_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['register_info'] = self.request.session.pop('register_info', None)
        return context


#--------------------------
# 共通関数
#--------------------------
def get_row(rec):
    group_names = ', '.join(rec.groups_custom.values_list('group_name', flat=True))

    return [
        rec.username,
        rec.username_kana or '',
        rec.email or '',
        rec.get_gender_display(),
        rec.tel_number or '',
        rec.get_employment_status_display(),
        rec.get_privilege_display(),
        group_names,
    ]

def filter_data(cleaned_data, queryset):
    """ユーザーマスタ一覧の検索条件付与"""
    keyword = cleaned_data.get('search_keyword', '').strip()
    q = Q()

    #------------------------
    # キーワード検索
    #------------------------
    if keyword:
        q |= (
            Q(username__icontains=keyword)
            | Q(username_kana__icontains=keyword)
            | Q(email__icontains=keyword)
            | Q(tel_number__icontains=keyword)
            | Q(groups_custom__group_name__icontains=keyword)
        )

    # 性別のキーワード検策
    mapped_value = None
    for key, val in GENDER_CHOICES_MAP:
        if keyword and keyword in key:
            mapped_value = val
            break
    if mapped_value:
        q |= Q(gender=mapped_value)

    # 雇用状態のキーワード検策
    mapped_value = None
    for key, val in EMPLOYMENT_STATUS_CHOICES_MAP:
        if keyword and keyword in key:
            mapped_value = val
            break
    if mapped_value:
        q |= Q(employment_status=mapped_value)

    # 権限のキーワード検策
    mapped_value = None
    for key, val in PRIVILEGE_CHOICES_MAP:
        if keyword and keyword in key:
            mapped_value = val
            break
    if mapped_value:
        q |= Q(privilege=mapped_value)

    # Q条件を適用
    if q:
        queryset = queryset.filter(q)

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

    if cleaned_data.get('search_user_group'):
        queryset = queryset.filter(groups_custom=cleaned_data['search_user_group'])

    return queryset.distinct()

def set_table_sort(queryset, sort):
    '''
    クエリセットにソート順を設定
    '''
    if sort in ['username_kana', '-username_kana', 'email', '-email']:
        return queryset.order_by(sort)
    return queryset.order_by('id')

def set_message(request, action, username):
    messages.success(request, f'ユーザー「{username}」を{action}しました。')

def filter_privilege(user):
    """ログインユーザーと同等・下位の権限のみを返す"""
    return [c for c in PRIVILEGE_CHOICES if c[0] >= user.privilege]