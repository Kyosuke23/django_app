from django.views import generic
from django.urls import reverse_lazy, reverse
from .models import Product, ProductCategory
from .form import ProductForm
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView, PrivilegeRequiredMixin
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import redirect
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy


# CSV/Excel の共通出力カラム定義
# アプリ固有のカラムに加え、共通カラムも連結
DATA_COLUMNS = [
    'product_name', 'product_category', 'unit_price', 'description'
]
FILENAME_PREFIX = 'product_mst'


# -----------------------------
# Product CRUD
# -----------------------------
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
        '''
        検索条件を反映したクエリセットを返す
        '''
        # クエリセットを初期化（削除フラグ：False, 所属テナント限定）
        req = self.request
        queryset = Product.objects.filter(is_deleted=False, tenant=req.user.tenant)
        
        # テンプレートの検索条件を適用
        queryset = filter_data(request=req, queryset=queryset)

        # クエリセット返却
        return queryset.order_by('product_name')
    
    def get_context_data(self, **kwargs):
        '''
        テンプレートに渡す追加コンテキスト
        - 検索条件を保持
        - カテゴリ一覧を提供
        - ページネーション情報を追加
        '''
        # コンテキスト取得
        context = super().get_context_data(**kwargs)
        g = self.request.GET
        
        # 検索フォームの入力値保持
        context['search_product_name'] = g.get('search_product_name') or ''
        context['search_product_category'] = g.get('search_product_category') or ''
        context['search_unit_price_min'] = g.get('search_unit_price_min') or ''
        context['search_unit_price_max'] = g.get('search_unit_price_max') or ''
        context['categories'] = ProductCategory.objects.filter(tenant=self.request.user.tenant)
        
        # ページネーション保持
        context = Common.set_pagination(context, self.request.GET.urlencode())
        
        # コンテキストの返却
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


class ProductCategoryEditView(PrivilegeRequiredMixin, generic.View):
    '''
    商品カテゴリ編集処理
    - 登録・編集・削除
    '''
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        category_id = request.POST.get('category_id')
        name = request.POST.get('category_name')

        # 削除処理
        if action == 'delete':
            if not category_id:
                messages.error(request, '削除対象を選択してください')
                return redirect('product_mst:list')
            category = get_object_or_404(ProductCategory, pk=category_id, tenant=request.user.tenant)
            try:
                cname = category.product_category_name
                category.delete()
                messages.success(request, f'カテゴリ「{cname}」を削除しました')
            except ProtectedError:
                messages.error(request, f'使用中の商品は削除できません')
            return redirect(f"{reverse('product_mst:list')}?category_open=1")

        # 入力値チェック
        if not name:
            messages.error(request, 'カテゴリ名を入力してください')
            return redirect(f"{reverse('product_mst:list')}?category_open=1")
        
        # 既存チェック
        exists = ProductCategory.objects.filter(
            tenant=request.user.tenant,
            product_category_name=name
        )
        if category_id:
            exists = exists.exclude(pk=category_id)
        if exists.exists():
            messages.error(request, f'カテゴリ「{name}」は既に存在します')
            return redirect(f"{reverse('product_mst:list')}?category_open=1")

        # 更新処理
        if category_id:
            category = get_object_or_404(ProductCategory, pk=category_id, tenant=request.user.tenant)
            category.product_category_name = name
            category.update_user = request.user
            category.save()
            messages.success(request, f'カテゴリ「{name}」を更新しました')
        # 登録処理
        else:
            ProductCategory.objects.create(
                product_category_name=name,
                tenant=request.user.tenant,
                create_user=request.user,
                update_user=request.user
            )
            messages.success(request, f'カテゴリ「{name}」を登録しました')

        return redirect(f"{reverse('product_mst:list')}?category_open=1")


# -----------------------------
# Export / Import
# -----------------------------
class ExportExcel(ExcelExportBaseView):
    '''
    商品マスタのExcel出力
    - 共通の get_row を利用
    - 検索条件を適用
    '''
    model_class = Product
    filename_prefix = FILENAME_PREFIX
    headers = DATA_COLUMNS

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
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        '''検索条件を適用したクエリセットを返す'''
        queryset = super().get_queryset(request)
        return filter_data(request=request, queryset=queryset).order_by('product_name')

    def row(self, rec):
        '''1行分のデータを返す'''
        return get_row(rec=rec)


class ImportCSV(CSVImportBaseView):
    '''
    商品マスタのCSVインポート
    - ヘッダ検証と1行ごとのバリデーション
    - 正常データをProductオブジェクトに変換
    '''
    expected_headers = DATA_COLUMNS
    model_class = Product
    unique_field = 'product_name'

    def validate_row(self, row, idx, existing, request):
        '''1行ごとのバリデーション処理'''
        product_name = row.get('product_name')
        if not product_name:
            return None, f'{idx}行目: product_name が空です'
        if product_name in existing:
            return None, f'{idx}行目: product_name "" は既に存在します'

        # カテゴリの変換
        category_name = row.get('product_category')
        try:
            category = ProductCategory.objects.get(product_category_name=category_name)
        except ProductCategory.DoesNotExist:
            return None, f'{idx}行目: product_category "{category_name}" が存在しません'

        # 価格の変換
        unit_price_val = row.get('unit_price')
        try:
            unit_price_val = int(unit_price_val) if unit_price_val else 0
        except ValueError:
            return None, f'{idx}行目: unit_price "{unit_price_val}" は数値である必要があります'

        # Product オブジェクト生成
        obj = Product(
            product_name=row.get('product_name'),
            product_category=category,
            description=row.get('description') or '',
            unit_price=unit_price_val,
            create_user=request.user,
            update_user=request.user
        )
        return obj, None


# -----------------------------
# 共通関数
# -----------------------------
def get_row(rec):
    '''CSV/Excel出力用: 1行分のリストを返す'''
    return [
        rec.product_name,
        rec.product_category.product_category_name if rec.product_category else '',
        rec.unit_price,
        rec.description,
    ]
    

def filter_data(request, queryset):
    g = request.GET

    ''' 検索条件付与 '''
    # リクエストから検索フォームの入力値を取得
    keyword = g.get('search_keyword') or ''
    product_name = g.get('search_product_name') or ''
    category = g.get('search_product_category') or ''
    unit_price_min = g.get('search_unit_price_min') or ''
    unit_price_max = g.get('search_unit_price_max') or ''
    
    # フィルタ実行
    if keyword:
        queryset = queryset.filter(
            Q(product_name__icontains=keyword)
            | Q(product_category__product_category_name__icontains=keyword)
        )
    if product_name:
        queryset = queryset.filter(Q(product_name__icontains=product_name))
    if category:
        queryset = queryset.filter(product_category_id=category)
    if unit_price_min:
        queryset = queryset.filter(unit_price__gte=unit_price_min)
    if unit_price_max:
        queryset = queryset.filter(unit_price__lte=unit_price_max)
    
    # バリデーション
    if unit_price_min and unit_price_max and int(unit_price_min) > int(unit_price_max):
        messages.error(request, '価格(下限)は価格(上限)以下を指定してください')
        queryset = queryset.none()

    # クエリセットの返却
    return queryset

def set_message(request, action, product_name):
    '''CRUD後の統一メッセージ'''
    messages.success(request, f'商品「{product_name}」を{action}しました。')
