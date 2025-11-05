from django.views import generic
from django.db import transaction
from django.urls import reverse_lazy, reverse
from .models import Product, ProductCategory
from .form import ProductSearchForm, ProductForm, ProductCategoryForm
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView, PrivilegeRequiredMixin
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.template.loader import render_to_string
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin


# 出力カラム定義
HEADER_MAP = {
    '商品名': 'product_name',
    '商品カテゴリ': 'product_category',
    '単価': 'unit_price',
    '単位': 'unit',
    '説明': 'description',
}

# 出力ファイル名定義
FILENAME_PREFIX = 'product_mst'


#--------------------------
# Product CRUD
#--------------------------
class ProductListView(LoginRequiredMixin, generic.ListView):
    '''
    商品一覧画面
    - 検索条件（キーワード/カテゴリ）に対応
    - ページネーション対応
    '''
    model = Product
    template_name = 'product_mst/list.html'
    context_object_name = 'products'
    paginate_by = settings.DEFAULT_PAGE_SIZE

    def get_queryset(self):
        req = self.request
        form = ProductSearchForm(req.GET or None, user=req.user)

        # クエリセットを初期化（削除フラグ：False, 所属テナント限定）
        queryset = Product.objects.filter(is_deleted=False, tenant=req.user.tenant)

        # フォームが有効なら検索条件を反映
        if form.is_valid():
            queryset = filter_data(cleaned_data=form.cleaned_data, queryset=queryset)

        # 並び替え
        sort = form.cleaned_data.get('sort') if form.is_valid() else ''
        queryset = set_table_sort(queryset=queryset, sort=sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProductSearchForm(self.request.GET or None, user=self.request.user)
        context['manage_category_form'] = ProductCategoryForm(self.request.GET or None, user=self.request.user)
        context = Common.set_pagination(context, self.request.GET.urlencode())
        return context


class ProductCreateView(LoginRequiredMixin, PrivilegeRequiredMixin, generic.CreateView):
    '''
    商品登録
    - GET: 部分テンプレートを返す（Ajax）
    - POST: Ajaxで登録処理
    '''
    model = Product
    form_class = ProductForm
    template_name = 'product_mst/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        html = render_to_string(
            self.template_name,
            {
                'edit_form': form,
                'form_action': reverse('product_mst:create'),
                'modal_title': '商品: 新規登録',
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
        Common.save_data(selv=self, form=form, is_update=False)
        set_message(self.request, '登録', self.object.product_name)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(
                self.template_name,
                {
                    'edit_form': form,
                    'form_action': reverse('product_mst:create'),
                    'modal_title': '商品: 新規登録',
                },
                self.request
            )
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)


class ProductUpdateView(LoginRequiredMixin, PrivilegeRequiredMixin, generic.UpdateView):
    '''
    商品更新
    - GET: 部分テンプレートを返す（Ajax）
    - POST: Ajaxで更新処理
    '''
    model = Product
    form_class = ProductForm
    template_name = 'product_mst/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            messages.error(request, 'この商品は既に削除されています。')
            return JsonResponse({'success': False}, status=404)

        form = self.get_form()
        html = render_to_string(
            self.template_name,
            {
                'edit_form': form,
                'form_action': reverse('product_mst:update', kwargs={'pk': self.object.pk}),
                'modal_title': f'商品更新: {self.object.product_name}',
            },
            request
        )
        return JsonResponse({'success': True, 'html': html})

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                messages.error(request, 'この商品は既に削除されています。')
                return JsonResponse({'success': False}, status=404)

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        Common.save_data(selv=self, form=form, is_update=True)
        set_message(self.request, '更新', self.object.product_name)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            obj = getattr(self, 'object', None)
            modal_title = f'商品更新: {obj.product_name}' if obj else '商品更新'
            html = render_to_string(
                self.template_name,
                {
                    'edit_form': form,
                    'form_action': reverse(
                        'product_mst:update',
                        kwargs={'pk': obj.pk} if obj else {}
                    ),
                    'modal_title': modal_title,
                },
                self.request
            )
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)


class ProductDeleteView(LoginRequiredMixin, PrivilegeRequiredMixin, generic.View):
    '''
    商品削除処理
    - 物理削除
    '''
    template_name = 'product_mst/confirm_delete.html'
    success_url = reverse_lazy('product_mst:list')

    def post(self, request, *args, **kwargs):
        try:
            obj = get_object_or_404(Product, pk=kwargs['pk'])
        except Http404:
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                messages.error(request, 'この商品は既に削除されています。')
                return JsonResponse({'success': False}, status=404)
        obj.delete()
        set_message(self.request, '削除', obj.product_name)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})


