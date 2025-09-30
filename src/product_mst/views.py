from django.views import generic
from django.urls import reverse_lazy, reverse
from .models import Product, ProductCategory
from sales_order.models import SalesOrderDetail
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
    'product_name', 'start_date', 'end_date',
    'product_category', 'price', 'description'
] + Common.COMMON_DATA_COLUMNS

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
        '''検索条件を反映したクエリセットを返す'''
        query_set = Product.objects.filter(is_deleted=False, tenant=self.request.user.tenant)
        query_set = filter_data(request=self.request, query_set=query_set)
        return query_set.order_by('product_name')
    
    def get_context_data(self, **kwargs):
        '''
        テンプレートに渡す追加コンテキスト
        - 検索条件を保持
        - カテゴリ一覧を提供
        - ページネーション情報を追加
        '''
        context = super().get_context_data(**kwargs)
        context['search_keyword'] = self.request.GET.get('search_keyword') or ''
        context['search_product_category'] = self.request.GET.get('search_product_category') or ''
        context['categories'] = ProductCategory.objects.filter(is_deleted=False, tenant=self.request.user.tenant).order_by('id')
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
    """
    商品削除処理
    - POST: 実際に削除
    """
    template_name = 'product_mst/confirm_delete.html'
    success_url = reverse_lazy('product_mst:list')

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(Product, pk=kwargs['pk'])
        try:
            obj.delete()
            set_message(self.request, '削除', obj.product_name)
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
        except ProtectedError as e:
            return JsonResponse({
                'error': '使用中の商品は削除できません',
                'details': ''
            }, status=400)
    
    
    
class ProductBulkDeleteView(PrivilegeRequiredMixin, generic.View):
    ''' 一括削除処理 '''
    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('ids')
        if ids:
            try:
                Product.objects.filter(id__in=ids).delete()
                return JsonResponse({'message': f'{len(ids)}件削除しました'})
            except ProtectedError as e:
                # 削除できなかった商品を抽出（SalesOrderDetail → product を辿る）
                protected_products = set()
                for obj in e.protected_objects:
                    if isinstance(obj, SalesOrderDetail):
                        protected_products.add(obj.product)

                details = ', '.join(
                    f"{p.product_name}" for p in protected_products
                )
                return JsonResponse({
                    'error': '使用中の商品は削除できません',
                    'details': details or str
                }, status=400)
        else:
            messages.warning(request, '削除対象が選択されていません')
        return redirect('product_mst:list')


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
        qs = super().get_queryset(request)
        return filter_data(request=request, query_set=qs)

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
        qs = super().get_queryset(request)
        return filter_data(request=request, query_set=qs)

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
        price_val = row.get('price')
        try:
            price_val = int(price_val) if price_val else 0
        except ValueError:
            return None, f'{idx}行目: price "{price_val}" は数値である必要があります'

        # 適用開始日 / 適用終了日の変換
        start_date, err = Common.parse_date(value=row.get('start_date'), field_name='start_date', idx=idx)
        if err:
            return None, err
        end_date, err = Common.parse_date(value=row.get('end_date'), field_name='end_date', idx=idx)
        if err:
            return None, err
        
        # 適用開始日 / 適用終了日の整合性チェック
        if start_date and end_date and end_date < start_date:
            return None, f'{idx}行目: 適用終了日が適用開始日より前の日付です'

        # Product オブジェクト生成
        obj = Product(
            product_name=row.get('product_name'),
            product_category=category,
            description=row.get('description') or '',
            price=price_val,
            start_date=start_date,
            end_date=end_date,
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
        rec.start_date,
        rec.end_date,
        rec.product_category.product_category_name if rec.product_category else '',
        rec.price,
        rec.description,
    ] + Common.get_common_columns(rec=rec)
    

def filter_data(request, query_set):
    ''' 検索条件付与 '''
    keyword = request.GET.get('search_keyword') or ''
    category = request.GET.get('search_product_category') or ''
    if keyword:
        query_set = query_set.filter(
            Q(product_name__icontains=keyword)
        )
    if category:
        query_set = query_set.filter(product_category_id=category)
    return query_set

def set_message(request, action, product_name):
    '''CRUD後の統一メッセージ'''
    messages.success(request, f'商品「{product_name}」を{action}しました。')
