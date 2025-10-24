from django.views import generic
from django.db import transaction
from django.conf import settings
from django.urls import reverse_lazy, reverse
from .models import Partner
from .form import PartnerSearchForm, PartnerForm
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView, PrivilegeRequiredMixin
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.template.loader import render_to_string
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin

# 出力カラム定義
HEADER_MAP = {
    '取引先名称' : 'partner_name',
    '取引先名称（カナ）': 'partner_name_kana',
    '取引先区分': 'partner_type',
    '担当者名': 'contact_name',
    'メールアドレス': 'email',
    '電話番号': 'tel_number',
    '郵便番号': 'postal_code',
    '都道府県': 'state',
    '市区町村': 'city',
    '住所': 'address',
    '住所2': 'address2',
}

# 出力ファイル名定義
FILENAME_PREFIX = 'partner_mst'

#-------------------------
# Partner CRUD
#-------------------------
class PartnerListView(LoginRequiredMixin, generic.ListView):
    model = Partner
    template_name = 'partner_mst/list.html'
    context_object_name = 'partners'
    paginate_by = settings.DEFAULT_PAGE_SIZE

    def get_queryset(self):
        req = self.request
        form = PartnerSearchForm(req.GET or None)

        # クエリセットを初期化（削除フラグ：False, 所属テナント限定）
        queryset = Partner.objects.filter(is_deleted=False, tenant=req.user.tenant)

        # フォームが有効なら検索条件を反映
        if form.is_valid():
            queryset = filter_data(cleaned_data=form.cleaned_data, queryset=queryset)

        # 並び替え
        sort = form.cleaned_data.get('sort') if form.is_valid() else ''
        queryset = set_table_sort(queryset=queryset, sort=sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PartnerSearchForm(self.request.GET or None)
        context['partner_types'] = Partner.PARTNER_TYPE_CHOICES
        context = Common.set_pagination(context, self.request.GET.urlencode())
        return context


class PartnerCreateView(LoginRequiredMixin, PrivilegeRequiredMixin, generic.CreateView):
    '''
    取引先登録
    - GET: 部分テンプレートを返す（Ajax）
    - POST: Ajaxで登録処理
    '''
    model = Partner
    form_class = PartnerForm
    template_name = 'partner_mst/form.html'

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        html = render_to_string(
            self.template_name,
            {
                'form': form,
                'form_action': reverse('partner_mst:create'),
                'modal_title': '取引先: 新規登録',
            },
            request
        )
        return JsonResponse({'success': True, 'html': html})

    def get_form(self, form_class=None):
        # フォームのインスタンスに tenant を最初から入れておく -> 同一テナント内での重複チェックのため
        form = super().get_form(form_class)
        form.instance.tenant = self.request.user.tenant
        return form

    def form_valid(self, form):
        # 保存処理
        Common.save_data(selv=self, form=form, is_update=False)
        # 処理後のメッセージ
        set_message(self.request, '登録', self.object.partner_name)
        # レスポンス
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(
                self.template_name,
                {
                    'form': form,
                    'form_action': reverse('partner_mst:create'),
                    'modal_title': '取引先: 新規登録',
                },
                self.request
            )
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)


class PartnerUpdateView(LoginRequiredMixin, PrivilegeRequiredMixin, generic.UpdateView):
    '''
    取引先更新
    - GET: 部分テンプレートを返す（Ajax）
    - POST: Ajaxで更新処理
    '''
    model = Partner
    form_class = PartnerForm
    template_name = 'partner_mst/form.html'

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            messages.error(request, 'この取引先は既に削除されています。')
            return JsonResponse({'success': False}, status=404)

        form = self.get_form()
        html = render_to_string(
            self.template_name,
            {
                'form': form,
                'form_action': reverse('partner_mst:update', kwargs={'pk': self.object.pk}),
                'modal_title': f'取引先更新: {self.object.partner_name}',
            },
            request
        )
        return JsonResponse({'success': True, 'html': html})

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                messages.error(request, 'この取引先は既に削除されています。')
                return JsonResponse({'success': False}, status=404)

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        Common.save_data(selv=self, form=form, is_update=True)
        set_message(self.request, '更新', self.object.partner_name)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            obj = getattr(self, 'object', None)
            modal_title = f'取引先更新: {obj.partner_name}' if obj else '取引先更新'
            html = render_to_string(
                self.template_name,
                {
                    'form': form,
                    'form_action': reverse(
                        'partner_mst:update',
                        kwargs={'pk': obj.pk} if obj else {}
                    ),
                    'modal_title': modal_title,
                },
                self.request
            )
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)