class ProductBulkDeleteView(LoginRequiredMixin, PrivilegeRequiredMixin, generic.View):
    '''
    一括削除処理
    - 物理削除
    '''
    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('ids')

        if not ids:
            messages.warning(request, '削除対象が選択されていません。')
            return redirect('product_mst:list')

        try:
            with transaction.atomic():
                # 対象取得
                products = Product.objects.filter(id__in=ids)

                # 存在しないIDを検出
                found_ids = set(str(p.id) for p in products)
                missing_ids = set(ids) - found_ids

                if missing_ids:
                    messages.error(request, 'すでに削除されている商品が含まれています。')
                    return JsonResponse({'success': False}, status=404)

                # 物理削除実行
                deleted_count, _ = products.delete()

            return JsonResponse({'message': f'{deleted_count}件削除しました。'})

        except ValueError as e:
            # トランザクションは自動ロールバック
            messages.error(request, str(e))
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': str(e)}, status=400)
            return redirect('product_mst:list')

        except Exception:
            # 想定外エラー（DBエラーなど）
            messages.error(request, '削除処理中にエラーが発生しました。')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': '削除処理中にエラーが発生しました。'}, status=500)
            return redirect('product_mst:list')


class ProductCategoryManageView(LoginRequiredMixin, PrivilegeRequiredMixin, generic.FormView):
    template_name = 'product_mst/category_mst.html'
    form_class = ProductCategoryForm
    success_url = reverse_lazy('product_mst:category_manage')

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
        selected_id = req.POST.get('selected_category')
        name = form.cleaned_data.get('product_category_name')

        # カテゴリIDの存在チェック
        if selected_id:
            selected = ProductCategory.objects.filter(id=int(selected_id), tenant=req.user.tenant).first()
        else:
            selected = None

        # 保存処理
        if action == 'save':
            # 更新
            if selected:
                selected.product_category_name = name
                selected.update_user = req.user
                selected.save(update_fields=['product_category_name', 'update_user', 'updated_at'])
                messages.success(req, f'商品カテゴリ「{name}」を更新しました。')
            # 新規登録
            else:
                ProductCategory.objects.create(
                    product_category_name=name,
                    tenant=req.user.tenant,
                    create_user=req.user,
                    update_user=req.user,
                )
                messages.success(req, f'商品カテゴリ「{name}」を新規作成しました。')

        # 削除処理
        elif action == 'delete':
            # 使用中のチェック
            in_use = Product.objects.filter(
                product_category=selected,
                tenant=req.user.tenant,
                is_deleted=False
            ).exists()
            if in_use:
                messages.warning(req, f'商品カテゴリ「{selected.product_category_name}」は使用中のため、削除できません。')
                return redirect(f"{reverse('product_mst:list')}?category_open=1")

            # 削除処理
            if selected:
                selected.delete()
                messages.success(req, f'商品カテゴリ「{selected.product_category_name}」を削除しました。')
            else:
                messages.warning(req, '削除対象の商品カテゴリを選択してください。')
        return redirect(f"{reverse('product_mst:list')}?category_open=1")

    def form_invalid(self, form):
        """未入力などバリデーションエラー時のハンドリング"""
        if self.request.POST.get('action') == 'save':
            if 'selected_category' in form.errors:
                msg = form.errors['selected_category'][0]
            elif 'product_category_name' in form.errors:
                msg = form.errors['product_category_name'][0]
            else:
                msg = 'エラーが発生しました。'
            messages.error(self.request, msg)
        return redirect(f"{reverse('product_mst:list')}?category_open=1")


#--------------------------
# Export / Import
#--------------------------
class ExportExcel(LoginRequiredMixin, ExcelExportBaseView):
    '''
    商品マスタのExcel出力
    - 共通の get_row を利用
    - 検索条件を適用
    '''
    model_class = Product
    filename_prefix = FILENAME_PREFIX
    headers = list(HEADER_MAP.keys())

    def get_queryset(self, request):
        '''検索条件を適用したクエリセットを返す'''
        queryset = super().get_queryset(request)
        return filter_data(request=request, queryset=queryset).order_by('product_name')

    def row(self, rec):
        '''1行分のデータを返す'''
        return get_row(rec=rec)


class ExportCheckView(LoginRequiredMixin, generic.View):
    '''CSV出力前の件数チェック'''
    def get(self, request):
        form = ProductSearchForm(request.GET or None)
        queryset = Product.objects.filter(is_deleted=False, tenant=request.user.tenant)

        if form.is_valid():
            queryset = filter_data(cleaned_data=form.cleaned_data, queryset=queryset)

        count = queryset.count()
        if count > settings.MAX_EXPORT_ROWS:
            return JsonResponse({
                'warning': f'出力件数が上限（{settings.MAX_EXPORT_ROWS:,}件）を超えています。'
                           f'先頭{settings.MAX_EXPORT_ROWS:,}件のみを出力します。'
            })

        return JsonResponse({'ok': True})


