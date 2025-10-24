from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from product_mst.models import Product, ProductCategory
from product_mst.views import ProductUpdateView, ProductDeleteView, ProductBulkDeleteView, HEADER_MAP
from django.contrib import messages
from tenant_mst.models import Tenant
from sales_order.models import SalesOrder, SalesOrderDetail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.management import call_command
from bs4 import BeautifulSoup
from django.utils import timezone
from decimal import Decimal
from django.contrib.messages import get_messages
import csv
import io
import json

User = get_user_model()


class ProductViewTests(TestCase):
    '''商品マスタ 単体テスト'''

    def setUp(self):
        '''共通データ作成'''
        self.factory = RequestFactory()

        # テストクライアント生成
        self.client = Client()

        # テストデータ投入
        call_command('loaddata', 'test_tenants.json')
        call_command('loaddata', 'test_registers.json')
        call_command('loaddata', 'test_product_categories.json')
        call_command('loaddata', 'test_products.json')

        # 基本は更新ユーザーで実施
        self.user = get_user_model().objects.get(pk=3)
        self.client.login(email='editor@example.com', password='pass')

    #----------------
    # ListView
    #----------------
    def test_1_1_1_1(self):
        '''初期表示（正常系: データあり）'''
        # レスポンス取得
        response = self.client.get(reverse('product_mst:list'))

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['products']
        self.assertEqual(list.count(), 13)
        self.assertTrue(all(tid == 1 for tid in list.values_list('tenant_id', flat=True)))

        # 要素の取得を確認
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertIsNotNone(soup.select_one('#import-btn'))
        self.assertIsNotNone(soup.select_one('#create-btn'))
        self.assertIsNotNone(soup.select_one('.edit-btn'))
        self.assertIsNotNone(soup.select_one('#bulk-delete-btn'))
        self.assertIsNotNone(soup.select_one('#check-all'))
        self.assertIsNotNone(soup.select_one('.check-item'))
        self.assertIsNotNone(soup.select_one('#category_manage'))

    def test_1_1_1_2(self):
        '''初期表示（正常系: 参照権限）'''
        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        # レスポンス取得
        response = self.client.get(reverse('product_mst:list'))

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['products']
        self.assertEqual(list.count(), 13)
        self.assertTrue(all(tid == 1 for tid in list.values_list('tenant_id', flat=True)))

        # 要素の取得を確認
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertIsNone(soup.select_one('#import-btn'))
        self.assertIsNone(soup.select_one('#create-btn'))
        self.assertIsNone(soup.select_one('.edit-btn'))
        self.assertIsNone(soup.select_one('#bulk-delete-btn'))
        self.assertIsNone(soup.select_one('#check-all'))
        self.assertIsNone(soup.select_one('.check-item'))
        self.assertIsNone(soup.select_one('#category_manage'))

    def test_1_1_2_1(self):
        '''一覧画面表示（異常系: 直リンク）'''
        url = reverse('product_mst:list')

        # ログアウト状態でアクセス
        self.client.logout()
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # リダイレクト確認
        self.assertRedirects(response, '/login/?next=/product_mst/')

    def test_1_2_1_1(self):
        '''検索処理（正常系: キーワード）'''
        key = '999'

        # レスポンス取得
        response = self.client.get(reverse('product_mst:list'), {'search_keyword': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['products']
        self.assertEqual(list.count(), 5)
        self.assertEqual('keyword_test_product_999', list[0].product_name)

        # 各オブジェクトのプロパティに "999" が含まれていることを確認
        for p in list:
            text_values = [
                str(p.product_name),
                str(p.unit or ''),
                str(p.unit_price),
                str(p.description or ''),
                str(p.product_category.product_category_name if p.product_category else ''),
            ]
            # どれか一つでも '999' を含めばOK
            self.assertTrue(
                any(key in v for v in text_values),
                f"{p.id} のいずれのプロパティにも '{key}' が含まれていません。: {text_values}"
            )

        # 検索後のフォーム値確認
        self.assertEqual(key, response.context['form']['search_keyword'].value())

    def test_1_2_1_2(self):
        '''検索処理（正常系: 商品名）'''
        # 検索値
        key = '003'

        # レスポンス取得
        response = self.client.get(reverse('product_mst:list'), {'search_product_name': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['products']
        self.assertEqual(list.count(), 1)
        self.assertEqual('商品003', list[0].product_name)

        # 検索後のフォーム値確認
        self.assertEqual(key, response.context['form']['search_product_name'].value())

    def test_1_2_1_3(self):
        '''検索処理（正常系: 商品カテゴリ）'''
        # 検索値
        key = 3

        # レスポンス取得
        response = self.client.get(reverse('product_mst:list'), {'search_category': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['products']
        self.assertEqual(list.count(), 1)
        self.assertEqual('商品005', list[0].product_name)

        # 検索後のフォーム値確認
        self.assertEqual(key, int(response.context['form']['search_category'].value()))

    def test_1_2_1_4(self):
        '''検索処理（正常系: 単位）'''
        # 検索値
        key = '箱'

        # レスポンス取得
        response = self.client.get(reverse('product_mst:list'), {'search_unit': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['products']
        self.assertEqual(list.count(), 1)
        self.assertEqual('商品006', list[0].product_name)

        # 検索後のフォーム値確認
        self.assertEqual(key, response.context['form']['search_unit'].value())

    def test_1_2_1_5(self):
        '''単価範囲検索（正常系: 最小～最大指定）'''
        Product.objects.all().delete()

        # 商品カテゴリを1件作成
        c = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ',
            create_user=self.user,
            update_user=self.user,
        )

        # 商品を5件作成（単価100,200,300,400,500）
        for i in range(1, 6):
            Product.objects.create(
                tenant=self.user.tenant,
                product_name=f'単価商品{i}',
                product_category=c,
                unit_price=i * 100,
                unit='個',
                description='テスト用',
                create_user=self.user,
                update_user=self.user,
            )

        # 単価範囲 200〜400 の検索
        url = reverse('product_mst:list')
        response = self.client.get(url, {
            'search_unit_price_min': 200,
            'search_unit_price_max': 400,
        })

        # ステータスと結果件数
        self.assertEqual(response.status_code, 200)
        products = response.context['products']

        # 抽出された単価リストを確認
        prices = list(products.values_list('unit_price', flat=True))
        self.assertTrue(all(200 <= p <= 400 for p in prices))

        # 件数および内容確認（想定：3件）
        self.assertEqual(products.count(), 3)
        expected_names = ['単価商品2', '単価商品3', '単価商品4']
        self.assertEqual(list(products.values_list('product_name', flat=True)), expected_names)

        # 検索後のフォーム値確認
        self.assertEqual(response.context['form']['search_unit_price_min'].value(), str(200))
        self.assertEqual(response.context['form']['search_unit_price_max'].value(), str(400))

    def test_1_3_1_1(self):
        '''単価昇順ソートの確認（正常）'''
        url = reverse('product_mst:list') + '?sort=unit_price'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 一覧データを取得
        qs = response.context['products']

        # DBから取得した単価を配列化
        prices = list(qs.values_list('unit_price', flat=True))

        # 昇順で並んでいることを確認
        self.assertEqual(prices, sorted(prices))

    def test_1_3_1_2(self):
        '''単価降順ソートの確認（正常）'''
        url = reverse('product_mst:list') + '?sort=-unit_price'

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        qs = response.context['products']
        prices = list(qs.values_list('unit_price', flat=True))

        # 降順で並んでいることを確認
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_1_4_1_1(self):
        '''ページング'''
        url = reverse('product_mst:list')

        # テスト初期データを削除
        Product.objects.all().delete()

        # 商品カテゴリを1件作成
        c = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ',
            create_user=self.user,
            update_user=self.user,
        )

        # 21件作成
        for i in range(1, 22):
            Product.objects.create(
                tenant=self.user.tenant,
                product_name=f'商品{i}',
                product_category=c,
                unit_price=100,
                unit='個',
                description='',
                create_user=self.user,
                update_user=self.user,
            )

        # 1ページ目
        response_page1 = self.client.get(url)
        self.assertEqual(response_page1.status_code, 200)

        products_page1 = response_page1.context['products']
        self.assertEqual(len(products_page1), 20, '1ページ目の件数が20件であること')

        # 21件目が含まれていない
        self.assertFalse(any('商品21' in p.product_name for p in products_page1))

        # 2ページ目
        response_page2 = self.client.get(url + '?page=2')
        self.assertEqual(response_page2.status_code, 200)

        products_page2 = response_page2.context['products']
        self.assertEqual(len(products_page2), 1, '2ページ目の件数が1件であること')

        # 21件目が2ページ目に含まれる
        self.assertTrue(any('商品21' in p.product_name for p in products_page2))

    #----------------
    # CreateView
    #----------------
    def test_2_1_1_1(self):
        '''登録画面表示（正常系）'''
        # レスポンス取得
        response = self.client.get(reverse('product_mst:create'))

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # JSONをロード
        data = json.loads(response.content)
        html = data['html']

        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(html, 'html.parser')
        modal_title = soup.select_one('.modal-title').get_text(strip=True)

        # 画面要素を確認
        self.assertEqual(modal_title, '商品: 新規登録')

    def test_2_1_2_1(self):
        '''登録画面表示（異常系：直リンク）'''
        url = reverse('product_mst:create')

        # ログインせずにアクセス
        self.client.logout()
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # リダイレクト確認
        self.assertRedirects(response, '/login/?next=/product_mst/create/')

    def test_2_1_2_2(self):
        '''登録画面表示（異常系：権限不足）'''
        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        url = reverse('product_mst:create')
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_2_2_1_1(self):
        '''V12: 登録処理（正常）'''
        url = reverse('product_mst:create')

        # 商品カテゴリを1件作成
        c = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ',
            create_user=self.user,
            update_user=self.user,
        )

        # 登録用データ
        data = {
            'product_name': '登録テスト',
            'product_category': c.id,
            'unit_price': 500,
            'unit': '箱',
            'description': 'テスト用の商品です',
        }

        # 処理実行
        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # レスポンス確認
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])

        # メッセージ確認
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages) > 0)
        self.assertEqual(messages[0].message, '商品「登録テスト」を登録しました。')
        self.assertEqual(messages[0].level_tag, 'success')

        # DB登録確認
        product = Product.objects.get(product_name='登録テスト')
        self.assertEqual(product.product_name, '登録テスト')
        self.assertEqual(product.product_category, c)
        self.assertEqual(product.unit_price, 500)
        self.assertEqual(product.unit, '箱')
        self.assertEqual(product.description, 'テスト用の商品です')
        self.assertEqual(product.is_deleted, False)
        self.assertEqual(product.create_user, self.user)
        self.assertEqual(product.update_user, self.user)
        self.assertEqual(product.tenant, self.user.tenant)
        self.assertLessEqual(abs((product.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((product.updated_at - timezone.now()).total_seconds()), 5)

    def test_2_2_1_2(self):
        '''登録処理（正常系: 別テナントで同じ取引先名称）'''
        # テナントを2つ作成
        self.tenant1 = Tenant.objects.create(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com'
        )
        self.tenant2 = Tenant.objects.create(
            tenant_name='テナントB',
            representative_name='代表B',
            email='b@example.com'
        )

        # ユーザーを作成してテナント1に所属
        self.user1 = get_user_model().objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass',
            privilege=0,
            tenant=self.tenant1
        )

        # ユーザーを作成してテナント2に所属
        self.user2 = get_user_model().objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass',
            privilege=0,
            tenant=self.tenant2
        )

        url = reverse('product_mst:create')

        # 商品カテゴリを1件作成
        c = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ',
            create_user=self.user,
            update_user=self.user,
        )

        # 登録用データ
        data = {
            'product_name': '重複テスト商品',
            'product_category': c.id,
            'unit_price': 500,
            'unit': '箱',
            'description': '重複テスト用の商品です',
        }

        # テナント1で登録
        self.client.login(email='user1@example.com', password='pass')
        response = self.client.post(
            url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])

        # テナント2で同じ名前を登録
        self.client.logout()
        self.client.login(email='user2@example.com', password='pass')
        response = self.client.post(
            url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])

        # DB確認
        product_1 = Product.objects.filter(tenant=self.tenant1, product_name='重複テスト商品')
        product_2 = Product.objects.filter(tenant=self.tenant2, product_name='重複テスト商品')

        # 件数確認
        self.assertEqual(product_1.count(), 1)
        self.assertEqual(product_2.count(), 1)

    def test_2_2_2_1(self):
        '''登録画面表示（異常系：直リンク）'''
        url = reverse('product_mst:create')

        # ログインせずにアクセス
        self.client.logout()

        # 商品カテゴリを1件作成
        c = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ',
            create_user=self.user,
            update_user=self.user,
        )

        # 登録用データ
        data = {
            'product_name': '登録テスト',
            'product_category': c.id,
            'unit_price': 500,
            'unit': '箱',
            'description': 'テスト用の商品です',
        }

        # 処理実行
        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # リダイレクト確認
        self.assertRedirects(response, '/login/?next=/product_mst/create/')

    def test_2_2_2_2(self):
        '''登録画面表示（異常系：権限不足）'''
        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        url = reverse('product_mst:create')

        # 商品カテゴリを1件作成
        c = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ',
            create_user=self.user,
            update_user=self.user,
        )

        # 登録用データ
        data = {
            'product_name': '登録テスト',
            'product_category': c.id,
            'unit_price': 500,
            'unit': '箱',
            'description': 'テスト用の商品です',
        }

        # 処理実行
        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_2_2_2_3(self):
        '''登録処理（異常系: 商品名必須エラー）'''
        url = reverse('product_mst:create')

        # 商品カテゴリを1件作成
        c = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ',
            create_user=self.user,
            update_user=self.user,
        )

        # 登録用データ
        data = {
            'product_name': '',
            'product_category': c.id,
            'unit_price': 500,
            'unit': '箱',
            'description': 'テスト用の商品です',
        }

        # 処理実行
        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # レスポンス確認
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertFalse(res_json['success'])

        # DBに登録されていないことを確認
        self.assertEqual(Product.objects.filter(product_name='登録テスト').count(), 0)

        # エラーメッセージをHTMLから抽出
        soup = BeautifulSoup(res_json['html'], 'html.parser')
        self.assertEqual('この項目は必須です。', soup.select_one('#id_product_name + .invalid-feedback').get_text())

    def test_2_2_2_4(self):
        '''登録処理（異常系: 同一テナント内商品名重複）'''
        url = reverse('product_mst:create')

        # 商品カテゴリを2件作成
        c1 = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ1',
            create_user=self.user,
            update_user=self.user,
        )
        c2 = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ2',
            create_user=self.user,
            update_user=self.user,
        )

        # 登録用データ
        data1 = {
            'product_name': '重複テスト商品',
            'product_category': c1.id,
            'unit_price': 500,
            'unit': '箱',
            'description': 'テスト用の商品1です',
        }

        # 1件目を登録
        response1 = self.client.post(
            url,
            data1,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response1.status_code, 200)
        res_json1 = json.loads(response1.content)
        self.assertTrue(res_json1['success'])

        # 同じ商品名で2件目を登録
        data2 = {
            'product_name': '重複テスト商品',
            'product_category': c2.id,
            'unit_price': 1000,
            'unit': '個',
            'description': 'テスト用の商品2です',
        }
        response2 = self.client.post(
            url,
            data2,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response2.status_code, 200)
        res_json2 = json.loads(response2.content)
        self.assertFalse(res_json2['success'])

        # DBに2件目は登録されていないことを確認
        self.assertEqual(Product.objects.filter(product_name='重複テスト商品').count(), 1)

        # エラーメッセージをHTMLから抽出
        soup = BeautifulSoup(res_json2['html'], 'html.parser')
        self.assertEqual('同じ商品名が既に登録されています。', soup.select_one('#id_product_name + .invalid-feedback').get_text())


    #----------------
    # UpdateView
    #----------------
    def test_3_1_1_1(self):
        '''更新画面表示'''
        # レスポンス取得
        response = self.client.get(reverse('product_mst:update', args=[1]))

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # JSONをロード
        data = json.loads(response.content)
        html = data['html']

        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(html, 'html.parser')
        modal_title = soup.select_one('.modal-title').get_text(strip=True)

        # モーダルタイトル確認
        self.assertEqual(modal_title, '商品更新: 商品001')

    def test_3_1_2_1(self):
        '''更新画面表示（異常系：直リンク）'''
        url = reverse('product_mst:update', args=[1])

        # ログアウト状態でアクセス
        self.client.logout()
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # リダイレクト確認
        self.assertRedirects(response, '/login/?next=/product_mst/1/update/')

    def test_3_1_2_2(self):
        '''更新画面表示（異常系：権限不足）'''
        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        url = reverse('product_mst:update', args=[1])
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_3_2_1_1(self):
        '''
        更新処理（正常系：全項目更新）
        '''
        # 商品カテゴリを2件作成
        c1 = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ1',
            create_user=self.user,
            update_user=self.user,
        )
        c2 = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ2',
            create_user=self.user,
            update_user=self.user,
        )

        # 事前データ作成
        product = Product.objects.create(
            tenant=self.user.tenant,
            product_name='旧商品',
            product_category=c1,
            unit='個',
            unit_price='123.45',
            description='旧説明文',
            create_user=self.user,
            update_user=self.user,
        )
        create_user = self.user

        # 事前データ作成ユーザーとは別のユーザーで実施
        update_user = get_user_model().objects.get(pk=2)
        self.client.login(email='manager@example.com', password='pass')

        url = reverse('product_mst:update', args=[product.id])
        data = {
            'product_name': '更新テスト',
            'product_category': c2.id,
            'unit_price': '234.56',
            'unit': '箱',
            'description': '新説明文',
        }

        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # レスポンス確認
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])

        # メッセージ確認
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages) > 0)
        self.assertEqual(messages[0].message, '商品「更新テスト」を更新しました。')
        self.assertEqual(messages[0].level_tag, 'success')

        # DB更新確認
        product.refresh_from_db()
        product = Product.objects.get(product_name='更新テスト')
        self.assertEqual(product.product_name, '更新テスト')
        self.assertEqual(product.product_category, c2)
        self.assertEqual(product.unit_price, Decimal('234.56'))
        self.assertEqual(product.unit, '箱')
        self.assertEqual(product.description, '新説明文')
        self.assertEqual(product.is_deleted, False)
        self.assertEqual(product.create_user, create_user)
        self.assertEqual(product.update_user, update_user)
        self.assertEqual(product.tenant, create_user.tenant)
        self.assertLessEqual(abs((product.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((product.updated_at - timezone.now()).total_seconds()), 5)

    def test_3_2_1_2(self):
        '''更新処理（正常系：別テナントで同じ商品名に変更）'''
        # テナントを2つ作成
        tenant1 = Tenant.objects.create(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com'
        )
        tenant2 = Tenant.objects.create(
            tenant_name='テナントB',
            representative_name='代表B',
            email='b@example.com'
        )

        # ユーザーを作成してテナント1に所属
        user1 = get_user_model().objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass',
            privilege=0,
            tenant=tenant1
        )

        # ユーザーを作成してテナント2に所属
        user2 = get_user_model().objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass',
            privilege=0,
            tenant=tenant2
        )

        # 商品カテゴリを2件作成
        c1 = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ1',
            create_user=self.user,
            update_user=self.user,
        )

        c2 = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ2',
            create_user=self.user,
            update_user=self.user,
        )

        # 各テナントに商品名データを事前作成（名称違い）
        product1 = Product.objects.create(
            tenant=tenant1,
            product_name='商品A',
            product_category=c1,
            unit='個',
            unit_price='123.45',
            description='説明文A',
            create_user=user1,
            update_user=user1,
        )

        product2 = Product.objects.create(
            tenant=tenant2,
            product_name='商品B',
            product_category=c2,
            unit='束',
            unit_price='234.56',
            description='説明文B',
            create_user=user2,
            update_user=user2,
        )

        # 更新データ（両方とも同じ名前に更新してみる）
        data = {
            'product_name': '更新テスト',
            'unit_price': '234.56',
        }

        # テナント1で更新
        self.client.login(email='user1@example.com', password='pass')
        url1 = reverse('product_mst:update', args=[product1.id])
        response = self.client.post(url1, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])

        # テナント2で更新
        self.client.logout()
        self.client.login(email='user2@example.com', password='pass')
        url2 = reverse('product_mst:update', args=[product2.id])
        response = self.client.post(url2, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])

        # DB確認（両テナントで同じ名前が登録されている）
        p1 = Product.objects.filter(tenant=tenant1, product_name='更新テスト')
        p2 = Product.objects.filter(tenant=tenant2, product_name='更新テスト')

        # 件数確認
        self.assertEqual(p1.count(), 1)
        self.assertEqual(p2.count(), 1)

    def test_3_2_2_1(self):
        '''
        更新処理（異常系：直リンク）
        '''
        # 商品カテゴリを2件作成
        c1 = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ1',
            create_user=self.user,
            update_user=self.user,
        )
        c2 = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ2',
            create_user=self.user,
            update_user=self.user,
        )

        # 事前データ作成
        product = Product.objects.create(
            tenant=self.user.tenant,
            product_name='旧商品',
            product_category=c1,
            unit='個',
            unit_price='123.45',
            description='旧説明文',
            create_user=self.user,
            update_user=self.user,
        )

        # ログインせずにアクセス
        self.client.logout()

        url = reverse('product_mst:update', args=[product.id])
        data = {
            'product_name': '更新テスト',
            'product_category': c2.id,
            'unit_price': '234.56',
            'unit': '箱',
            'description': '新説明文',
        }

        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # リダイレクト確認
        self.assertRedirects(response, f'/login/?next=/product_mst/{product.id}/update/')

    def test_3_2_2_2(self):
        '''
        更新処理（異常系：権限不足）
        '''
        # 商品カテゴリを2件作成
        c1 = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ1',
            create_user=self.user,
            update_user=self.user,
        )
        c2 = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ2',
            create_user=self.user,
            update_user=self.user,
        )

        # 事前データ作成
        product = Product.objects.create(
            tenant=self.user.tenant,
            product_name='旧商品',
            product_category=c1,
            unit='個',
            unit_price='123.45',
            description='旧説明文',
            create_user=self.user,
            update_user=self.user,
        )

        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        # ステータスコード確認
        url = reverse('product_mst:update', args=[product.id])
        data = {
            'product_name': '更新テスト',
            'product_category': c2.id,
            'unit_price': '234.56',
            'unit': '箱',
            'description': '新説明文',
        }

        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_3_2_2_3(self):
        '''更新処理（異常系：単位桁数超過）'''
        # 商品カテゴリを作成
        c = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ',
            create_user=self.user,
            update_user=self.user,
        )

        # 更新対象データ
        product = Product.objects.create(
            tenant=self.user.tenant,
            product_name='単位桁数商品',
            product_category=c,
            unit='個',
            unit_price='123.45',
            description='説明文A',
            create_user=self.user,
            update_user=self.user,
        )

        url = reverse('product_mst:update', args=[product.id])
        data = {
            'product_name': '更新テスト',
            'unit': 'a' * 21,
            'unit_price': '234.56',
        }

        # レスポンス確認
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertFalse(res_json['success'])

        # 更新されていないこと
        product.refresh_from_db()
        self.assertEqual(product.product_name, '単位桁数商品')

        # エラーメッセージ確認
        soup = BeautifulSoup(res_json['html'], 'html.parser')
        self.assertEqual('この値は 20 文字以下でなければなりません( 21 文字になっています)。', soup.select_one('#id_unit + .invalid-feedback').get_text())

    def test_3_2_2_4(self):
        '''更新処理（異常系：同一テナントで同じ商品名）'''
        # 商品カテゴリを1件作成
        c = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ',
            create_user=self.user,
            update_user=self.user,
        )

        # 同一テナントに商品名データを事前作成（名称違い）
        Product.objects.create(
            tenant=self.user.tenant,
            product_name='商品A',
            product_category=c,
            unit='個',
            unit_price='123.45',
            description='説明文A',
            create_user=self.user,
            update_user=self.user,
        )

        product2 = Product.objects.create(
            tenant=self.user.tenant,
            product_name='商品B',
            product_category=c,
            unit='束',
            unit_price='234.56',
            description='説明文B',
            create_user=self.user,
            update_user=self.user,
        )

        url = reverse('product_mst:update', args=[product2.id])
        data = {
            'product_name': '商品A',
            'unit_price': '234.56',
        }

        # レスポンス確認
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertFalse(res_json['success'])

        # 更新されていないこと
        product2.refresh_from_db()
        self.assertEqual(product2.product_name, '商品B')  # 更新されていない

        # エラーメッセージ確認
        soup = BeautifulSoup(res_json['html'], 'html.parser')
        self.assertEqual('同じ商品名が既に登録されています。', soup.select_one('#id_product_name + .invalid-feedback').get_text())

    def test_3_2_2_5(self):
        '''
        更新処理（異常系：存在しないデータの更新）
        '''
        url = reverse('product_mst:update', args=[99999])
        data = {
            'product_name': '更新テスト',
            'unit_price': '234.56',
        }

        # RequestFactoryでPOSTリクエスト生成
        request = self.factory.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.user
        setattr(request, 'session', self.client.session)

        # メッセージストレージをリクエストに付与
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # View呼び出し
        response = ProductUpdateView.as_view()(request, pk=99999)

        # JSONレスポンス構造確認
        self.assertJSONEqual(response.content, {'success': False})

        # ステータスコード確認
        self.assertEqual(response.status_code, 404)

        # messages.error 確認
        storage = list(messages)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, 'この商品は既に削除されています。')
        self.assertEqual(storage[0].level_tag, 'error')


    #----------------
    # DeleteView
    #----------------
    def test_4_1_1_1(self):
        '''
        削除処理（正常系）
        '''
        # 商品カテゴリを作成
        c = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ',
            create_user=self.user,
            update_user=self.user,
        )

        # 削除対象データ
        product = Product.objects.create(
            tenant=self.user.tenant,
            product_name='削除テスト',
            product_category=c,
            unit='個',
            unit_price='123.45',
            description='説明文A',
            create_user=self.user,
            update_user=self.user,
        )

        # 受注ヘッダ・明細を作成
        sales_order = SalesOrder.objects.create(
            tenant=self.user.tenant,
            sales_order_no='SO001',
            sales_order_date='2025-10-22',
            delivery_due_date='2025-10-25',
            create_user=self.user,
            update_user=self.user,
        )
        sales_order_detail = SalesOrderDetail.objects.create(
            tenant=self.user.tenant,
            sales_order=sales_order,
            line_no=1,
            product=product,
            quantity=2,
            master_unit_price='146.90',
            billing_unit_price='146.90',
            create_user=self.user,
            update_user=self.user,
        )

        url = reverse('product_mst:delete', args=[product.id])
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertTrue(res_json['success'])

        # メッセージ確認
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages) > 0)
        self.assertEqual(messages[0].message, '商品「削除テスト」を削除しました。')
        self.assertEqual(messages[0].level_tag, 'success')

        # 商品データの削除確認
        self.assertFalse(Product.objects.filter(id=product.id).exists())

        # 受注明細データの商品がNullになっていること
        sales_order_detail.refresh_from_db()
        self.assertIsNone(sales_order_detail.product)

    def test_4_1_2_1(self):
        '''削除処理（異常系：直リンク）'''
        # 商品カテゴリを作成
        c = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ1',
            create_user=self.user,
            update_user=self.user,
        )

        # 事前データ作成
        product = Product.objects.create(
            tenant=self.user.tenant,
            product_name='旧商品',
            product_category=c,
            unit='個',
            unit_price='123.45',
            description='旧説明文',
            create_user=self.user,
            update_user=self.user,
        )

        # 更新処理のURL作成
        url = reverse('product_mst:delete', args=[product.id])

        # ログアウト
        self.client.logout()

        # 処理実行
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # リダイレクト確認
        self.assertRedirects(response, f'/login/?next=/product_mst/{product.id}/delete/')

    def test_4_1_2_2(self):
        '''削除画面表示（異常系：権限不足）'''
        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        url = reverse('product_mst:delete', args=[1])
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_4_1_2_3(self):
        '''
        削除処理（異常系：存在しないデータの削除）
        '''
        url = reverse('product_mst:delete', args=[99999])

        # RequestFactoryでPOSTリクエスト生成
        request = self.factory.post(url,  HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.user
        setattr(request, 'session', self.client.session)

        # メッセージストレージをリクエストに付与
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # View呼び出し
        response = ProductDeleteView.as_view()(request, pk=99999)

        # JSONレスポンス構造確認
        self.assertJSONEqual(response.content, {'success': False})

        # ステータスコード確認
        self.assertEqual(response.status_code, 404)

        # messages.error 確認
        storage = list(messages)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, 'この商品は既に削除されています。')
        self.assertEqual(storage[0].level_tag, 'error')


    #----------------
    # BulkDeleteView
    #----------------
    def test_5_1_1_1(self):
        '''
        一括削除（正常系）
        '''
        # 商品カテゴリを作成
        c = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ',
            create_user=self.user,
            update_user=self.user,
        )

        # 商品データ
        product1 = Product.objects.create(
            tenant=self.user.tenant,
            product_name='商品A',
            product_category=c,
            unit='個',
            unit_price='123.45',
            description='説明文A',
            create_user=self.user,
            update_user=self.user,
        )

        product2 = Product.objects.create(
            tenant=self.user.tenant,
            product_name='商品B',
            product_category=c,
            unit='束',
            unit_price='123.45',
            description='説明文B',
            create_user=self.user,
            update_user=self.user,
        )

        # 受注データ作成
        sales_order = SalesOrder.objects.create(
            tenant=self.user.tenant,
            sales_order_no='SO-001',
            sales_order_date='2025-09-30',
            create_user=self.user,
            update_user=self.user,
        )

        sales_order_detail1 = SalesOrderDetail.objects.create(
            tenant=self.user.tenant,
            sales_order=sales_order,
            line_no=1,
            product=product1,
            quantity=2,
            master_unit_price='146.90',
            billing_unit_price='146.90',
            create_user=self.user,
            update_user=self.user,
        )

        sales_order_detail2 = SalesOrderDetail.objects.create(
            tenant=self.user.tenant,
            sales_order=sales_order,
            line_no=2,
            product=product2,
            quantity=2,
            master_unit_price='146.90',
            billing_unit_price='146.90',
            create_user=self.user,
            update_user=self.user,
        )

        # 処理実行
        url = reverse('product_mst:bulk_delete')
        response = self.client.post(
            url,
            {'ids': [product1.id, product2.id]},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # レスポンス確認
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertEqual('2件削除しました。', res_json['message'])

        # DB確認
        self.assertFalse(Product.objects.filter(id=product1.id).exists())
        self.assertFalse(Product.objects.filter(id=product2.id).exists())

        # 受注データの取引先がすべてNullになっていること
        sales_order_detail1.refresh_from_db()
        sales_order_detail2.refresh_from_db()
        self.assertIsNone(sales_order_detail1.product)
        self.assertIsNone(sales_order_detail2.product)

    def test_5_1_1_2(self):
        '''
        一括削除（正常系：指定なし）
        '''
        # 商品カテゴリを作成
        c = ProductCategory.objects.create(
            tenant=self.user.tenant,
            product_category_name='テストカテゴリ',
            create_user=self.user,
            update_user=self.user,
        )

        # 商品データ
        product1 = Product.objects.create(
            tenant=self.user.tenant,
            product_name='商品A',
            product_category=c,
            unit='個',
            unit_price='123.45',
            description='説明文A',
            create_user=self.user,
            update_user=self.user,
        )

        product2 = Product.objects.create(
            tenant=self.user.tenant,
            product_name='商品B',
            product_category=c,
            unit='束',
            unit_price='123.45',
            description='説明文B',
            create_user=self.user,
            update_user=self.user,
        )

        # 受注データ作成
        sales_order = SalesOrder.objects.create(
            tenant=self.user.tenant,
            sales_order_no='SO-001',
            sales_order_date='2025-09-30',
            create_user=self.user,
            update_user=self.user,
        )

        SalesOrderDetail.objects.create(
            tenant=self.user.tenant,
            sales_order=sales_order,
            line_no=1,
            product=product1,
            quantity=2,
            master_unit_price='146.90',
            billing_unit_price='146.90',
            create_user=self.user,
            update_user=self.user,
        )

        SalesOrderDetail.objects.create(
            tenant=self.user.tenant,
            sales_order=sales_order,
            line_no=2,
            product=product2,
            quantity=2,
            master_unit_price='146.90',
            billing_unit_price='146.90',
            create_user=self.user,
            update_user=self.user,
        )

        # 処理実行
        url = reverse('product_mst:bulk_delete')
        response = self.client.post(
            url,
            {'ids': []},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # リダイレクト確認
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('product_mst:list'))

        # メッセージがセットされていることを確認
        storage = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any('削除対象が選択されていません。' in str(m) for m in storage))

        # DB確認（削除されていないこと）
        self.assertTrue(Product.objects.filter(id=product1.id).exists())
        self.assertTrue(Product.objects.filter(id=product2.id).exists())

    def test_5_1_2_1(self):
        '''
        一括削除（異常系：直リンク）
        '''
        # 削除対象データ作成
        product1 = Product.objects.create(
            tenant=self.user.tenant,
            product_name='商品A',
            product_category=None,
            unit='個',
            unit_price='123.45',
            description='説明文A',
            create_user=self.user,
            update_user=self.user,
        )

        product2 = Product.objects.create(
            tenant=self.user.tenant,
            product_name='商品B',
            product_category=None,
            unit='束',
            unit_price='123.45',
            description='説明文B',
            create_user=self.user,
            update_user=self.user,
        )

        # ログアウト
        self.client.logout()

        # 処理実行
        url = reverse('product_mst:bulk_delete')
        response = self.client.post(
            url,
            {'ids': [product1.id, product2.id]},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # リダイレクト確認
        self.assertRedirects(response, '/login/?next=/product_mst/bulk_delete/')

        # DB確認
        self.assertTrue(Product.objects.filter(id=product1.id).exists())
        self.assertTrue(Product.objects.filter(id=product2.id).exists())

    def test_5_1_2_2(self):
        '''一括削除処理（異常系：権限不足）'''
        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        # 削除対象データ作成
        product1 = Product.objects.create(
            tenant=self.user.tenant,
            product_name='商品A',
            product_category=None,
            unit='個',
            unit_price='123.45',
            description='説明文A',
            create_user=self.user,
            update_user=self.user,
        )

        product2 = Product.objects.create(
            tenant=self.user.tenant,
            product_name='商品B',
            product_category=None,
            unit='束',
            unit_price='123.45',
            description='説明文B',
            create_user=self.user,
            update_user=self.user,
        )

        # 処理実行
        url = reverse('product_mst:bulk_delete')
        response = self.client.post(
            url,
            {'ids': [product1.id, product2.id]},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_5_1_2_3(self):
        '''一括削除処理（異常系：部分失敗）'''

        # 商品データ
        product = Product.objects.create(
            tenant=self.user.tenant,
            product_name='商品A',
            product_category=None,
            unit='個',
            unit_price='123.45',
            description='説明文A',
            create_user=self.user,
            update_user=self.user,
        )

        # 実在するIDと存在しないIDを混ぜる
        valid_id = str(product.id)
        nonexistent_id = str(product.id + 9999)
        ids = [valid_id, nonexistent_id]

        # RequestFactory で Ajax POST リクエスト作成
        url = reverse('product_mst:bulk_delete')
        request = self.factory.post(
            url,
            {'ids': ids},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        request.user = self.user
        setattr(request, 'session', self.client.session)

        # メッセージストレージを付与
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # View呼び出し
        response = ProductBulkDeleteView.as_view()(request)

        # ステータスコード確認
        self.assertEqual(response.status_code, 404)

        # JSONレスポンス内容確認
        self.assertJSONEqual(response.content, {'success': False})

        # メッセージ内容確認
        storage = list(messages)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, 'すでに削除されている商品が含まれています。')
        self.assertEqual(storage[0].level_tag, 'error')

        # 削除が実行されていないこと（ロールバック確認）
        self.assertTrue(Product.objects.filter(id=product.id).exists())


    #----------------
    # ExportCSV
    #----------------
    def _request_and_parse(self, url: str):
        '''エクスポートを叩いてレスポンスとCSV行を返す共通処理'''
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

        # 文字コード確認
        try:
            content = response.content.decode('utf-8')
        except UnicodeDecodeError:
            self.fail('CSVファイルの文字コードがutf-8ではありません。')

        # BOMがある場合も想定して除去
        if content.startswith('\ufeff'):
            content = content.lstrip('\ufeff')

        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        # ヘッダ確認
        self.assertEqual(rows[0], list(HEADER_MAP.keys()))
        return rows

    def _assert_csv_matches_queryset(self, rows, queryset):
        '''CSVの行とクエリセットを突き合わせ'''
        field_names = list(HEADER_MAP.values())

        # 並び順一致確認（id順 or order_by指定順）
        csv_first_column_values = [r[0] for r in rows[1:]]
        queryset_first_column_values = [
            str(getattr(p, field_names[0])) if getattr(p, field_names[0]) is not None else ''
            for p in queryset
        ]
        self.assertEqual(
            csv_first_column_values,
            queryset_first_column_values,
            'CSVの並び順がクエリセットと一致しません。',
        )

        # 内容一致確認
        for row, partner in zip(rows[1:], queryset):
            expected = []
            for field in field_names:
                display_method = f'get_{field}_display'
                if hasattr(partner, display_method):
                    value = getattr(partner, display_method)()
                else:
                    value = getattr(partner, field)
                expected.append(str(value) if value is not None else '')

            self.assertEqual(row, expected)

    def test_6_1_1_1(self):
        '''CSVエクスポート（正常系：n件）'''
        url = reverse('product_mst:export_csv')
        rows = self._request_and_parse(url)

        # 件数チェック（事前に8件のデータがある想定）
        self.assertEqual(len(rows) - 1, 13)

        data = Product.objects.filter(
            tenant=self.user.tenant,
            is_deleted=False
        ).order_by('id')

        self._assert_csv_matches_queryset(rows, data)

    def test_6_1_1_2(self):
        '''CSVエクスポート（正常系：商品名検索）'''
        target = '003'
        url = reverse('product_mst:export_csv') + f'?search_product_name={target}'
        rows = self._request_and_parse(url)
        data = Product.objects.filter(
            product_name__icontains=target,
            tenant=self.user.tenant,
            is_deleted=False
        ).order_by('id')
        self.assertEqual(len(rows) - 1, data.count())
        self._assert_csv_matches_queryset(rows, data)

    def test_6_1_1_3(self):
        '''CSVエクスポート（正常系：0件）'''
        Product.objects.all().delete()
        url = reverse('product_mst:export_csv')
        rows = self._request_and_parse(url)
        # ヘッダのみ
        self.assertEqual(len(rows), 1)

    def test_6_1_1_4(self):
        '''CSVエクスポート（正常系：参照ユーザー）'''
        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        url = reverse('product_mst:export_csv')
        rows = self._request_and_parse(url)

        data = Product.objects.filter(
            tenant=self.user.tenant,
            is_deleted=False
        ).order_by('id')

        self.assertEqual(len(rows) - 1, data.count())
        self._assert_csv_matches_queryset(rows, data)

    def _create_max_data(self, n):
        data = []
        for i in range(n):
            p = Product.objects.create(
                tenant=self.user.tenant,
                product_name=f'商品{i}',
                unit_price='123.45',
                create_user=self.user,
                update_user=self.user,
            )
            data.append(p)
        return data

    def test_6_1_1_5(self):
        '''CSVエクスポート（正常系：上限数以上）'''
        self._create_max_data(settings.MAX_EXPORT_ROWS + 1)
        url = reverse('product_mst:export_check')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('warning', data)
        self.assertEqual('出力件数が上限（10,000件）を超えています。先頭10,000件のみを出力します。', data['warning'])
        self.assertNotIn('ok', data)

    def test_6_1_2_1(self):
        '''CSVエクスポート（異常系：直リンク）'''
        url = reverse('product_mst:export_csv')

        # ログアウト
        self.client.logout()

        # アクセス実行
        response = self.client.get(url)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # リダイレクト確認
        self.assertRedirects(response, '/login/?next=/product_mst/export/csv')

        # CSVが返却されていないことを確認
        if 'Content-Type' in response:
            self.assertNotEqual(response['Content-Type'], 'text/csv')


    #----------------
    # ImportCSV
    #-----------------
    def _make_csv_file(self, rows, encoding='utf-8', header=None):
        '''
        テスト用CSVファイルの作成
        '''
        if header is None:
            fieldnames = ['商品名', '商品カテゴリ', '単価', '単位', '説明']
        else:
            fieldnames = header
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        output.seek(0)
        bytes_file = io.BytesIO(output.getvalue().encode(encoding=encoding))
        bytes_file.name = 'test.csv'
        return bytes_file

    def test_7_1_1_1(self):
        '''CSVインポート（正常系：n件）'''
        url = reverse('product_mst:import_csv')
        rows = [
            {'商品名': '商品A', '商品カテゴリ': '食品', '単価': '100', '単位': '個', '説明': '説明A'},
            {'商品名': '商品B', '商品カテゴリ': '文房具', '単価': '200', '単位': '箱', '説明': '説明B'},
        ]

        # 商品データを全削除
        Product.objects.all().delete()

        # CSVファイルの作成
        file = self._make_csv_file(rows)

        # レスポンス取得
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)
        # メッセージ確認
        self.assertEqual('2件をインポートしました。', res_json['message'])

        products = Product.objects.filter(tenant=self.user.tenant)
        self.assertEqual(products.count(), 2)

       # 登録値の確認
        products = Product.objects.order_by('product_name')
        for row, product in zip(sorted(rows, key=lambda x: x['商品名']), products):
            self.assertEqual(product.product_name, row['商品名'])
            self.assertEqual(product.product_category.product_category_name, row['商品カテゴリ'])
            self.assertEqual(product.unit_price, Decimal(row['単価']))
            self.assertEqual(product.unit, row['単位'])
            self.assertEqual(product.description, row['説明'])
            self.assertEqual(product.is_deleted, False)
            self.assertEqual(product.create_user, self.user)
            self.assertEqual(product.update_user, self.user)
            self.assertEqual(product.tenant, self.user.tenant)
            self.assertLessEqual(abs((product.created_at - timezone.now()).total_seconds()), 5)
            self.assertLessEqual(abs((product.updated_at - timezone.now()).total_seconds()), 5)

    def test_7_1_1_2(self):
        '''CSVインポート（正常系：shift-jis）'''
        url = reverse('product_mst:import_csv')

        # データを削除しておく
        Product.objects.all().delete()

        rows = [
            {'商品名': '商品SJIS', '商品カテゴリ': '食品', '単価': '100', '単位': '個', '説明': '説明A'},
        ]
        file = self._make_csv_file(rows, encoding='cp932')

        # レスポンス確認
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # メッセージ確認
        self.assertEqual('1件をインポートしました。', res_json['message'])

        # 件数確認
        self.assertEqual(Product.objects.count(), 1)

    def test_7_1_1_3(self):
        '''CSVインポート（正常系：改行混在 CRLF/LF）'''
        url = reverse('product_mst:import_csv')

        # データを削除しておく
        Product.objects.all().delete()

        rows = [
            {
                '商品名': '改行混在商品',
                '商品カテゴリ': '食品',
                '単価': '234.56',
                '単位': '箱',
                '説明': '改行混在商品です',
            },
        ]

        # 改行混在CSVを手動で生成（\r\n + \n）
        header = list(rows[0].keys())
        lines = [','.join(header)] + [','.join(r.values()) for r in rows]
        csv_content = '\r\n'.join(lines[:-1]) + '\n' + lines[-1]
        file = io.BytesIO(csv_content.encode('utf-8'))
        file.name = 'test.csv'

        response = self.client.post(url, {'file': file})
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertEqual('1件をインポートしました。', res_json['message'])

        # 件数確認
        self.assertEqual(Product.objects.count(), 1)

        # 登録値の確認
        product = Product.objects.first()
        self.assertEqual(product.product_name, '改行混在商品')
        self.assertEqual(product.product_category.product_category_name, '食品')
        self.assertEqual(product.unit_price, Decimal('234.56'))
        self.assertEqual(product.unit, '箱')
        self.assertEqual(product.description, '改行混在商品です')
        self.assertEqual(product.is_deleted, False)
        self.assertEqual(product.create_user, self.user)
        self.assertEqual(product.update_user, self.user)
        self.assertEqual(product.tenant, self.user.tenant)
        self.assertLessEqual(abs((product.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((product.updated_at - timezone.now()).total_seconds()), 5)

    def test_7_1_1_4(self):
        '''CSVインポート（正常系：空行スキップ）'''
        url = reverse('product_mst:import_csv')

        # データを削除しておく
        Product.objects.all().delete()

        # データの作成
        rows = [
            {
                '商品名': '空行商品',
                '商品カテゴリ': '文房具',
                '単価': '234.56',
                '単位': '箱',
                '説明': '空行商品テストです。',
            },
        ]
        file = self._make_csv_file(rows)
        file = io.BytesIO((file.getvalue() + b'\n\n').strip())  # 空行を追加
        file.name = 'test.csv'

        # レスポンス確認
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # メッセージ確認
        self.assertEqual('1件をインポートしました。', res_json['message'])

        # 件数確認
        self.assertEqual(Product.objects.count(), 1)

        # 登録値の確認
        product = Product.objects.first()
        self.assertEqual(product.product_name, '空行商品')
        self.assertEqual(product.product_category.product_category_name, '文房具')
        self.assertEqual(product.unit_price, Decimal('234.56'))
        self.assertEqual(product.unit, '箱')
        self.assertEqual(product.description, '空行商品テストです。')
        self.assertEqual(product.is_deleted, False)
        self.assertEqual(product.create_user, self.user)
        self.assertEqual(product.update_user, self.user)
        self.assertEqual(product.tenant, self.user.tenant)
        self.assertLessEqual(abs((product.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((product.updated_at - timezone.now()).total_seconds()), 5)

    def test_7_1_1_5(self):
        '''CSVインポート（正常系：ヘッダ順入替え）'''
        url = reverse('product_mst:import_csv')

        # データを削除しておく
        Product.objects.all().delete()

        # データの作成
        header = ['商品カテゴリ', '商品名', '単価', '単位', '説明']
        rows = [
            {
                '商品カテゴリ': '文房具',
                '商品名': '入れ替え商品',
                '単価': '234.56',
                '単位': '箱',
                '説明': '入れ替えテストです。',
            },
        ]
        file = self._make_csv_file(rows, header=header)

        # レスポンス確認
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # メッセージ確認
        self.assertEqual('1件をインポートしました。', res_json['message'])

        # 件数確認
        self.assertEqual(Product.objects.count(), 1)

        # 登録値の確認
        product = Product.objects.first()
        self.assertEqual(product.product_name, '入れ替え商品')
        self.assertEqual(product.product_category.product_category_name, '文房具')
        self.assertEqual(product.unit_price, Decimal('234.56'))
        self.assertEqual(product.unit, '箱')
        self.assertEqual(product.description, '入れ替えテストです。')
        self.assertEqual(product.is_deleted, False)
        self.assertEqual(product.create_user, self.user)
        self.assertEqual(product.update_user, self.user)
        self.assertEqual(product.tenant, self.user.tenant)
        self.assertLessEqual(abs((product.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((product.updated_at - timezone.now()).total_seconds()), 5)

    def test_7_1_2_1(self):
        '''CSVインポート（異常系：直リンク）'''
        self.client.logout()
        url = reverse('product_mst:import_csv')

        # データを削除しておく
        Product.objects.all().delete()

        rows = [
            {
                '商品名': 'テスト商品A',
                '商品カテゴリ': '文房具',
                '単価': '234.56',
                '単位': '箱',
                '説明': '重複商品テストです。',
            },
        ]

        # CSVファイルの作成
        file = self._make_csv_file(rows)

        # レスポンスを取得
        response = self.client.post(url, {'file': file})

        # 登録されていないことを確認
        self.assertEqual(Product.objects.count(), 0)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # リダイレクト先を確認
        self.assertRedirects(response, r'/login/?next=/product_mst/import/csv')


    def test_7_1_2_2(self):
        '''CSVインポート（異常系：権限不足）'''
        # 現在ログイン中ユーザーをviewer権限に変更
        self.user.privilege = '3'
        self.user.save()
        url = reverse('product_mst:import_csv')

        # データを削除しておく
        Product.objects.all().delete()

        # テストデータ
        rows = [
            {
                '商品名': 'テスト商品A',
                '商品カテゴリ': '文房具',
                '単価': '234.56',
                '単位': '箱',
                '説明': '重複商品テストです。',
            },
        ]

        # CSVファイルの作成
        file = self._make_csv_file(rows)

        # レスポンスを取得
        response = self.client.post(url, {'file': file})

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

        # 登録されていないことを確認
        self.assertEqual(Product.objects.count(), 0)

    def test_7_1_2_3(self):
        '''CSVインポート（異常系：複数フィールド・複数行エラー）'''
        url = reverse('product_mst:import_csv')

        # データを削除しておく
        Product.objects.all().delete()

        rows = [
            {
                '商品名': '商品' + 'A' * 260,
                '商品カテゴリ': '食品',
                '単価': '123.45',
                '単位': '個',
                '説明': '説明' + 'B' * 600,
            },
            {
                '商品名': '商品B',
                '商品カテゴリ': '食品',
                '単価': 'number',
                '単位': '個' * 21,
                '説明': '説明C',
            },
        ]
        file = self._make_csv_file(rows)

        res = self.client.post(url, {'file': file})
        self.assertEqual(res.status_code, 400)
        res_json = json.loads(res.content)

        # 期待メッセージ確認
        self.assertEqual('CSVに問題があります。', res_json.get('error', ''))
        self.assertIn('2行目:', res_json.get('details', '')[0])
        self.assertIn('商品名', res_json.get('details', '')[0])
        self.assertIn('説明', res_json.get('details', '')[0])
        self.assertIn('3行目:', res_json.get('details', '')[1])
        self.assertIn('単価', res_json.get('details', '')[1])
        self.assertIn('単位', res_json.get('details', '')[1])

    def test_7_1_2_4(self):
        '''CSVインポート（異常系：カテゴリ未登録）'''
        url = reverse('product_mst:import_csv')
        rows = [
            {
                '商品名': 'カテゴリテスト',
                '商品カテゴリ': '未登録カテゴリ',
                '単価': '234.56',
                '単位': '箱',
                '説明': 'カテゴリテストです。',
            },
        ]

        file = self._make_csv_file(rows)
        res = self.client.post(url, {'file': file})
        self.assertEqual(res.status_code, 400)
        res_json = json.loads(res.content)
        self.assertEqual('CSVに問題があります。', res_json.get('error', ''))
        self.assertEqual('2行目: 商品カテゴリ「未登録カテゴリ」が存在しません。', res_json.get('details', '')[0])

    def test_7_1_2_5(self):
        '''CSVインポート（異常系：商品名重複）'''
        url = reverse('product_mst:import_csv')
        Product.objects.create(
            tenant=self.user.tenant,
            product_name='重複商品',
            product_category=ProductCategory.objects.first(),
            unit='個',
            unit_price=100,
            description='既存',
            create_user=self.user,
            update_user=self.user,
        )
        rows = [
            {
                '商品名': '重複商品',
                '商品カテゴリ': '文房具',
                '単価': '234.56',
                '単位': '箱',
                '説明': '重複商品テストです。',
            },
        ]

        file = self._make_csv_file(rows)
        res = self.client.post(url, {'file': file})
        self.assertEqual(res.status_code, 400)
        res_json = json.loads(res.content)
        self.assertEqual('CSVに問題があります。', res_json.get('error', ''))
        self.assertEqual('2行目: 商品「重複商品」は既に存在します。', res_json.get('details', '')[0])

    def test_7_1_2_6(self):
        '''CSVインポート（異常系：部分失敗）'''
        url = reverse('product_mst:import_csv')

        # データを削除しておく
        Product.objects.all().delete()

        # CSVファイルの作成
        rows = [
            {
                '商品名': 'テスト商品A',
                '商品カテゴリ': '文房具',
                '単価': '234.56',
                '単位': '箱',
                '説明': '重複商品テストです。',
            },
            {
                '商品名': '',
                '商品カテゴリ': '文房具',
                '単価': '234.56',
                '単位': '箱',
                '説明': '重複商品テストです。',
            },
        ]
        file = self._make_csv_file(rows)

        # レスポンス確認
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)

        # ステータスコード確認
        self.assertEqual(response.status_code, 400)

        # エラーメッセージ確認
        self.assertEqual('CSVに問題があります。', res_json['error'])
        self.assertTrue(any('必須' in s for s in res_json['details']))

        # 件数確認
        self.assertEqual(Product.objects.count(), 0)

    def test_7_1_2_7(self):
        '''CSVインポート（異常系：ヘッダ欠落）'''
        url = reverse('product_mst:import_csv')

        header = ['商品名', '商品カテゴリ', '単価', '説明']
        rows = [
            {
                '商品名': 'テスト商品',
                '商品カテゴリ': '文房具',
                '単価': '234.56',
                '説明': '重複商品テストです。',
            },
        ]
        file = self._make_csv_file(rows, header=header)

        res = self.client.post(url, {'file': file})
        self.assertEqual(res.status_code, 400)
        res_json = json.loads(res.content)
        self.assertEqual('CSVヘッダが正しくありません。', res_json.get('error', ''))
        self.assertEqual("不足: ['単位'] / 期待: ['商品名', '商品カテゴリ', '単価', '単位', '説明'] / 実際: ['商品名', '商品カテゴリ', '単価', '説明']", res_json['details'])

    def test_7_1_2_8(self):
        '''CSVインポート（異常系：ヘッダ過多）'''
        url = reverse('product_mst:import_csv')
        rows = [
            {
                '商品名': 'テスト商品',
                '商品カテゴリ': '文房具',
                '単価': '234.56',
                '単位': '箱',
                '説明': '重複商品テストです。',
                'テストカラム': '過多テスト',
            },
        ]
        file = self._make_csv_file(rows, header=['商品名', '商品カテゴリ', '単価', '単位', '説明', 'テストカラム'])

        res = self.client.post(url, {'file': file})
        self.assertEqual(res.status_code, 400)
        res_json = json.loads(res.content)
        self.assertEqual('想定外のヘッダが含まれています。', res_json.get('error', ''))
        self.assertEqual("不要: ['テストカラム'] / 許可: ['商品名', '商品カテゴリ', '単価', '単位', '説明']", res_json['details'])

    def test_7_1_2_9(self):
        '''CSVインポート（異常系：ヘッダ重複）'''
        url = reverse('product_mst:import_csv')
        rows = [
            {
                '商品名': 'テスト商品',
                '商品カテゴリ': '文房具',
                '単価': '234.56',
                '単位': '箱',
                '単位': 'セット',
                '説明': '重複商品テストです。',
            },
        ]
        file = self._make_csv_file(rows, header=['商品名', '商品カテゴリ', '単価', '単位', '単位', '説明'])

        res = self.client.post(url, {'file': file})
        self.assertEqual(res.status_code, 400)
        res_json = json.loads(res.content)
        self.assertEqual('CSVヘッダが重複しています。', res_json.get('error', ''))
        self.assertEqual("重複: ['単位']", res_json['details'])

    def test_7_1_2_10(self):
        '''CSVインポート（異常系：拡張子不正）'''
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Product.objects.all().delete()

         # CSVファイルの作成
        file = SimpleUploadedFile('test.txt', b'dummy text', content_type='text/plain')

        # レスポンス確認
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)

        # ステータスコード確認
        self.assertEqual(response.status_code, 400)

        # エラーメッセージ確認
        self.assertEqual('CSVファイル（.csv）のみアップロード可能です。', res_json['error'])

        # 件数確認
        self.assertEqual(Product.objects.count(), 0)

    def test_7_1_2_11(self):
        '''CSVインポート（異常系：サイズ超過）'''
        url = reverse('product_mst:import_csv')

        # データを削除しておく
        Product.objects.all().delete()

        # サイズ超過分のデータ値作成
        large_content = b'a' * (settings.MAX_FILE_SIZE + 1)

        # CSVファイルの作成
        file = SimpleUploadedFile('large.csv', large_content, content_type='text/csv')

        # レスポンス取得
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)

        # ステータスコード確認
        self.assertEqual(response.status_code, 400)

        # エラーメッセージ確認
        self.assertEqual('ファイルサイズが上限を超えています。', res_json['error'])

        # 件数確認
        self.assertEqual(Product.objects.count(), 0)
