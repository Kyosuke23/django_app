from django.urls import path
from . import views

app_name = 'sales_order'

urlpatterns = [
    # -----------------
    # 受注管理
    # -----------------
    path('', views.SalesOrderListView.as_view(), name='list'),
    path('<int:pk>/delete/', views.SalesOrderDeleteView.as_view(), name='delete'),
    path("import/csv", views.ImportCSV.as_view(), name='import_csv'),
    path('export/csv', views.ExportCSV.as_view(), name='export_csv'),
    path('export/excel', views.ExportExcel.as_view(), name='export_excel'),
    path('create/', views.SalesOrderCreateModalView.as_view(), name='create'),
    path('<int:pk>/update/', views.SalesOrderUpdateModalView.as_view(), name='update'),
    path('product/info/', views.ProductInfoView.as_view(), name='product_info'),
    path('partner/info/', views.PartnerInfoView.as_view(), name='partner_info'),
    path('public/thanks/', views.SalesOrderPublicThanksView.as_view(), name='public_thanks'),  # 下のURLと入れ替え不可
    path('public/<str:token>/', views.SalesOrderPublicDetailView.as_view(), name='public_detail'),
]