class ExportCSV(LoginRequiredMixin, CSVExportBaseView):
    '''
    商品マスタのCSV出力
    - 共通の get_row を利用
    - 検索条件を適用
    '''
    model_class = Product
    filename_prefix = FILENAME_PREFIX
    headers = list(HEADER_MAP.keys())

    def get_queryset(self, request):
        form = ProductSearchForm(request.GET or None)

        # クエリセットを初期化（削除フラグ：False, 所属テナント限定）
        queryset = Product.objects.filter(is_deleted=False, tenant=request.user.tenant)

        # フォームが有効なら検索条件を反映
        if form.is_valid():
            queryset = filter_data(cleaned_data=form.cleaned_data, queryset=queryset)

        # 並び替え
        sort = form.cleaned_data.get('sort') if form.is_valid() else ''
        queryset = set_table_sort(queryset=queryset, sort=sort)

        return queryset

    def row(self, rec):
        '''1行分のデータを返す'''
        return get_row(rec=rec)


class ImportCSV(LoginRequiredMixin, PrivilegeRequiredMixin, CSVImportBaseView):
    '''
    商品マスタのCSVインポート
    - ヘッダ検証と1行ごとのバリデーション
    - 正常データをProductオブジェクトに変換
    '''
    expected_headers = list(HEADER_MAP.keys())
    model_class = Product
    unique_field = ('tenant_id', 'product_name')
    HEADER_MAP = HEADER_MAP

    def validate_row(self, row, idx, existing, request):
        data = row.copy()

        #---------------------------------------------------
        # 商品カテゴリチェック
        #---------------------------------------------------
        category_name = data.get('product_category')
        if category_name:
            try:
                category = ProductCategory.objects.get(
                    product_category_name=category_name,
                    tenant=request.user.tenant
                )
                data['product_category'] = category.id
            except ProductCategory.DoesNotExist:
                return None, f'{idx}行目: 商品カテゴリ「{category_name}」が存在しません。'
        else:
            data['product_category'] = None

        #---------------------------------------------------
        # Djangoフォームバリデーション
        #---------------------------------------------------
        form = ProductForm(data=data)
        if not form.is_valid():
            error_text = '; '.join(self._format_errors_with_verbose_name(form))
            return None, f'{idx}行目: {error_text}'

        #---------------------------------------------------
        # 重複チェック（tenant + product_name）
        #---------------------------------------------------
        product_name = data.get('product_name')
        key = (request.user.tenant_id, product_name)
        if key in existing:
            return None, f'{idx}行目: 商品「{product_name}」は既に存在します。'
        existing.add(key)

        #---------------------------------------------------
        # Productオブジェクト作成
        #---------------------------------------------------
        obj = form.save(commit=False)
        obj.tenant = request.user.tenant
        obj.create_user = request.user
        obj.update_user = request.user

        return obj, None


#--------------------------
# 共通関数
#--------------------------
def get_row(rec):
    '''CSV/Excel出力用: 1行分のリストを返す'''
    return [
        rec.product_name,
        rec.product_category.product_category_name if rec.product_category else '',
        rec.unit_price,
        rec.unit,
        rec.description,
    ]


def filter_data(cleaned_data, queryset):
    keyword = cleaned_data.get('search_keyword', '').strip()
    if keyword:
        queryset = queryset.filter(
            Q(product_name__icontains=keyword)
            | Q(description__icontains=keyword)
            | Q(unit__icontains=keyword)
            | Q(unit_price__icontains=keyword)
            | Q(product_category__product_category_name__icontains=keyword)
        )

    if cleaned_data.get('search_product_name'):
        queryset = queryset.filter(product_name__icontains=cleaned_data['search_product_name'])
    if cleaned_data.get('search_category'):
        queryset = queryset.filter(product_category=cleaned_data['search_category'])
    if cleaned_data.get('search_unit'):
        queryset = queryset.filter(unit__icontains=cleaned_data['search_unit'])
    if cleaned_data.get('search_unit_price_min') is not None:
        queryset = queryset.filter(unit_price__gte=cleaned_data['search_unit_price_min'])
    if cleaned_data.get('search_unit_price_max') is not None:
        queryset = queryset.filter(unit_price__lte=cleaned_data['search_unit_price_max'])

    return queryset

def set_table_sort(queryset, sort):
    '''
    クエリセットにソート順を設定
    '''
    if sort in [
        'product_name', '-product_name',
        'product_category__product_category_name', '-product_category__product_category_name',
        'unit_price', '-unit_price',
    ]:
        return queryset.order_by(sort)
    return queryset.order_by('id')

def set_message(request, action, product_name):
    '''CRUD後の統一メッセージ'''
    messages.success(request, f'商品「{product_name}」を{action}しました。')
