from django.urls import path
from . import views

app_name = 'register'

urlpatterns = [
    path('', views.RegisterUserList.as_view(), name='list'),
    path('create/', views.RegisterUserCreate.as_view(), name='create'),
    path('update/<int:pk>/', views.RegisterUserUpdate.as_view(), name='update'),
    path('delete/<int:pk>/', views.RegisterUserDelete.as_view(), name='delete'),
    path('change_password/', views.RegisterUserChangePassword.as_view(), name='change_password'),
    path('export/csv', views.ExportCSV.as_view(), name='export_csv'),
    path('export/excel', views.ExportExcel.as_view(), name='export_excel'),
]
