from django.views import generic
from django.urls import reverse_lazy, reverse
from .models import Partner
from .form import PartnerForm
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView, PrivilegeRequiredMixin
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin

# CSV/Excel の共通出力カラム定義
DATA_COLUMNS = [
    'partner_name', 'partner_name_kana', 'partner_type', 'contact_name',
    'email', 'tel_number', 'postal_code', 'state', 'city', 'address', 'address2'
]

FILENAME_PREFIX = 'partner_mst'

#-------------------------
# Partner CRUD
#-------------------------
class PartnerListView(LoginRequiredMixin, generic.ListView):
    model = Partner
    template_name = 'partner_mst/list.html'
    context_object_name = 'partners'
    paginate_by = 20

    def get_queryset(self):
        '''
        検索条件を反映したクエリセットを返す
        '''
        # クエリセットを初期化（削除フラグ：False, 所属テナント限定）
        req = self.request
        queryset = Partner.objects.filter(is_deleted=False, tenant=req.user.tenant)
        
        # テンプレートの検索条件を適用
        queryset = filter_data(request=req, queryset=queryset)
        
         # クエリセット返却
        return queryset.order_by('partner_name')

    def get_context_data(self, **kwargs):
        '''
        テンプレートに渡す追加コンテキスト
        - 検索条件を保持
        - ページネーション情報を追加
        '''
        # コンテキスト取得
        context = super().get_context_data(**kwargs)
        g = self.request.GET
        
        # 検索フォームの入力値保持
        context['search_keyword'] = g.get('search_keyword') or ''
        context['search_partner_name'] = g.get('search_partner_name') or ''
        context['search_partner_type'] = g.get('search_partner_type') or ''
        context['search_contact_name'] = g.get('search_contact_name') or ''
        context['search_email'] = g.get('search_email') or ''
        context['search_tel_number'] = g.get('search_tel_number') or ''
        context['search_address'] = g.get('search_address') or ''
        
        # マスタ系の選択肢（セレクトボックス用）
        context['partner_types'] = Partner.PARTNER_TYPE_CHOICES
        
        # ページネーション保持
        context = Common.set_pagination(context, g.urlencode())
        
        # コンテキストの返却
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
        self.object = self.get_object()
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
        obj = get_object_or_404(Partner, pk=kwargs['pk'])
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
        if ids:
            Partner.objects.filter(id__in=ids).delete()
            return JsonResponse({'message': f'{len(ids)}件削除しました'})
        else:
            messages.warning(request, '削除対象が選択されていません')
        return redirect('partner_mst:list')


#-------------------------
# Export / Import
#-------------------------
class ExportExcel(LoginRequiredMixin, ExcelExportBaseView):
    model_class = Partner
    filename_prefix = FILENAME_PREFIX
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return filter_data(request=request, queryset=queryset).order_by('partner_name')

    def row(self, rec):
        return get_row(rec)


class ExportCSV(LoginRequiredMixin, CSVExportBaseView):
    model_class = Partner
    filename_prefix = FILENAME_PREFIX
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return filter_data(request=request, queryset=queryset).order_by('partner_name')

    def row(self, rec):
        return get_row(rec)


class ImportCSV(LoginRequiredMixin, CSVImportBaseView):
    expected_headers = DATA_COLUMNS
    model_class = Partner
    unique_field = ('tenant_id', 'partner_name', 'email')

    def validate_row(self, row, idx, existing, request):
        form = PartnerForm(data=row)

        if not form.is_valid():
            error_text = '; '.join(
                [f"{field}: {','.join(errors)}" for field, errors in form.errors.items()]
            )
            return None, f'{idx}行目: {error_text}'

        partner_name = row['partner_name']
        email = row['email']
        key = (request.user.tenant_id, partner_name, email)

        if key in existing:
            return None, f'{idx}行目: tenant_id + partner_name + email "{partner_name}, {email}" は既に存在します。'
        existing.add(key)

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
        rec.partner_type,
        rec.contact_name,
        rec.email,
        rec.tel_number,
        rec.postal_code,
        rec.state,
        rec.city,
        rec.address,
        rec.address2
    ]


def filter_data(request, queryset):
    g = request.GET

    # キーワード検索（全体横断）
    keyword = g.get('search_keyword', '').strip()
    if keyword:
        queryset = queryset.filter(
            Q(partner_name__icontains=keyword)
            | Q(partner_name_kana__icontains=keyword)
            | Q(contact_name__icontains=keyword)
            | Q(email__icontains=keyword)
            | Q(tel_number__icontains=keyword)
            | Q(state__icontains=keyword)
            | Q(city__icontains=keyword)
            | Q(address__icontains=keyword)
            | Q(address2__icontains=keyword)
        )
        
    # 取引先区分のkey, valの辞書を作ってキーワード検索
    type_display_map = dict(Partner._meta.get_field('partner_type').choices)
    matched_types = [code for code, label in type_display_map.items() if keyword in label]
    if matched_types:
        queryset = queryset | Partner.objects.filter(partner_type__in=matched_types)

    # 詳細検索（個別フィールド）
    if g.get('search_partner_name'):
        queryset = queryset.filter(partner_name__icontains=g['search_partner_name'])
    if g.get('search_contact_name'):
        queryset = queryset.filter(contact_name__icontains=g['search_contact_name'])
    if g.get('search_email'):
        queryset = queryset.filter(email__icontains=g['search_email'])
    if g.get('search_tel_number'):
        queryset = queryset.filter(tel_number__icontains=g['search_tel_number'])
    if g.get('search_address'):
        s = g['search_address']
        queryset = queryset.filter(Q(state__icontains=s) | Q(city__icontains=s) | Q(address__icontains=s) | Q(address2__icontains=s))

    # 区分検索
    if g.get('search_partner_type'):
        queryset = queryset.filter(partner_type=g['search_partner_type'])

    return queryset


def set_message(request, action, partner_name):
    '''CRUD後の統一メッセージ'''
    messages.success(request, f'取引先「{partner_name}」を{action}しました。')