class PartnerDeleteView(LoginRequiredMixin, PrivilegeRequiredMixin, generic.View):
    '''
    取引先削除処理（物理削除）
    '''
    template_name = 'product_mst/delete.html'
    success_url = reverse_lazy('product_mst:list')

    def post(self, request, *args, **kwargs):
        try:
            obj = get_object_or_404(Partner, pk=kwargs['pk'])
        except Http404:
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                messages.error(request, 'この取引先は既に削除されています。')
                return JsonResponse({'success': False}, status=404)
        obj.delete()
        set_message(self.request, '削除', obj.partner_name)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})


class PartnerBulkDeleteView(LoginRequiredMixin, PrivilegeRequiredMixin, generic.View):
    '''
    一括削除処理（物理削除）
    '''
    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('ids')

        if not ids:
            messages.warning(request, '削除対象が選択されていません')
            return redirect('partner_mst:list')

        try:
            with transaction.atomic():
                # 対象取得
                partners = Partner.objects.filter(id__in=ids)

                # 存在しないIDを検出
                found_ids = set(str(p.id) for p in partners)
                missing_ids = set(ids) - found_ids

                if missing_ids:
                    messages.error(request, 'すでに削除されている取引先が含まれています。')
                    return JsonResponse({'success': False}, status=404)

                # 物理削除実行
                deleted_count, _ = partners.delete()

            return JsonResponse({'message': f'{deleted_count}件削除しました'})

        except ValueError as e:
            # トランザクションは自動ロールバック
            messages.error(request, str(e))
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': str(e)}, status=400)
            return redirect('partner_mst:list')

        except Exception:
            # 想定外エラー（DBエラーなど）
            messages.error(request, '削除処理中にエラーが発生しました。')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': '削除処理中にエラーが発生しました。'}, status=500)
            return redirect('partner_mst:list')


#-------------------------
# Export / Import
#-------------------------
class ExportExcel(LoginRequiredMixin, ExcelExportBaseView):
    model_class = Partner
    filename_prefix = FILENAME_PREFIX
    headers = list(HEADER_MAP.values())

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return filter_data(request=request, queryset=queryset).order_by('partner_name')

    def row(self, rec):
        return get_row(rec)

class ExportCheckView(LoginRequiredMixin, generic.View):
    '''CSV出力前の件数チェック'''
    def get(self, request):
        form = PartnerSearchForm(request.GET or None)
        queryset = Partner.objects.filter(is_deleted=False, tenant=request.user.tenant)

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
    model_class = Partner
    filename_prefix = FILENAME_PREFIX
    headers = list(HEADER_MAP.keys())


    def get_queryset(self, request):
        req = self.request
        form = PartnerSearchForm(req.GET or None)

        # 初期クエリセット（削除フラグ：False, 所属テナント限定）
        queryset = Partner.objects.filter(is_deleted=False, tenant=req.user.tenant)

        # 検索フォーム有効時のフィルタ
        if form.is_valid():
            queryset = filter_data(cleaned_data=form.cleaned_data, queryset=queryset)

        # 並び替え処理
        sort = form.cleaned_data.get('sort') if form.is_valid() else ''
        queryset = set_table_sort(queryset=queryset, sort=sort)

        # 出力件数制限処理（n件超の場合はメッセージ＋上限件数まで）
        total_count = queryset.count()
        if total_count > settings.MAX_EXPORT_ROWS:
            messages.warning(
                req,
                f"出力件数が上限（{settings.MAX_EXPORT_ROWS:,}件）を超えています。"
                f"先頭{settings.MAX_EXPORT_ROWS:,}件のみを出力しました。"
            )
            queryset = queryset[:settings.MAX_EXPORT_ROWS]

        return queryset

    def row(self, rec):
        return get_row(rec=rec)


