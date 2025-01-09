from django.views import generic
from ..models.item_mst import Item, Category
from ..form import ItemCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.core.paginator import Page
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib import messages
import re


class ItemList(LoginRequiredMixin, generic.ListView, generic.edit.ModelFormMixin):
    """
    アイテムマスタ画面の一覧表示
    """
    model = Item
    form_class = ItemCreationForm
    context_object_name = 'items'
    template_name = 'demo_app/item_mst/index.html'
    paginate_by = 50

    def get_queryset(self, **kwarg):
        # query_setをクレンジングして取得
        query_set = super().get_queryset(**kwarg).filter(is_deleted=False)
        # 検索キーワードを取得（空白時に"None"と表示されるのを予防）
        searchInputText = self.request.GET.get('search') or ''
        # 検索キーワードでフィルタ
        if searchInputText:
            query_set = query_set.filter(
                Q(item_cd__icontains=searchInputText) | Q(item_nm__icontains=searchInputText)
            )
        return query_set

    def get_context_data(self, **kwarg):
        # コンテキストデータの取得
        context = super().get_context_data(**kwarg)
        # 検索キーワードを取得（空白時に"None"と表示されるのを予防）
        searchInputText = self.request.GET.get('search') or ''
        # 検索フォームにキーワードを残す
        context['search'] = searchInputText
        # カテゴリマスタのデータをフォームに適用
        categories = Category.objects.order_by('id')
        context['category_list'] = categories
        # ページネーション設定
        context = set_pagination(context, self.request.GET.urlencode())
        # フォームの値を設定
        context['form'] = self.get_form
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = None
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = None
        self.object_list = self.get_queryset()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    
class ItemCreate(LoginRequiredMixin, generic.edit.CreateView):
    """
    サンプルマスタ情報の登録処理
    """
    model = Item
    form_class = ItemCreationForm
    context_object_name = 'item'
    template_name = 'demo_app/item_mst/create.html'
    
    def get_success_url(self):
        # 処理後は検索一覧画面に遷移
        return reverse_lazy('demo_app:item_mst_index')
    
    def post(self, request, *args, **kwargs):
        # フォームの入力データを取得
        self.object = None
        self.object_list = self.get_queryset()
        form = self.get_form()
        # バリデーションを通過した場合のみフォームの情報を保存
        if form.is_valid():
            post = form.save(commit=False)
            # 作成者と更新者をログインユーザーで設定
            post.created_user = self.request.user
            post.updated_user = self.request.user
            # 登録処理の実行
            post.save()
            # 処理成功のフラッシュメッセージを設定
            messages.success(request, '登録が完了しました')
        # 処理結果を格納
        result = JsonResponse(
            {
                'errors': form.errors  # エラーフィールド
                , 'success_url': self.get_success_url()  # 成功時の遷移先URL
            },
            json_dumps_params={'ensure_ascii': False}  # 文字化け対策
        )
        # 処理結果を返却
        return result

class ItemUpdate(LoginRequiredMixin, generic.edit.UpdateView):
    """
    サンプルマスタ情報の更新処理
    """
    model = Item
    form_class = ItemCreationForm
    context_object_name = 'item'
    template_name = 'demo_app/item_mst/edit.html'
    
    def get_success_url(self):
        # 処理後は検索一覧画面に遷移
        return reverse_lazy('demo_app:item_mst_index')
    
    def post(self, request, *args, **kwargs):
        # フォームのデータからモデルインスタンスを取得
        item = get_object_or_404(Item, pk=request.POST['pk'])
        # モデルを基にしたフォームを作成
        form = ItemCreationForm(request.POST, instance=item)
        # バリデーションを通過した場合のみフォームの情報を保存
        if form.is_valid():
            # 更新ユーザーをログインユーザーで設定
            form.update_user = self.request.user
            # 保存処理の実行
            form.save()
            # 処理成功のフラッシュメッセージを設定
            messages.success(request, '更新が完了しました')
        # 処理結果を格納
        result = JsonResponse(
            {
                'errors': form.errors  # エラーフィールド
                , 'success_url': self.get_success_url()  # 成功時の遷移先URL
            },
            json_dumps_params={'ensure_ascii': False}  # 文字化け対策
        )
        # 処理結果を返却
        return result
    
class ItemDelete(LoginRequiredMixin, generic.edit.DeleteView):
    """
    サンプルマスタ情報の削除処理
    """
    model = Item
    template_name = 'demo_app/item_mst/delete.html'

    def get_success_url(self):
        # 処理後は検索一覧画面に遷移
        return reverse_lazy('demo_app:item_mst_index')

    def post(self, request, *args, **kwargs):
        # 削除処理の実行
        Item.objects.filter(pk=request.POST['pk']).delete()
        # 処理成功のフラッシュメッセージを設定
        messages.success(request, '削除が完了しました')
        # 処理結果を格納
        result = JsonResponse(
            {
                'errors': {}  # エラーフィールド
                , 'success_url': self.get_success_url()  # 成功時の遷移先URL
            },
            json_dumps_params={'ensure_ascii': False}  # 文字化け対策
        )
        # 処理結果を返却
        return result
    
def set_pagination(context, url_params):
    """
    ページング部品の値をコンテキストに設定
    """
    page: Page = context['page_obj']
    context['paginator_range'] = page.paginator.get_elided_page_range(
        page.number
        , on_each_side=1
        , on_ends=1
    )
    # ページングのパラメータを削除
    url_params = re.sub('\&page\=\d*', '', url_params)
    # URLパラメータを再設定
    context['query_str'] = url_params
    # 処理結果を返却
    return context