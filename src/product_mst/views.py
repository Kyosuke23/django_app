from django.views import generic
from django.urls import reverse_lazy, reverse
from .models import Product, ProductCategory
from .form import ProductSearchForm, ProductForm, ProductCategoryForm
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView, PrivilegeRequiredMixin
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy

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
class ProductListView(generic.ListView):
    '''
    商品一覧画面
    - 検索条件（キーワード/カテゴリ）に対応
    - ページネーション対応
    '''
    model = Product
    template_name = 'product_mst/list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        req = self.request
        form = ProductSearchForm(req.GET or None)
        
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
        context['form'] = ProductSearchForm(self.request.GET or None)
        context['product_category_form'] = ProductCategoryForm(self.request.GET or None)
        context = Common.set_pagination(context, self.request.GET.urlencode())
        return context


class ProductCreateView(PrivilegeRequiredMixin, generic.CreateView):
    '''
    商品登録
    - GET: 部分テンプレートを返す（Ajax）
    - POST: Ajaxで登録処理
    '''
    model = Product
    form_class = ProductForm
    template_name = 'product_mst/form.html'

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        html = render_to_string(
            self.template_name,
            {
                'form': form,
                'form_action': reverse('product_mst:create'),
                'modal_title': '商品新規登録',
            },
            request
        )
        return JsonResponse({'success': True, 'html': html})

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
                    'form': form,
                    'form_action': reverse('product_mst:create'),
                    'modal_title': '商品新規登録',
                },
                self.request
            )
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)


class ProductUpdateView(PrivilegeRequiredMixin, generic.UpdateView):
    '''
    商品更新
    - GET: 部分テンプレートを返す（Ajax）
    - POST: Ajaxで更新処理
    '''
    model = Product
    form_class = ProductForm
    template_name = 'product_mst/form.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(instance=self.object)
        html = render_to_string(
            self.template_name,
            {
                'form': form,
                'form_action': reverse('product_mst:update', kwargs={'pk': self.object.pk}),
                'modal_title': f'商品更新: {self.object.product_name}',
            },
            request
        )
        return JsonResponse({'success': True, 'html': html})

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            self.object = form.save(commit=False)
            self.object.update_user = self.request.user
            self.object.save()
            set_message(self.request, '更新', self.object.product_name)
            return JsonResponse({'success': True})
        else:
            html = render_to_string(
                self.template_name,
                {
                    'form': form,
                    'form_action': reverse('product_mst:update', kwargs={'pk': self.object.pk}),
                    'modal_title': f'商品更新: {self.object.product_name}',
                },
                request
            )
            return JsonResponse({'success': False, 'html': html})


class ProductDeleteView(PrivilegeRequiredMixin, generic.View):
    '''
    商品削除処理
    - 物理削除
    '''
    template_name = 'product_mst/confirm_delete.html'
    success_url = reverse_lazy('product_mst:list')

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(Product, pk=kwargs['pk'])
        obj.delete()
        set_message(self.request, '削除', obj.product_name)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
    
    
class ProductBulkDeleteView(PrivilegeRequiredMixin, generic.View):
    '''
    一括削除処理
    - 物理削除
    '''
    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('ids')
        if ids:
            Product.objects.filter(id__in=ids).delete()
            return JsonResponse({'message': f'{len(ids)}件削除しました'})
        else:
            messages.warning(request, '削除対象が選択されていません')
        return redirect('product_mst:list')
    
    
class ProductCategoryManageView(generic.FormView):
    template_name = 'product_mst/category_mst.html'
    form_class = ProductCategoryForm
    success_url = reverse_lazy('product_mst:category_manage')
    
    def post(self, request, *args, **kwargs):
        '''カテゴリ名がnullでもバリデーションを通すための処理'''
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
        selected = form.cleaned_data.get('selected_category')
        name = form.cleaned_data.get('product_category_name')

        if action == 'save':
            if not name:
                messages.warning(req, 'カテゴリ名を入力してください。')
            elif selected:
                selected.product_category_name = name
                selected.update_user = req.user
                selected.save(update_fields=['product_category_name', 'update_user', 'updated_at'])
                messages.success(req, f'カテゴリ「{name}」を更新しました。')
            else:
                ProductCategory.objects.create(product_category_name=name, tenant_id=req.user.tenant.id, create_user=req.user, update_user=req.user)
                messages.success(req, f'カテゴリ「{name}」を新規作成しました。')

        elif action == 'delete':
            if selected:
                selected.delete()
                messages.success(req, f'カテゴリ「{selected.product_category_name}」を削除しました。')
            else:
                messages.warning(req, '削除対象のカテゴリを選択してください。')

        return redirect(f"{reverse('product_mst:list')}?category_open=1")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context



#--------------------------
# Export / Import
#--------------------------
class ExportExcel(ExcelExportBaseView):
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


class ExportCSV(CSVExportBaseView):
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


class ImportCSV(CSVImportBaseView):
    '''
    商品マスタのCSVインポート
    - ヘッダ検証と1行ごとのバリデーション
    - 正常データをProductオブジェクトに変換
    '''
    expected_headers = list(HEADER_MAP.keys())
    model_class = Product
    unique_field = 'product_name'
    HEADER_MAP = HEADER_MAP

    def validate_row(self, row, idx, existing, request):
        data = row.copy()
        
        # ------------------------------------------------------
        # 商品カテゴリチェック
        # ------------------------------------------------------
        category_name = data.get('product_category')
        if category_name:
            try:
                category = ProductCategory.objects.get(
                    product_category_name=category_name,
                    tenant=request.user.tenant
                )
                data['product_category'] = category.id
            except ProductCategory.DoesNotExist:
                return None, f'{idx}行目: 商品カテゴリ「{category_name}」が存在しません'
        else:
            data['product_category'] = None
        
        # ------------------------------------------------------
        # Djangoフォームバリデーション
        # ------------------------------------------------------
        form = ProductForm(data=data)
        if not form.is_valid():
            error_text = '; '.join(
                [f"{field}: {','.join(errors)}" for field, errors in form.errors.items()]
            )
            return None, f'{idx}行目: {error_text}'

        # ------------------------------------------------------
        # 重複チェック（tenant + product_name）
        # ------------------------------------------------------
        product_name = data.get('product_name')
        key = (request.user.tenant_id, product_name)
        if key in existing:
            return None, f'{idx}行目: 商品名称「{product_name}」は既に存在します。'
        existing.add(key)
        
        # ------------------------------------------------------
        # Productオブジェクト作成
        # ------------------------------------------------------
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
            | Q(product_category__product_category_name__icontains=keyword)
        )

    if cleaned_data.get('search_product_name'):
        queryset = queryset.filter(product_name__icontains=cleaned_data['search_product_name'])
    if cleaned_data.get('search_category'):
        queryset = queryset.filter(product_category=cleaned_data['search_category'])
    if cleaned_data.get('search_unit'):
        queryset = queryset.filter(unit__icontains=cleaned_data['search_unit'])
    if cleaned_data.get('min_price') is not None:
        queryset = queryset.filter(unit_price__gte=cleaned_data['min_price'])
    if cleaned_data.get('max_price') is not None:
        queryset = queryset.filter(unit_price__lte=cleaned_data['max_price'])

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
