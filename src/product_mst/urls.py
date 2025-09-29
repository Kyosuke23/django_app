from django.urls import path
from . import views

app_name = 'product_mst'

urlpatterns = [
    # -----------------
    # 商品マスタ
    # -----------------
    path('product/', views.ProductListView.as_view(), name='list'),
    path('product/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='delete'),
    path("product/import/csv", views.ImportCSV.as_view(), name='import_csv'),
    path('product/export/csv', views.ExportCSV.as_view(), name='export_csv'),
    path('product/export/excel', views.ExportExcel.as_view(), name='export_excel'),
    path('product/modal/create/', views.ProductCreateView.as_view(), name='create'),
    path('product/<int:pk>/modal/update/', views.ProductUpdateView.as_view(), name='update'),
]
