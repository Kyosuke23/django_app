from django.urls import path
from . import views

app_name = 'register'

urlpatterns = [
    path('', views.RegisterUserList.as_view(), name='register_user_index'),
    path('create/', views.RegisterUserCreate.as_view(), name='register_user_create'),
    path('update/<int:pk>/', views.RegisterUserUpdate.as_view(), name='register_user_update'),
    path('delete/<int:pk>/', views.RegisterUserDelete.as_view(), name='register_user_delete'),
    path('change_password/', views.RegisterUserChangePassword.as_view(), name='register_user_change_password'),
    # データダウンロード
    path('export/csv', views.ExportCSV.as_view(), name='register_user_export_csv'),
    path('export/excel', views.ExportExcel.as_view(), name='register_user_export_excel'),
    # 住所検索
    path('get_postal_code/', views.GetPostalCode.as_view(), name='get_postal_code'),
]
