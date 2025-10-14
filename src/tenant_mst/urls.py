from django.urls import path
from . import views

app_name = 'tenant_mst'

urlpatterns = [
    #--------------
    # テナント情報
    #--------------
    path('edit/', views.TenantEditView.as_view(), name='edit'),
]
