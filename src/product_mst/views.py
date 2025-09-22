from django.views import generic
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product, ProductCategory
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView
from django.db.models import Q

# CSV/Excel の共通出力カラム定義
# アプリ固有のカラムに加え、共通カラムも連結
DATA_COLUMNS = ['product_cd', 'product_nm', 'product_category', 'description', 'price'] + Common.COMMON_DATA_COLUMNS

# -----------------------------
# Product CRUD
# -----------------------------

class ProductListView(LoginRequiredMixin, generic.ListView):
    '''
    Product 一覧
    '''
    model = Product
    template_name = 'product/product_list.html'
    context_object_name = 'products'
    paginate_by = 20


    def get_queryset(self):
        queryset = Product.objects.filter(is_deleted=False)

        search = self.request.GET.get('search')
        category = self.request.GET.get('search_product_category')

        if search:
            queryset = queryset.filter(
                Q(product_cd__icontains=search) |
                Q(product_nm__icontains=search) |
                Q(description__icontains=search)
            )

        if category:
            queryset = queryset.filter(product_category_id=category)

        return queryset.order_by('product_cd')
    
    def get_context_data(self, **kwarg):
        '''
        テンプレートに渡す追加コンテキストを設定
        - 検索ワードやカテゴリ一覧をセット
        - ページネーション情報を付加
        - 入力フォームを設定
        '''
        context = super().get_context_data(**kwarg)
        context['search'] = self.request.GET.get('search') or ''
        context['search_product_category'] = self.request.GET.get('search_product_category') or ''
        context['categories'] = ProductCategory.objects.filter(is_deleted=False).order_by('id')
        context = Common.set_pagination(context, self.request.GET.urlencode())
        return context


class ProductDetailView(LoginRequiredMixin, generic.DetailView):
    '''
    Product 詳細
    '''
    model = Product
    template_name = 'product/product_detail.html'
    context_object_name = 'product'


class ProductCreateView(LoginRequiredMixin, generic.CreateView):
    '''
    Product 作成
    '''
    model = Product
    fields = ['product_cd', 'product_nm', 'category', 'description', 'price', 'start_date', 'end_date']
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product:product_list')

    def form_valid(self, form):
        form.instance.create_user = self.request.user
        form.instance.update_user = self.request.user
        return super().form_valid(form)


class ProductUpdateView(LoginRequiredMixin, generic.UpdateView):
    '''
    Product 更新
    '''
    model = Product
    fields = ['product_cd', 'product_nm', 'category', 'description', 'price', 'start_date', 'end_date', 'is_deleted']
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product:product_list')

    def form_valid(self, form):
        form.instance.update_user = self.request.user
        return super().form_valid(form)


class ProductDeleteView(LoginRequiredMixin, generic.DeleteView):
    '''
    Product 削除
    - 論理削除したい場合は DeleteView を使わずに UpdateView 内で is_deleted フラグを立てる
    '''
    model = Product
    template_name = 'product/product_confirm_delete.html'
    success_url = reverse_lazy('product:product_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # 論理削除
        self.object.is_deleted = True
        self.object.update_user = self.request.user
        self.object.save()
        return super().delete(request, *args, **kwargs)

class ExportExcel(ExcelExportBaseView):
    '''
    商品マスタの Excel 出力
    - 共通の get_row を利用して1行を生成
    - 検索条件を適用したデータを出力
    '''
    model_class = Product
    filename_prefix = 'product_mst'
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return search_data(request=request, query_set=qs)

    def row(self, rec):
        return get_row(rec=rec)


class ExportCSV(CSVExportBaseView):
    '''
    商品マスタの CSV 出力
    - 共通の get_row を利用して1行を生成
    - 検索条件を適用したデータを出力
    '''
    model_class = Product
    filename_prefix = 'product_mst'
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return search_data(request=request, query_set=qs)

    def row(self, rec):
        return get_row(rec=rec)


class ImportCSV(CSVImportBaseView):
    '''
    商品マスタの CSV インポート
    - ヘッダ検証と行ごとのバリデーションを実施
    - 正常データを一括登録する
    '''
    expected_headers = DATA_COLUMNS
    model_class = Product
    unique_field = 'product_cd'

    def validate_row(self, row, idx, existing, request):
        '''
        CSVの1行をバリデーションし、問題なければ product オブジェクトを返す
        - product_cd の必須/重複チェック
        - category の外部参照チェック
        - price を数値に変換
        '''
        product_cd = row.get('product_cd')
        if not product_cd:
            return None, f'{idx}行目: product_cd が空です'
        if product_cd in existing:
            return None, f'{idx}行目: product_cd "{product_cd}" は既に存在します'

        category_name = row.get('category')
        try:
            category = ProductCategory.objects.get(category=category_name)
        except ProductCategory.DoesNotExist:
            return None, f'{idx}行目: category "{category_name}" が存在しません'

        try:
            price = int(price) if price else 0
        except ValueError:
            return None, f'{idx}行目: price "{price}" は数値である必要があります'

        obj = Product(
            product_cd=product_cd,
            product_nm=row.get('product_nm'),
            category=category,
            description=row.get('description') or '',
            price=int(price) if price else 0,
            update_user=request.user
        )
        return obj, None
    

def get_row(rec):
    '''
    共通の出力行生成処理
    - CSV/Excel エクスポートで共通利用
    '''
    return [
        rec.product_cd,
        rec.product_nm,
        rec.product_category.product_category_nm if rec.product_category else '',
        rec.description,
        rec.price
    ] + Common.get_common_columns(rec=rec)
    
def search_data(request, query_set):
    '''
    共通検索処理
    - 検索キーワードを item_cd / item_nm に部分一致で適用
    '''
    keyword = request.GET.get('search') or ''
    if keyword:
        query_set = query_set.filter(
            Q(product_cd__icontains=keyword) | Q(product_nm__icontains=keyword)
        )
    return query_set
