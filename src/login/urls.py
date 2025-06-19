from django.urls import path
from . import views

app_name = 'login'

urlpatterns = [
    # ログインページの表示
    path('', views.Login.as_view(), name='login'),
    # アクセス履歴確認画面
    path('access_history/', views.AccessLogListView.as_view(), name='access_history'),
    # パスワードリセット関連
    path('reset/<uidb64>/<token>', views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('password_reset/done/', views.PasswordResetDone.as_view(), name='password_reset_done'),
    path('password_reset/complete/', views.PasswordResetComplete.as_view(), name='password_reset_complete'),
    path('password_reset/', views.PasswordReset.as_view(), name='password_reset'),
]