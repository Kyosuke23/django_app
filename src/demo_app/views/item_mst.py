from django.views import generic
from ..views.base import CSVImportBaseView, CSVExportBaseView, ExcelExportBaseView
from ..models.item_mst import Item, Category
from ..form import ItemCreationForm
from django.urls import reverse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib import messages
from config.common import Common
from django.db.models import Q


# CSV/Excel の共通出力カラム定義
# アプリ固有のカラムに加え、共通カラムも連結
DATA_COLUMNS = ['item_cd', 'item_nm', 'category', 'description', 'price'] + Common.COMMON_DATA_COLUMNS


class ItemList(generic.ListView, generic.edit.ModelFormMixin):
    """
    アイテムマスタ一覧画面
    - 一覧表示・検索・ページネーションを提供
    """
    model = Item
    form_class = ItemCreationForm
    context_object_name = 'items'
    template_name = 'demo_app/item_mst/index.html'
    paginate_by = 50

    def get_queryset(self, **kwarg):
        """
        一覧用のクエリセットを返す
        - 論理削除されていないデータのみ対象
        - category を select_related で事前取得して N+1 を防止
        - 検索条件を適用
        """
        query_set = super().get_queryset(**kwarg).filter(is_deleted=False).select_related('category')
        return search_data(request=self.request, query_set=query_set)

    def get_context_data(self, **kwarg):
        """
        テンプレートに渡す追加コンテキストを設定
        - 検索ワードやカテゴリ一覧をセット
        - ページネーション情報を付加
        - 入力フォームを設定
        """
        context = super().get_context_data(**kwarg)
        context['search'] = self.request.GET.get('search') or ''
        context['category_list'] = Category.objects.order_by('id')
        context = Common.set_pagination(context, self.request.GET.urlencode())
        context['form'] = self.get_form()
        return context
    
    def get(self, request, *args, **kwargs):
        """
        GETリクエスト処理
        - object をリセットして一覧を表示
        """
        self.object = None
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        POSTリクエスト処理
        - フォーム送信時にバリデーションを実行
        """
        self.object = None
        self.object_list = self.get_queryset()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        

def search_data(request, query_set):
    """
    共通検索処理
    - 検索キーワードを item_cd / item_nm に部分一致で適用
    """
    keyword = request.GET.get('search') or ''
    if keyword:
        query_set = query_set.filter(
            Q(item_cd__icontains=keyword) | Q(item_nm__icontains=keyword)
        )
    return query_set
        
    
class ItemCreate(generic.edit.CreateView):
    """
    アイテムマスタの新規登録処理
    - フォームをバリデーションし、作成者・更新者を設定して登録
    - 結果は JSON で返却
    """
    model = Item
    form_class = ItemCreationForm
    context_object_name = 'item'
    template_name = 'demo_app/item_mst/create.html'
    
    def get_success_url(self):
        return reverse('demo_app:item_mst_index')
    
    def post(self, request, *args, **kwargs):
        self.object = None
        self.object_list = self.get_queryset()
        form = self.get_form()
        if form.is_valid():
            post = form.save(commit=False)
            post.create_user = self.request.user
            post.update_user = self.request.user
            post.save()
            messages.success(request, '登録が完了しました')
        return JsonResponse(
            {
                'errors': form.errors,
                'success_url': self.get_success_url()
            },
            json_dumps_params={'ensure_ascii': False}
        )


class ItemUpdate(generic.edit.UpdateView):
    """
    アイテムマスタの更新処理
    - 指定された PK のデータを更新
    - update_user をログインユーザーに設定
    - 結果は JSON で返却
    """
    model = Item
    form_class = ItemCreationForm
    context_object_name = 'item'
    template_name = 'demo_app/item_mst/edit.html'
    
    def get_success_url(self):
        return reverse('demo_app:item_mst_index')
    
    def post(self, request, *args, **kwargs):
        item = get_object_or_404(Item, pk=request.POST['pk'])
        form = ItemCreationForm(request.POST, instance=item)
        if form.is_valid():
            post = form.save(commit=False)
            post.update_user = self.request.user
            post.save()
            messages.success(request, '更新が完了しました')
        return JsonResponse(
            {
                'errors': form.errors,
                'success_url': self.get_success_url()
            },
            json_dumps_params={'ensure_ascii': False}
        )
    

class ItemDelete(generic.edit.DeleteView):
    """
    アイテムマスタの削除処理
    - 指定された PK を物理削除
    - 結果は JSON で返却
    """
    model = Item
    template_name = 'demo_app/item_mst/delete.html'

    def get_success_url(self):
        return reverse('demo_app:item_mst_index')

    def post(self, request, *args, **kwargs):
        item = get_object_or_404(Item, pk=request.POST['pk'])
        item.delete()
        messages.success(request, '削除が完了しました')
        return JsonResponse(
            {
                'errors': {},
                'success_url': self.get_success_url()
            },
            json_dumps_params={'ensure_ascii': False}
        )


class ItemExportExcel(ExcelExportBaseView):
    """
    アイテムマスタの Excel 出力
    - 共通の get_row を利用して1行を生成
    - 検索条件を適用したデータを出力
    """
    model_class = Item
    filename_prefix = 'item_mst'
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return search_data(request=request, query_set=qs)

    def row(self, rec):
        return get_row(rec=rec)


class ItemExportCSV(CSVExportBaseView):
    """
    アイテムマスタの CSV 出力
    - 共通の get_row を利用して1行を生成
    - 検索条件を適用したデータを出力
    """
    model_class = Item
    filename_prefix = 'item_mst'
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return search_data(request=request, query_set=qs)

    def row(self, rec):
        return get_row(rec=rec)


class ItemImportCSV(CSVImportBaseView):
    """
    アイテムマスタの CSV インポート
    - ヘッダ検証と行ごとのバリデーションを実施
    - 正常データを一括登録する
    """
    expected_headers = DATA_COLUMNS
    model_class = Item
    unique_field = 'item_cd'

    def validate_row(self, row, idx, existing, request):
        """
        CSVの1行をバリデーションし、問題なければ Item オブジェクトを返す
        - item_cd の必須/重複チェック
        - category の外部参照チェック
        - price を数値に変換
        """
        item_cd = row.get('item_cd')
        if not item_cd:
            return None, f'{idx}行目: item_cd が空です'
        if item_cd in existing:
            return None, f'{idx}行目: item_cd "{item_cd}" は既に存在します'

        category_name = row.get('category')
        try:
            category = Category.objects.get(category=category_name)
        except Category.DoesNotExist:
            return None, f'{idx}行目: category "{category_name}" が存在しません'

        try:
            price = int(price) if price else 0
        except ValueError:
            return None, f'{idx}行目: price "{price}" は数値である必要があります'

        obj = Item(
            item_cd=item_cd,
            item_nm=row.get('item_nm'),
            category=category,
            description=row.get('description') or '',
            price=int(price) if price else 0,
            update_user=request.user
        )
        return obj, None
    

def get_row(rec):
    """
    共通の出力行生成処理
    - CSV/Excel エクスポートで共通利用
    """
    return [
        rec.item_cd,
        rec.item_nm,
        rec.category.category if rec.category else "",
        rec.description,
        rec.price
    ] + Common.get_common_columns(rec=rec)
