from django.urls import path
from . import views

app_name = 'register'

urlpatterns = [
    path('', views.UserListView.as_view(), name='list'),
    path('create/', views.UserCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.UserUpdateView.as_view(), name='update'),
    path('update_profile/', views.ProfileUpdateView.as_view(), name='update_profile'),
    path('<int:pk>/delete/', views.UserDeleteView.as_view(), name='delete'),
    path('change_password/', views.UserChangePassword.as_view(), name='change_password'),
    path('export/csv', views.ExportCSV.as_view(), name='export_csv'),
    path('export/excel', views.ExportExcel.as_view(), name='export_excel'),
    path('bulk_delete/', views.UserBulkDeleteView.as_view(), name='bulk_delete'),
]
