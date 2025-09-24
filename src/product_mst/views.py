from django.views import generic
from django.urls import reverse_lazy
from .models import Product, ProductCategory
from .form import ProductForm
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse

# CSV/Excel の共通出力カラム定義
# アプリ固有のカラムに加え、共通カラムも連結
DATA_COLUMNS = ['product_cd', 'product_nm', 'start_date', 'end_date', 'product_category', 'price', 'description'] + Common.COMMON_DATA_COLUMNS

# -----------------------------
# Product CRUD
# -----------------------------

class ProductListView(generic.ListView):
    '''
    Product 一覧
    '''
    model = Product
    template_name = 'product_mst/product_list_modal.html'
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


class ProductDetailView(generic.DetailView):
    '''
    Product 詳細
    '''
    model = Product
    template_name = 'product_mst/product_detail.html'
    context_object_name = 'product'


class ProductCreateView(generic.CreateView):
    '''
    Product 作成
    '''
    model = Product
    form_class = ProductForm
    template_name = 'product_mst/product_edit.html'
    success_url = reverse_lazy('product_mst:product_list_modal')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = False
        return context

    def form_valid(self, form):
        form.instance.create_user = self.request.user
        form.instance.update_user = self.request.user
        return super().form_valid(form)


class ProductUpdateView(generic.UpdateView):
    '''
    Product 更新
    '''
    model = Product
    form_class = ProductForm
    template_name = 'product_mst/product_edit.html'
    success_url = reverse_lazy('product_mst:product_list_modal')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        form.instance.update_user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'商品「{form.instance.product_nm}」を更新しました。')
        return response


class ProductDeleteView(generic.DeleteView):
    '''
    Product 削除
    - 論理削除したい場合は DeleteView を使わずに UpdateView 内で is_deleted フラグを立てる
    '''
    model = Product
    template_name = 'product_mst/product_confirm_delete.html'
    success_url = reverse_lazy('product_mst:product_list_modal')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # 論理削除
        self.object.is_deleted = True
        self.object.update_user = self.request.user
        self.object.save()
        messages.success(self.request, f'商品「{self.object.product_nm}」を削除しました。')
        return super().delete(request, *args, **kwargs)
    
class ProductCreateModalView(ProductCreateView):
    template_name = "product_mst/product_form.html"

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        html = render_to_string(
            self.template_name,
            {
                "form": form,
                "form_action": reverse("product_mst:product_create_modal"),
                "modal_title": "商品新規登録",
            },
            request
        )
        return JsonResponse({"success": True, "html": html})

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.create_user = self.request.user
        self.object.update_user = self.request.user
        self.object.save()
        messages.success(self.request, f'商品「{self.object.product_nm}」を登録しました。')
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html = render_to_string(self.template_name, {"form": form}, self.request)
            return JsonResponse({"success": False, "html": html})
        return super().form_invalid(form)


class ProductUpdateModalView(ProductUpdateView):
    template_name = "product_mst/product_form.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        html = render_to_string(
            self.template_name,
            {
                "form": form,
                "form_action": reverse(
                    "product_mst:product_update_modal", kwargs={"pk": self.object.pk}
                ),
                "modal_title": f"商品更新: {self.object.product_nm}",
            },
            request
        )
        return JsonResponse({"success": True, "html": html})

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.update_user = self.request.user
        self.object.save()
        messages.success(self.request, f'商品「{self.object.product_nm}」を更新しました。')
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html = render_to_string(self.template_name, {"form": form}, self.request)
            return JsonResponse({"success": False, "html": html})
        return super().form_invalid(form)


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


from datetime import datetime

class ImportCSV(CSVImportBaseView):
    '''
    商品マスタの CSV インポート
    '''
    expected_headers = DATA_COLUMNS
    model_class = Product
    unique_field = 'product_cd'

    def validate_row(self, row, idx, existing, request):
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


def get_row(rec):
    '''
    共通の出力行生成処理
    - CSV/Excel エクスポートで共通利用
    '''
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
    '''
    共通検索処理
    - 検索キーワードを product_cd / product_nm に部分一致で適用
    '''
    keyword = request.GET.get('search') or ''
    if keyword:
        query_set = query_set.filter(
            Q(product_cd__icontains=keyword) | Q(product_nm__icontains=keyword)
        )
    return query_set
