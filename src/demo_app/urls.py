from django.urls import path
from .views import item_mst, ajax_test

app_name = 'demo_app'

urlpatterns = [
    # サンプルマスタ管理画面
    path('item_mst/', item_mst.ItemList.as_view(), name='item_mst_index'),
    path('item_mst/create/', item_mst.ItemCreate.as_view(), name='item_mst_create'),
    path('item_mst/update/<int:pk>/', item_mst.ItemUpdate.as_view(), name='item_mst_update'),
    path('item_mst/delete/<int:pk>/', item_mst.ItemDelete.as_view(), name='item_mst_delete'),

    # Ajaxテスト画面
    path('greet/', ajax_test.AjaxTest.as_view(), name='ajax_test'),
]
