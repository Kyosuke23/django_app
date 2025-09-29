from django.urls import path
from . import views

app_name = 'product_mst'

urlpatterns = [
    # -----------------
    # 商品マスタ
    # -----------------
    path('', views.ProductListView.as_view(), name='list'),
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='delete'),
    path("import/csv", views.ImportCSV.as_view(), name='import_csv'),
    path('export/csv', views.ExportCSV.as_view(), name='export_csv'),
    path('export/excel', views.ExportExcel.as_view(), name='export_excel'),
    path('create/', views.ProductCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.ProductUpdateView.as_view(), name='update'),
    path('bulk_delete/', views.ProductBulkDeleteView.as_view(), name='bulk_delete'),
]
