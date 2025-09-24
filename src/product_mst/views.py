from django.views import generic
from django.urls import reverse_lazy, reverse
from .models import Product, ProductCategory
from .form import ProductForm
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from datetime import datetime

# CSV/Excel の共通出力カラム定義
# アプリ固有のカラムに加え、共通カラムも連結
DATA_COLUMNS = [
    'product_cd', 'product_nm', 'start_date', 'end_date',
    'product_category', 'price', 'description'
] + Common.COMMON_DATA_COLUMNS


# -----------------------------
# Product CRUD (通常画面)
# -----------------------------

class ProductListView(generic.ListView):
    """
    商品一覧画面
    - 検索条件（キーワード/カテゴリ）に対応
    - ページネーション対応
    """
    model = Product
    template_name = 'product_mst/product_list_modal.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        """検索条件を反映したクエリセットを返す"""
        queryset = Product.objects.filter(is_deleted=False)

        search = self.request.GET.get('search')
        category = self.request.GET.get('search_product_category')

        # キーワード検索
        if search:
            queryset = queryset.filter(
                Q(product_cd__icontains=search) |
                Q(product_nm__icontains=search) |
                Q(description__icontains=search)
            )

        # カテゴリ検索
        if category:
            queryset = queryset.filter(product_category_id=category)

        return queryset.order_by('product_cd')
    
    def get_context_data(self, **kwarg):
        """
        テンプレートに渡す追加コンテキスト
        - 検索条件を保持
        - カテゴリ一覧を提供
        - ページネーション情報を追加
        """
        context = super().get_context_data(**kwarg)
        context['search'] = self.request.GET.get('search') or ''
        context['search_product_category'] = self.request.GET.get('search_product_category') or ''
        context['categories'] = ProductCategory.objects.filter(is_deleted=False).order_by('id')
        context = Common.set_pagination(context, self.request.GET.urlencode())
        return context


class ProductDetailView(generic.DetailView):
    """商品詳細画面"""
    model = Product
    template_name = 'product_mst/product_detail.html'
    context_object_name = 'product'


class ProductCreateView(generic.CreateView):
    """
    商品登録画面（通常遷移版）
    """
    model = Product
    form_class = ProductForm
    template_name = 'product_mst/product_edit.html'
    success_url = reverse_lazy('product_mst:product_list')
    
    def get_context_data(self, **kwargs):
        """新規登録フラグを追加（テンプレート分岐用）"""
        context = super().get_context_data(**kwargs)
        context['is_update'] = False
        return context

    def form_valid(self, form):
        """作成者・更新者を設定して保存"""
        form.instance.create_user = self.request.user
        form.instance.update_user = self.request.user
        return super().form_valid(form)


class ProductUpdateView(generic.UpdateView):
    """
    商品更新画面（通常遷移版）
    """
    model = Product
    form_class = ProductForm
    template_name = 'product_mst/product_edit.html'
    success_url = reverse_lazy('product_mst:product_list')
    
    def get_context_data(self, **kwargs):
        """更新フラグを追加（テンプレート分岐用）"""
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        """更新処理とフラッシュメッセージ"""
        form.instance.update_user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'商品「{form.instance.product_nm}」を更新しました。')
        return response


class ProductDeleteView(generic.DeleteView):
    """
    商品削除画面
    - 論理削除として is_deleted フラグを立てる
    """
    model = Product
    template_name = 'product_mst/product_confirm_delete.html'
    success_url = reverse_lazy('product_mst:product_list')

    def delete(self, request, *args, **kwargs):
        """削除時に is_deleted フラグを立てる"""
        self.object = self.get_object()
        self.object.is_deleted = True
        self.object.update_user = self.request.user
        self.object.save()
        messages.success(self.request, f'商品「{self.object.product_nm}」を削除しました。')
        return super().delete(request, *args, **kwargs)


# -----------------------------
# Product CRUD (モーダル画面)
# -----------------------------

class ProductCreateModalView(ProductCreateView):
    """
    商品登録モーダル版
    - GET: 部分テンプレートを返す（Ajax）
    - POST: Ajaxで登録処理
    """
    template_name = 'product_mst/product_form.html'

    def get(self, request, *args, **kwargs):
        """モーダルフォームHTMLを返す"""
        form = self.get_form()
        html = render_to_string(
            self.template_name,
            {
                'form': form,
                'form_action': reverse('product_mst:product_create_modal'),
                'modal_title': '商品新規登録',
            },
            request
        )
        return JsonResponse({'success': True, 'html': html})

    def form_valid(self, form):
        """登録処理（Ajax対応）"""
        self.object = form.save(commit=False)
        self.object.create_user = self.request.user
        self.object.update_user = self.request.user
        self.object.save()
        messages.success(self.request, f'商品「{self.object.product_nm}」を登録しました。')
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return super().form_valid(form)

    def form_invalid(self, form):
        """バリデーションエラー時（Ajax対応）"""
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, {'form': form}, self.request)
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)


