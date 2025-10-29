from django.urls import path
from . import views

app_name = 'partner_mst'

urlpatterns = [
    #--------------
    # 取引先マスタ
    #--------------
    path('', views.PartnerListView.as_view(), name='list'),
    path('<int:pk>/delete/', views.PartnerDeleteView.as_view(), name='delete'),
    path('import/csv', views.ImportCSV.as_view(), name='import_csv'),
    path('export/csv', views.ExportCSV.as_view(), name='export_csv'),
    path('export/check/', views.ExportCheckView.as_view(), name='export_check'),
    path('create/', views.PartnerCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.PartnerUpdateView.as_view(), name='update'),
    path('bulk_delete/', views.PartnerBulkDeleteView.as_view(), name='bulk_delete'),
]
