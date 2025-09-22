from django.urls import path
from . import views

app_name = 'product_mst'

urlpatterns = [
    # -----------------
    # 商品マスタ
    # -----------------
    path('product/', views.ProductListView.as_view(), name='product_list'),
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('product/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('product/<int:pk>/update/', views.ProductUpdateView.as_view(), name='product_update'),
    path('product/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    path("product/import/csv", views.ImportCSV.as_view(), name='import_csv'),
    path('product/export/csv', views.ExportCSV.as_view(), name='export_csv'),
    path('product/export/excel', views.ExportExcel.as_view(), name='export_excel'),
]
