from django.urls import path
from . import views

app_name = 'sales_order'

urlpatterns = [
    # -----------------
    # 受注管理
    # -----------------
    # --- CRUD処理 ---
    path('', views.SalesOrderListView.as_view(), name='list'),
    path('create/', views.SalesOrderCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.SalesOrderUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.SalesOrderDeleteView.as_view(), name='delete'),
    path('export/csv', views.ExportCSV.as_view(), name='export_csv'),
    path('export/excel', views.ExportExcel.as_view(), name='export_excel'),
    
    # --- マスタ情報取得 ---
    path('product/info/', views.ProductInfoView.as_view(), name='product_info'),
    path('partner/info/', views.PartnerInfoView.as_view(), name='partner_info'),
    
    # --- 顧客向けページ ---
    path('public/contract/<str:token>/', views.SalesOrderPublicContractView.as_view(), name='public_contract'),
    path('public/confirm/<str:token>/', views.SalesOrderPublicConfirmView.as_view(), name='public_confirm'),
    path('public/thanks/', views.SalesOrderPublicThanksView.as_view(), name='public_thanks'),
    
    # --- 注文書発行処理 ---
    path('<int:pk>/order_sheet/', views.OrderSheetPdfView.as_view(), name='order_sheet_pdf'),
]
