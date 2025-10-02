import io
import csv
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.management import call_command
from product_mst.models import Product

User = get_user_model()


class ProductViewTests(TestCase):
    def setUp(self):
        '''共通データ作成'''
        # テストクライアント生成
        self.client = Client()
        
        # テストデータ投入
        call_command('loaddata', 'test_tenants.json')
        call_command('loaddata', 'test_registers.json')
        call_command('loaddata', 'test_product_categories.json')
        call_command('loaddata', 'test_products.json')
        
        # システムユーザーで実施
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='system@example.com', password='pass')

    # -----------------------------
    # 一覧
    # -----------------------------
    def test_1_1_1(self):
        '''初期表示（データあり）'''
        # レスポンス取得
        response = self.client.get(reverse('product_mst:list'))
        
        # ステータスコード確認
        self.assertEqual(response.status_code, 200)
        
        # レスポンス内容確認
        self.assertContains(response, '商品001')
        
        # 取得データ確認
        list = response.context['products']
        self.assertEqual(list.count(), 8)  # 件数
        self.assertTrue(all(tid == 1 for tid in list.values_list('tenant_id', flat=True)))  # テナントID
        
    def test_1_1_2(self):
        '''初期表示（データなし）'''
        # 商品データを全削除
        Product.objects.all().delete()
        
        # レスポンス取得
        response = self.client.get(reverse('product_mst:list'))

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)
        
        # 取得データ確認
        list = response.context['products']
        self.assertEqual(list.count(), 0)  # 件数
        
    # -------------------
    # 検索処理
    # -------------------
    def test_2_1_1(self):
        '''検索処理（商品名称）'''
        # レスポンス取得
        response = self.client.get(reverse('product_mst:list'), {'search_product_name': '001'})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)
        
        # 取得データ確認
        list = response.context['products']
        self.assertEqual(list.count(), 1)  # 件数
        self.assertEqual('商品001', list[0].product_name)  # データ値
        self.assertEqual('001', response.context['search_product_name'])  # 検索フォームの入力値
        
    def test_2_1_2(self):
        '''検索処理（商品カテゴリ）'''
        # レスポンス取得
        response = self.client.get(reverse('product_mst:list'), {'search_product_category': 1})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)
        
        # 取得データ確認
        list = response.context['products']
        self.assertEqual(list.count(), 2)  # 件数
        self.assertEqual(1, list[0].product_category.pk)  # データ値
        self.assertEqual(1, int(response.context['search_product_category']))  # 検索フォームの入力値