class ProductUpdateModalView(ProductUpdateView):
    """
    商品更新モーダル版
    - GET: 部分テンプレートを返す（Ajax）
    - POST: Ajaxで更新処理
    """
    template_name = 'product_mst/product_form.html'

    def get(self, request, *args, **kwargs):
        """モーダルフォームHTMLを返す"""
        self.object = self.get_object()
        form = self.get_form()
        html = render_to_string(
            self.template_name,
            {
                'form': form,
                'form_action': reverse('product_mst:product_update_modal', kwargs={'pk': self.object.pk}),
                'modal_title': f'商品更新: {self.object.product_nm}',
            },
            request
        )
        return JsonResponse({'success': True, 'html': html})

    def form_valid(self, form):
        """更新処理（Ajax対応）"""
        self.object = form.save(commit=False)
        self.object.update_user = self.request.user
        self.object.save()
        messages.success(self.request, f'商品「{self.object.product_nm}」を更新しました。')
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return super().form_valid(form)

    def form_invalid(self, form):
        """バリデーションエラー時（Ajax対応）"""
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, {'form': form}, self.request)
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)


# -----------------------------
# Export / Import
# -----------------------------

class ExportExcel(ExcelExportBaseView):
    """
    商品マスタのExcel出力
    - 共通の get_row を利用
    - 検索条件を適用
    """
    model_class = Product
    filename_prefix = 'product_mst'
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        """検索条件を適用したクエリセットを返す"""
        qs = super().get_queryset(request)
        return search_data(request=request, query_set=qs)

    def row(self, rec):
        """1行分のデータを返す"""
        return get_row(rec=rec)


class ExportCSV(CSVExportBaseView):
    """
    商品マスタのCSV出力
    - 共通の get_row を利用
    - 検索条件を適用
    """
    model_class = Product
    filename_prefix = 'product_mst'
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        """検索条件を適用したクエリセットを返す"""
        qs = super().get_queryset(request)
        return search_data(request=request, query_set=qs)

    def row(self, rec):
        """1行分のデータを返す"""
        return get_row(rec=rec)


class ImportCSV(CSVImportBaseView):
    """
    商品マスタのCSVインポート
    - ヘッダ検証と1行ごとのバリデーション
    - 正常データをProductオブジェクトに変換
    """
    expected_headers = DATA_COLUMNS
    model_class = Product
    unique_field = 'product_cd'

    def validate_row(self, row, idx, existing, request):
        """1行ごとのバリデーション処理"""
        product_cd = row.get('product_cd')
        if not product_cd:
            return None, f'{idx}行目: product_cd が空です'
        if product_cd in existing:
            return None, f'{idx}行目: product_cd "{product_cd}" は既に存在します'

        # カテゴリの変換
        category_name = row.get('product_category')
        try:
            category = ProductCategory.objects.get(product_category_nm=category_name)
        except ProductCategory.DoesNotExist:
            return None, f'{idx}行目: product_category "{category_name}" が存在しません'

        # 価格の変換
        price_val = row.get('price')
        try:
            price_val = int(price_val) if price_val else 0
        except ValueError:
            return None, f'{idx}行目: price "{price_val}" は数値である必要があります'

        # 適用開始日 / 適用終了日の変換
        start_date_str = row.get('start_date')
        end_date_str   = row.get('end_date')
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
        except ValueError:
            return None, f'{idx}行目: start_date "{start_date_str}" は YYYY-MM-DD 形式で指定してください'

        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
        except ValueError:
            return None, f'{idx}行目: end_date "{end_date_str}" は YYYY-MM-DD 形式で指定してください'

        # Product オブジェクト生成
        obj = Product(
            product_cd=product_cd,
            product_nm=row.get('product_nm'),
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
    """CSV/Excel出力用: 1行分のリストを返す"""
    return [
        rec.product_cd,
        rec.product_nm,
        rec.start_date,
        rec.end_date,
        rec.product_category.product_category_nm if rec.product_category else '',
        rec.price,
        rec.description,
    ] + Common.get_common_columns(rec=rec)
    

def search_data(request, query_set):
    """共通検索処理: CSV/Excel出力時に利用"""
    keyword = request.GET.get('search') or ''
    if keyword:
        query_set = query_set.filter(
            Q(product_cd__icontains=keyword) | Q(product_nm__icontains=keyword)
        )
    return query_set