class ImportCSV(LoginRequiredMixin, PrivilegeRequiredMixin, CSVImportBaseView):
    expected_headers = list(HEADER_MAP.keys())
    model_class = Partner
    unique_field = ('tenant_id', 'partner_name', 'email')
    HEADER_MAP = HEADER_MAP

    def validate_row(self, row, idx, existing, request):
        data = row.copy()

        # ------------------------------------------------------
        # Djangoフォームバリデーション
        # ------------------------------------------------------
        form = PartnerForm(data=data)
        if not form.is_valid():
            error_text = '; '.join(
                [f"{field}: {','.join(errors)}" for field, errors in form.errors.items()]
            )
            return None, f'{idx}行目: {error_text}'

        # ------------------------------------------------------
        # 重複チェック（tenant + name + email）
        # ------------------------------------------------------
        partner_name = data.get('partner_name')
        email = data.get('email')
        key = (request.user.tenant_id, partner_name, email)
        if key in existing:
            return None, f'{idx}行目: 取引先名称＋メールアドレス「{partner_name}, {email}」は既に存在します。'
        existing.add(key)

        # ------------------------------------------------------
        # Partner オブジェクト作成
        # ------------------------------------------------------
        obj = form.save(commit=False)
        obj.tenant = request.user.tenant
        obj.create_user = request.user
        obj.update_user = request.user

        return obj, None


#-------------------------
# 共通関数
#-------------------------
def get_row(rec):
    return [
        rec.partner_name,
        rec.partner_name_kana,
        rec.get_partner_type_display(),
        rec.contact_name,
        rec.email,
        rec.tel_number,
        rec.postal_code,
        rec.state,
        rec.city,
        rec.address,
        rec.address2
    ]


def filter_data(cleaned_data, queryset):
    keyword = cleaned_data.get('search_keyword', '').strip()
    q = None

    # キーワード検索
    if keyword:
        q = (
            Q(partner_name__icontains=keyword)
            | Q(partner_name_kana__icontains=keyword)
            | Q(contact_name__icontains=keyword)
            | Q(email__icontains=keyword)
            | Q(tel_number__icontains=keyword)
            | Q(postal_code__icontains=keyword)
            | Q(state__icontains=keyword)
            | Q(city__icontains=keyword)
            | Q(address__icontains=keyword)
            | Q(address2__icontains=keyword)
        )

    # キーワード入力が取引先区分値にあればに変換
    mapped_value = None
    for key, val in Partner.PARTNER_TYPE_MAP.items():
        if keyword not in (None, '') and keyword in key:
            mapped_value = val
            break

    if mapped_value:
        if q is not None:
            q |= Q(partner_type__icontains=mapped_value)
        else:
            q = Q(partner_type__icontains=mapped_value)

    if q is not None:
        queryset = queryset.filter(q)

    # 詳細検索
    if cleaned_data.get('search_partner_name'):
        queryset = queryset.filter(partner_name__icontains=cleaned_data['search_partner_name'])
    if cleaned_data.get('search_contact_name'):
        queryset = queryset.filter(contact_name__icontains=cleaned_data['search_contact_name'])
    if cleaned_data.get('search_email'):
        queryset = queryset.filter(email__icontains=cleaned_data['search_email'])
    if cleaned_data.get('search_tel_number'):
        queryset = queryset.filter(tel_number__icontains=cleaned_data['search_tel_number'])
    if cleaned_data.get('search_address'):
        s = cleaned_data['search_address']
        queryset = queryset.filter(
            Q(state__icontains=s) | Q(city__icontains=s)
            | Q(address__icontains=s) | Q(address2__icontains=s)
        )
    if cleaned_data.get('search_partner_type'):
        queryset = queryset.filter(partner_type=cleaned_data['search_partner_type'])
    return queryset

def set_table_sort(queryset, sort):
    '''
    クエリセットにソート順を設定
    '''
    if sort in ['partner_name_kana', '-partner_name_kana', 'email', '-email']:
        return queryset.order_by(sort)
    return queryset.order_by('id')

def set_message(request, action, partner_name):
    '''CRUD後の統一メッセージ'''
    messages.success(request, f'取引先「{partner_name}」を{action}しました。')
