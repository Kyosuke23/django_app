from .forms import SignUpForm, EditForm, ChangePasswordForm
from register.models import CustomUser
from django.views import generic
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Page
from django.http import JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.views import PasswordChangeView
from .const import GENDER_CHOICES, STATE_CHOICES, PRIVILEGE_CHOICES


class RegisterUserList(LoginRequiredMixin, generic.ListView, generic.edit.ModelFormMixin):
    """
    ユーザーの一覧表示
    """
    model = CustomUser
    form_class = SignUpForm
    context_object_name = 'users'
    template_name = 'register/index.html'
    paginate_by = 50

    def get_queryset(self, **kwarg):
        # query_setをクレンジングして取得
        query_set = super().get_queryset(**kwarg)
        # 検索キーワードを取得（空白時に"None"と表示されるのを予防）
        searchInputText = self.request.GET.get('search') or ''
        # 検索キーワードでフィルタ
        if searchInputText:
            query_set = query_set.filter(
                Q(username__icontains=searchInputText) | Q(first_name__icontains=searchInputText) | Q(last_name__icontains=searchInputText)
            )
        return query_set

    def get_context_data(self, **kwarg):
        # コンテキストデータの取得
        context = super().get_context_data(**kwarg)
        # 検索キーワードを取得（空白時に"None"と表示されるのを予防）
        searchInputText = self.request.GET.get('search') or ''
        # 検索フォームにキーワードを残す
        context['search'] = searchInputText
        # 各種リストのデータをフォームに適用
        context['gender_list'] = GENDER_CHOICES
        context['state_list'] = STATE_CHOICES
        context['privilege_list'] = PRIVILEGE_CHOICES
        page: Page = context['page_obj']
        # ページネーション設定
        context['paginator_range'] = page.paginator.get_elided_page_range(
            page.number
            , on_each_side=1
            , on_ends=1
        )
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

class RegisterUserCreate(LoginRequiredMixin, generic.edit.CreateView):
    """
    ユーザー情報の登録処理
    """
    class Meta:
        model = CustomUser
    template_name = 'register/create.html'
    context_object_name = 'user'
    form_class = SignUpForm
    
    def get_success_url(self):
        # 処理後は検索一覧画面に遷移
        return reverse_lazy('register:register_user_index')
    
    def post(self, request, *args, **kwargs):
        # フォームの入力データを取得
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
    
class RegisterUserUpdate(LoginRequiredMixin, generic.edit.UpdateView):
    """
    ユーザー情報の更新処理
    """
    class Meta:
        model = CustomUser
    template_name = 'register/edit.html'
    context_object_name = 'user'
    form_class = EditForm
    
    def get_success_url(self):
        # 処理後は検索一覧画面に遷移
        return reverse_lazy('register:register_user_index')
    
    def post(self, request, *args, **kwargs):
        # フォームのデータからモデルインスタンスを取得
        user = get_object_or_404(CustomUser, pk=request.POST['pk'])
        # モデルを基にしたフォームを作成
        form = EditForm(request.POST, instance=user)
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
    
class RegisterUserDelete(LoginRequiredMixin, generic.edit.DeleteView):
    """
    ユーザー情報の削除処理
    """
    model = CustomUser
    template_name = 'register/delete.html'

    def get_success_url(self):
        # 処理後は検索一覧画面に遷移
        return reverse_lazy('register:register_user_index')

    def post(self, request, *args, **kwargs):
        # 削除処理の実行
        CustomUser.objects.filter(pk=request.POST['pk']).delete()
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
    
class RegisterUserChangePassword(LoginRequiredMixin, PasswordChangeView):
    """
    パスワードの変更処理
    """
    form_class = ChangePasswordForm
    template_name = 'register/password_change.html'

    def get_success_url(self):
        # 処理成功のフラッシュメッセージを設定
        messages.success(self.request, 'パスワードが変更されました')
        # 処理後は検索一覧画面に遷移
        return reverse_lazy('dashboard:top')
