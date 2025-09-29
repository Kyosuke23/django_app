from django.urls import path
from . import views

app_name = 'sales_order'

urlpatterns = [
    # -----------------
    # 受注管理
    # -----------------
    path('sales_order/', views.SalesOrderListView.as_view(), name='list'),
    path('sales_order/<int:pk>/delete/', views.SalesOrderDeleteView.as_view(), name='delete'),
    path("sales_order/import/csv", views.ImportCSV.as_view(), name='import_csv'),
    path('sales_order/export/csv', views.ExportCSV.as_view(), name='export_csv'),
    path('sales_order/export/excel', views.ExportExcel.as_view(), name='export_excel'),
    path('sales_order/modal/create/', views.SalesOrderCreateModalView.as_view(), name='create'),
    path('sales_order/<int:pk>/modal/update/', views.SalesOrderUpdateModalView.as_view(), name='update'),
]
