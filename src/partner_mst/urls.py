from django.urls import path
from . import views

app_name = 'partner_mst'

urlpatterns = [
    # -----------------
    # 商品マスタ
    # -----------------
    path('partner/', views.PartnerListView.as_view(), name='partner_list'),
    path('partner/create/', views.PartnerCreateView.as_view(), name='partner_create'),
    path('partner/<int:pk>/update/', views.PartnerUpdateView.as_view(), name='partner_update'),
    path('partner/<int:pk>/delete/', views.PartnerDeleteView.as_view(), name='partner_delete'),
    path("partner/import/csv", views.ImportCSV.as_view(), name='import_csv'),
    path('partner/export/csv', views.ExportCSV.as_view(), name='export_csv'),
    path('partner/export/excel', views.ExportExcel.as_view(), name='export_excel'),
    path('partner/modal/create/', views.PartnerCreateModalView.as_view(), name='partner_create_modal'),
    path('partner/<int:pk>/modal/update/', views.PartnerUpdateModalView.as_view(), name='partner_update_modal'),
]
