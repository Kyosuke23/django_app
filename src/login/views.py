from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView


class Login(LoginView):
    """
    ログイン処理
    """
    fields = '__all__'
    template_name = 'login/login.html'

    def get_success_url(self):
        return reverse_lazy('dashboard:top')

class Logout(LogoutView):
    """
    ログアウト処理
    """
    template_name = 'login/login.html'

class PasswordReset(PasswordResetView):
    """
    パスワードリセット画面表示
    """
    subject_template_name = 'mail/password_reset/password_reset_subject.txt'
    email_template_name = 'mail/password_reset/password_reset_email.txt'
    template_name = 'login/password_reset_form.html'
    success_url = reverse_lazy('login:password_reset_done')

class PasswordResetDone(PasswordResetDoneView):
    """
    パスワードリセットメール送信後の画面
    """
    template_name = 'login/password_reset_done.html'

class PasswordResetConfirm(PasswordResetConfirmView):
    """
    パスワード再設定画面
    （パスワードリセットURLを踏んだ直後の画面）
    """
    success_url = reverse_lazy('login:password_reset_complete')
    template_name = 'login/password_reset_confirm.html'

class PasswordResetComplete(PasswordResetCompleteView):
    """
    パスワード再設定の完了画面
    """
    template_name = 'login/password_reset_complete.html'