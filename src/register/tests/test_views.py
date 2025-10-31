from django.conf import settings
from django.test import TestCase, Client, RequestFactory
from register.models import UserGroup, CustomUser
from sales_order.models import SalesOrder
from register.views import UserUpdateView, UserDeleteView, UserBulkDeleteView, HEADER_MAP
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse
from register.constants import EMPLOYMENT_STATUS_CHOICES, PRIVILEGE_CHOICES, PRIVILEGE_SYSTEM, PRIVILEGE_MANAGER, PRIVILEGE_VIEWER
from tenant_mst.models import Tenant
from bs4 import BeautifulSoup
from django.utils import timezone
from django.contrib import messages
import csv
import io
import json


class RegisterViewsTests(TestCase):
    '''ユーザーマスタ 単体テスト'''

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

        # 基本は管理者ユーザーで実施
        self.user = get_user_model().objects.get(pk=2)
        self.client.login(email='manager@example.com', password='pass')

    #----------------
    # ListView
    #----------------
    def test_1_1_1_1(self):
        '''初期表示（正常系: データあり）'''
        # レスポンス取得
        response = self.client.get(reverse('register:list'))

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['users']
        self.assertEqual(list.count(), 9)
        self.assertTrue(all(tid == 1 for tid in list.values_list('tenant_id', flat=True)))

        # 要素の取得を確認
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertIsNotNone(soup.select_one('#create-btn'))
        self.assertIsNotNone(soup.select_one('.edit-btn'))
        self.assertIsNotNone(soup.select_one('#bulk-delete-btn'))
        self.assertIsNotNone(soup.select_one('#user_group_manage'))

    def test_1_1_1_2(self):
        '''初期表示（正常系: 参照権限）'''
        # 更新ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='editor@example.com', password='pass')

        # レスポンス取得
        response = self.client.get(reverse('register:list'))

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['users']
        self.assertEqual(list.count(), 9)
        self.assertTrue(all(tid == 1 for tid in list.values_list('tenant_id', flat=True)))

        # 要素の取得を確認
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertIsNone(soup.select_one('#create-btn'))
        self.assertIsNotNone(soup.select_one('.edit-btn'))
        self.assertIsNone(soup.select_one('#bulk-delete-btn'))
        self.assertIsNone(soup.select_one('#user_group_manage'))

    def test_1_1_1_3(self):
        '''検索処理（正常系: 結果0件）'''
        # 検索値

        # レスポンス取得
        response = self.client.get(reverse('register:list'), {'search_keyword': 'ZZZZZZZ',})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['users']
        self.assertEqual(list.count(), 0)

    def test_1_1_2_1(self):
        '''一覧画面表示（異常系: 直リンク）'''
        url = reverse('register:list')

        # 直リンク状態でアクセス
        self.client.logout()
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # 遷移後の画面確認
        self.assertRedirects(response, '/login/?next=/register/')

    def test_1_2_1_1(self):
        '''検索処理（正常系: キーワード->ユーザー名 or ユーザー名カナ or メールアドレス or 電話番号 or 所属グループ）'''
        # 検索値
        key = '999'

        # レスポンス取得
        response = self.client.get(reverse('register:list'), {'search_keyword': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['users']
        self.assertEqual(list.count(), 5)

        # プロパティに "999" が含まれていることを確認
        for p in list:
            text_values = [
                str(p.username or ''),
                str(p.username_kana or ''),
                str(p.email or ''),
                str(p.tel_number or ''),
                ', '.join(p.groups_custom.values_list('group_name', flat=True)),
            ]
            # どれか一つでも '999' を含めばOK
            self.assertTrue(
                any(key in v for v in text_values),
                f"{p.id} のいずれのプロパティにも '{key}' が含まれていません。: {text_values}"
            )

        # 検索後のフォーム確認
        self.assertEqual(key, response.context['form']['search_keyword'].value())

    def test_1_2_1_2(self):
        '''検索処理（正常系: キーワード->性別）'''
        # 検索値
        key = '男'

        # レスポンス取得
        response = self.client.get(reverse('register:list'), {'search_keyword': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['users']
        self.assertEqual(list.count(), 7)

        # プロパティに検索値が含まれていることを確認
        for p in list:
            text_values = [
                str(p.get_gender_display() or ''),
            ]
            # どれか一つでも検索値を含めばOK
            self.assertTrue(
                any(key in v for v in text_values),
                f"{p.id} のいずれのプロパティにも '{key}' が含まれていません。: {text_values}"
            )

        # 検索後のフォーム確認
        self.assertEqual(key, response.context['form']['search_keyword'].value())

    def test_1_2_1_3(self):
        '''検索処理（正常系: キーワード->雇用状態）'''
        # 検索値
        key = '休'

        # レスポンス取得
        response = self.client.get(reverse('register:list'), {'search_keyword': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['users']
        self.assertEqual(list.count(), 1)

        # プロパティに検索値が含まれていることを確認
        for p in list:
            text_values = [
                str(p.get_employment_status_display() or ''),
            ]
            # どれか一つでも検索値を含めばOK
            self.assertTrue(
                any(key in v for v in text_values),
                f"{p.id} のいずれのプロパティにも '{key}' が含まれていません。: {text_values}"
            )

        # 検索後のフォーム確認
        self.assertEqual(key, response.context['form']['search_keyword'].value())

    def test_1_2_1_4(self):
        '''検索処理（正常系: キーワード->権限）'''
        # 検索値
        key = '照'

        # レスポンス取得
        response = self.client.get(reverse('register:list'), {'search_keyword': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['users']
        self.assertEqual(list.count(), 1)

        # プロパティに検索値が含まれていることを確認
        for p in list:
            text_values = [
                str(p.get_privilege_display() or ''),
            ]
            # どれか一つでも検索値を含めばOK
            self.assertTrue(
                any(key in v for v in text_values),
                f"{p.id} のいずれのプロパティにも '{key}' が含まれていません。: {text_values}"
            )

        # 検索後のフォーム確認
        self.assertEqual(key, response.context['form']['search_keyword'].value())

    def test_1_2_1_5(self):
        '''検索処理（正常系: ユーザー名）'''
        # 検索値
        key = 'system'

        # レスポンス取得
        response = self.client.get(reverse('register:list'), {'search_username': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['users']
        self.assertEqual(list.count(), 1)
        self.assertEqual('system_user', list[0].username)
        self.assertEqual(key, response.context['form']['search_username'].value())

    def test_1_2_1_6(self):
        '''検索処理（正常系: メールアドレス）'''
        # 検索値
        key = 'm@'

        # レスポンス取得
        response = self.client.get(reverse('register:list'), {'search_email': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['users']
        self.assertEqual(list.count(), 1)
        self.assertEqual('system@example.com', list[0].email)
        self.assertEqual(key, response.context['form']['search_email'].value())

    def test_1_2_1_7(self):
        '''検索処理（正常系: 性別）'''
        # 検索値
        key = '1'

        # レスポンス取得
        response = self.client.get(reverse('register:list'), {'search_gender': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['users']
        self.assertEqual(list.count(), 1)
        self.assertEqual('manager_user', list[0].username)
        self.assertEqual(key, response.context['form']['search_gender'].value())

    def test_1_2_1_8(self):
        '''検索処理（正常系: 電話番号）'''
        # 検索値
        key = '7777'

        # レスポンス取得
        response = self.client.get(reverse('register:list'), {'search_tel_number': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['users']
        self.assertEqual(list.count(), 1)
        self.assertEqual('editor_user', list[0].username)
        self.assertEqual(key, response.context['form']['search_tel_number'].value())

    def test_1_2_1_9(self):
        '''検索処理（正常系: 雇用状態）'''
        # 検索値
        key_label = '休職中'
        key_value = [k for k, v in EMPLOYMENT_STATUS_CHOICES if v == key_label][0]

        # レスポンス取得
        response = self.client.get(reverse('register:list'), {'search_employment_status': key_value})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['users']
        self.assertEqual(list.count(), 1)
        self.assertEqual('user_4', list[0].username)
        self.assertEqual(key_value, response.context['form']['search_employment_status'].value())

    def test_1_2_1_10(self):
        '''検索処理（正常系: 権限）'''
        # 検索値
        key_label = 'システム'
        key_value = [k for k, v in PRIVILEGE_CHOICES if v == key_label][0]

        # レスポンス取得
        response = self.client.get(reverse('register:list'), {'search_privilege': key_value})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['users']
        self.assertEqual(list.count(), 1)
        self.assertEqual('system_user', list[0].username)
        self.assertEqual(key_value, response.context['form']['search_privilege'].value())

    def test_1_2_1_11(self):
        '''検索処理（正常系: 所属グループ）'''
        # 検索値
        key = '999'
        obj = UserGroup.objects.get(group_name__icontains=key)
        pk = obj.pk

        # レスポンス取得
        response = self.client.get(reverse('register:list'), {'search_user_group': pk})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['users']
        self.assertEqual(list.count(), 1)
        self.assertEqual('manager_user', list[0].username)
        self.assertEqual(str(pk), response.context['form']['search_user_group'].value())

    def test_1_2_1_12(self):
        """ページング（正常系: 1ページあたり20件、21件目が次ページに表示）"""
        url = reverse('register:list')

        # ログイン
        self.client.force_login(self.user)

        # テスト初期データを削除
        CustomUser.objects.exclude(pk=self.user.pk).delete() # 自分のユーザーは対象外

        # 21件作成（ページング確認用）
        CustomUser.objects.bulk_create([
            CustomUser(
                tenant=self.user.tenant,
                username=f'user_{i+1:02}',
                email=f'mail_{i+1:02}@example.com',
                create_user=self.user,
                update_user=self.user,
            )
            for i in range(20)  # 自分自身と20件で合計21件にする
        ])

        # 1ページ目
        response_page1 = self.client.get(url)
        self.assertEqual(response_page1.status_code, 200)

        users_p1 = response_page1.context['users']
        self.assertEqual(len(users_p1), 20, '1ページ目の件数が20件であること')
        self.assertFalse(any('user_21' in p.username for p in users_p1))

        # 2ページ目
        response_page2 = self.client.get(url + '?page=2')
        self.assertEqual(response_page2.status_code, 200)

        users_p2 = response_page2.context['users']
        self.assertEqual(len(users_p2), 1, '2ページ目の件数が1件であること')
        self.assertTrue(any('user_20' in p.username for p in users_p2))

    #----------------
    # CreateView
    #----------------
    def test_2_1_1_1(self):
        '''登録画面表示（正常系）'''
        # レスポンス取得
        response = self.client.get(reverse('register:create'))

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # JSONをロード
        data = json.loads(response.content)
        html = data['html']

        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(html, 'html.parser')
        modal_title = soup.select_one('.modal-title').get_text(strip=True)

        # モーダルタイトル確認
        self.assertEqual(modal_title, 'ユーザー: 新規登録')

    def test_2_1_2_1(self):
        '''登録画面表示（異常系：直リンク）'''
        url = reverse('register:create')

        # 直リンク状態でアクセス
        self.client.logout()
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # 遷移後の画面確認
        self.assertRedirects(response, '/login/?next=/register/create/')

    def test_2_1_2_2(self):
        '''登録画面表示（異常系：権限不足）'''

        # 更新権限ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='editor@example.com', password='pass')

        url = reverse('register:create')
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_2_2_1_1(self):
        """2-2-1-1: 登録処理（正常）"""
        url = reverse('register:create')
        data = {
            'username': 'テストユーザー',
            'username_kana': 'テストユーザー',
            'email': 'test@example.com',
            'tel_number': '090-1111-2222',
            'gender': '1',
            'employment_status': '1',
            'privilege': '2',
        }

        before_count = CustomUser.objects.filter(tenant=self.user.tenant).count()

        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # DB件数確認
        after_count = CustomUser.objects.filter(tenant=self.user.tenant).count()
        self.assertEqual(after_count, before_count + 1, '登録後に1件追加されていること')

        # 登録内容確認
        obj = CustomUser.objects.filter(email='test@example.com').first()
        self.assertIsNotNone(obj)
        self.assertEqual(obj.username, 'テストユーザー')
        self.assertEqual(obj.is_deleted, False)
        self.assertEqual(obj.create_user, self.user)
        self.assertEqual(obj.update_user, self.user)
        self.assertEqual(obj.tenant, self.user.tenant)
        self.assertLessEqual(abs((obj.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((obj.updated_at - timezone.now()).total_seconds()), 5)

        # メッセージ確認
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('ユーザー「テストユーザー」を登録しました。' in m for m in messages))

    def test_2_2_1_2(self):
        '''登録処理（正常系: 異なるテナントで同じユーザー名'''
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
            privilege=PRIVILEGE_MANAGER,
            tenant=self.tenant1
        )

        # ユーザーを作成してテナント2に所属
        self.user2 = get_user_model().objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass',
            privilege=PRIVILEGE_MANAGER,
            tenant=self.tenant2
        )

        url = reverse('register:create')
        data = {
            'username': '重複ユーザー',
            'username_kana': 'チョウフクユーザー',
            'email': 'a@example.com',
            'tel_number': '090-1111-2222',
            'gender': '1',
            'employment_status': '1',
            'privilege': '2',
        }

        # テナント1で登録
        self.client.login(email='user1@example.com', password='pass')
        response = self.client.post(
            url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])

        data = {
            'username': '重複ユーザー',
            'username_kana': 'チョウフクユーザー',
            'email': 'b@example.com',
            'tel_number': '090-1111-2222',
            'gender': '1',
            'employment_status': '1',
            'privilege': '2',
        }

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
        t1 = CustomUser.objects.filter(tenant=self.tenant1, username='重複ユーザー')
        t2 = CustomUser.objects.filter(tenant=self.tenant2, username='重複ユーザー')

        # 件数確認
        self.assertEqual(t1.count(), 1)
        self.assertEqual(t2.count(), 1)

    def test_2_2_1_3(self):
        '''登録処理（正常系: 同一テナントで同じユーザー名）'''
        url = reverse('register:create')
        data = {
            'username': '重複ユーザー',
            'username_kana': 'チョウフクユーザー',
            'email': 'a@example.com',
            'tel_number': '090-1111-2222',
            'gender': '1',
            'employment_status': '1',
            'privilege': '2',
        }

        # テナント1で登録
        response = self.client.post(
            url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])

        data = {
            'username': '重複ユーザー',
            'username_kana': 'チョウフクユーザー',
            'email': 'b@example.com',
            'tel_number': '090-1111-2222',
            'gender': '1',
            'employment_status': '1',
            'privilege': '2',
        }

        # テナント2で同じ名前を登録
        response = self.client.post(
            url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])

        # DB確認
        t1 = CustomUser.objects.filter(tenant=self.user.tenant, email='a@example.com')
        t2 = CustomUser.objects.filter(tenant=self.user.tenant, email='b@example.com')

        # 件数確認
        self.assertEqual(t1.count(), 1)
        self.assertEqual(t2.count(), 1)

    def test_2_2_2_1(self):
        '''
        登録処理（異常系: 直リンク）
        '''
        url = reverse('register:create')

        # ログインせずにアクセス
        self.client.logout()

        data = {
            'username': 'テストユーザー',
            'username_kana': 'テストユーザー',
            'email': 'test@example.com',
            'tel_number': '090-1111-2222',
            'gender': '1',
            'employment_status': '1',
            'privilege': '2',
        }

        # 処理実行
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # レスポンス確認
        self.assertEqual(response.status_code, 302)

    def test_2_2_2_2(self):
        '''
        登録処理（異常系: 権限不足）
        '''
        url = reverse('register:create')

        # 更新ユーザーでログイン
        self.user = get_user_model().objects.get(pk=2)
        self.client.login(email='editor@example.com', password='pass')

        data = {
            'username': 'テストユーザー',
            'username_kana': 'テストユーザー',
            'email': 'test@example.com',
            'tel_number': '090-1111-2222',
            'gender': '1',
            'employment_status': '1',
            'privilege': '2',
        }

        # 処理実行
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # レスポンス確認
        self.assertEqual(response.status_code, 403)

    def test_2_2_2_3(self):
        '''
        登録処理（異常系: 直リンク）
        '''
        url = reverse('register:create')

        # ログインせずにアクセス
        self.client.logout()

        data = {
            'username': 'テストユーザー',
            'username_kana': 'テストユーザー',
            'email': 'test@@example.com',
            'tel_number': '090-1111-2222',
            'gender': '1',
            'employment_status': '1',
            'privilege': '2',
        }

        # 処理実行
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # レスポンス確認
        self.assertEqual(response.status_code, 302)

    def test_2_2_2_4(self):
        '''登録処理（異常系: 異なるテナント内重複）'''
        url = reverse('register:create')

        # 先に1件目を登録
        data1 = {
            'username': 'テストユーザー',
            'username_kana': 'テストユーザー',
            'email': 'test@example.com',
            'tel_number': '090-1111-2222',
            'gender': '1',
            'employment_status': '1',
            'privilege': '2',
        }
        response1 = self.client.post(url, data1, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response1.status_code, 200)
        res_json1 = json.loads(response1.content)
        self.assertTrue(res_json1['success'])

        # 同じメールアドレスで2件目を登録
        data2 = {
            'username': 'テストユーザー2',
            'username_kana': 'テストユーザー',
            'email': 'test@example.com',
            'tel_number': '090-1111-2222',
            'gender': '0',
            'employment_status': '2',
            'privilege': '3',
        }
        response2 = self.client.post(url, data2, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response2.status_code, 200)
        res_json2 = json.loads(response2.content)
        self.assertFalse(res_json2['success'])

        # DBに2件目は登録されていないことを確認
        self.assertEqual(CustomUser.objects.filter(email='test@example.com').count(), 1)

        # エラーメッセージをHTMLから抽出
        soup = BeautifulSoup(res_json2['html'], 'html.parser')
        self.assertIn('この メールアドレス を持った ユーザー が既に存在します。', soup.select_one('#id_email + .invalid-feedback').get_text())


    #----------------
    # UpdateView
    #----------------
    def test_3_1_1_1(self):
        '''更新画面表示'''
        # レスポンス取得
        response = self.client.get(reverse('register:update', args=[1]))

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # JSONをロード
        data = json.loads(response.content)
        html = data['html']

        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(html, 'html.parser')
        modal_title = soup.select_one('.modal-title').get_text(strip=True)

        # モーダルタイトル確認
        self.assertEqual(modal_title, 'ユーザー更新: system_user')

    def test_3_1_2_1(self):
        '''更新画面表示（異常系：直リンク）'''
        url = reverse('register:update', args=[1])

        # 直リンク状態でアクセス
        self.client.logout()
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # 遷移後の画面確認
        self.assertRedirects(response, '/login/?next=/register/1/update/')

    def test_3_1_2_2(self):
        '''更新画面表示（異常系：権限不足）'''
        # 更新ユーザーでログイン
        self.user = get_user_model().objects.get(pk=3)
        self.client.login(email='editor@example.com', password='pass')

        url = reverse('register:update', args=[1])
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_3_1_2_3(self):
        '''
        更新画面表示（異常系：存在しないデータを開く）
        '''
        # リクエスト作成
        url = reverse('register:update', args=[99999])
        request = self.factory.get(url)
        request.user = self.user
        setattr(request, 'session', self.client.session)

        # メッセージストレージ設定
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # View実行
        response = UserUpdateView.as_view()(request, pk=99999)

        # JSONレスポンス構造確認
        self.assertJSONEqual(response.content, {'success': False})

        # ステータスコード確認
        self.assertEqual(response.status_code, 404)

        # メッセージ内容確認
        storage = list(messages)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, 'このユーザーは既に削除されています。')
        self.assertEqual(storage[0].level_tag, 'error')

    def test_3_2_1_1(self):
        '''
        更新処理（正常系：通常更新）
        '''
        # 事前データ作成
        user = CustomUser.objects.create(
            tenant=self.user.tenant,
            username='旧ユーザー',
            username_kana='キュウユーザー',
            email='old@example.com',
            tel_number='111-1111-1111',
            gender='1',
            employment_status='1',
            privilege='1',
            create_user=self.user,
            update_user=self.user,
        )
        create_user = self.user

        # 事前データ作成ユーザーとは別のユーザーで実施
        self.user = get_user_model().objects.get(pk=2)
        self.client.login(email='manager@example.com', password='pass')

        url = reverse('register:update', args=[user.id])
        data = {
            'employment_status': '2',
            'privilege': '2',
            'groups_custom': [1, 2]
        }

        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # レスポンス確認
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])

        # メッセージ確認
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages) > 0)
        self.assertEqual(messages[0].message, 'ユーザー「旧ユーザー」を更新しました。')
        self.assertEqual(messages[0].level_tag, 'success')

        # DB更新確認
        user.refresh_from_db()
        self.assertEqual(user.employment_status, '2')
        self.assertEqual(user.privilege, '2')
        self.assertEqual(user.is_deleted, False)
        self.assertEqual(user.create_user, create_user)
        self.assertEqual(user.update_user, self.user)
        self.assertEqual(user.tenant, self.user.tenant)
        self.assertLess((timezone.now() - user.created_at).total_seconds(), 60)
        self.assertLessEqual(abs((user.updated_at - timezone.now()).total_seconds()), 5)

        # グループ更新確認
        group_ids = list(user.groups_custom.values_list('id', flat=True))
        self.assertCountEqual(group_ids, [1, 2], f'groups_custom={group_ids}')

    def test_3_2_2_1(self):
        '''
        更新処理（異常系: 直リンク）
        '''
        url = reverse('register:update', args=[1])

        # ログインせずにアクセス
        self.client.logout()

        # 事前データ作成
        CustomUser.objects.create(
            tenant=self.user.tenant,
            username='旧ユーザー',
            username_kana='キュウユーザー',
            email='old@example.com',
            tel_number='111-1111-1111',
            gender='1',
            employment_status='1',
            privilege='1',
            create_user=self.user,
            update_user=self.user,
        )

        data = {
            'employment_status': '2',
            'privilege': '2',
        }

        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # レスポンス確認
        self.assertEqual(response.status_code, 302)

    def test_3_2_2_2(self):
        '''
        更新処理（異常系: 権限不足）
        '''
        url = reverse('register:update', args=[1])

        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=4)
        self.client.login(email='viewer@example.com', password='pass')

        data = {
            'employment_status': '2',
            'privilege': '2',
        }

        # 処理実行
        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # レスポンス確認
        self.assertEqual(response.status_code, 403)

    def test_3_2_2_3(self):
        '''
        更新処理（異常系：権限桁数オーバー）
        '''
        # 事前データ作成
        user = CustomUser.objects.create(
            tenant=self.user.tenant,
            username='旧ユーザー',
            username_kana='キュウユーザー',
            email='old@example.com',
            tel_number='111-1111-1111',
            gender='1',
            employment_status='1',
            privilege='1',
            create_user=self.user,
            update_user=self.user,
        )
        create_user = self.user

        # 事前データ作成ユーザーとは別のユーザーで実施
        self.user = get_user_model().objects.get(pk=2)
        self.client.login(email='manager@example.com', password='pass')

        url = reverse('register:update', args=[user.id])
        data = {
            'employment_status': '2',
            'privilege': 'invalid',
            'groups_custom': [1, 2]
        }

        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # レスポンス確認
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertFalse(res_json['success'])

        # エラーメッセージをHTMLから抽出
        soup = BeautifulSoup(res_json['html'], 'html.parser')
        self.assertIn('正しく選択してください。 invalid は候補にありません。', soup.select_one('#id_privilege + .invalid-feedback').get_text())

    def test_3_2_2_4(self):
        '''
        更新処理（異常系：存在しないデータの更新）
        '''
        url = reverse('register:update', args=[99999])
        data = {
            'username': 'テストユーザー',
            'username_kana': 'テストユーザー',
            'email': 'test@example.com',
            'tel_number': '090-1111-2222',
            'gender': '1',
            'employment_status': '1',
            'privilege': '2',
        }

        # RequestFactoryでPOSTリクエスト生成
        request = self.factory.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.user
        setattr(request, 'session', self.client.session)

        # メッセージストレージをリクエストに付与
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # View呼び出し
        response = UserUpdateView.as_view()(request, pk=99999)

        # JSONレスポンス構造確認
        self.assertJSONEqual(response.content, {'success': False})

        # ステータスコード確認
        self.assertEqual(response.status_code, 404)

        # messages.error 確認
        storage = list(messages)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, 'このユーザーは既に削除されています。')
        self.assertEqual(storage[0].level_tag, 'error')


    #----------------
    # DeleteView
    #----------------
    def test_4_1_1_1(self):
        '''
        削除処理（正常系）
        '''
        # ユーザーテストデータ
        user = CustomUser.objects.create(
            tenant=self.user.tenant,
            username='テストユーザー',
            username_kana='テストユーザー',
            email='test@example.com',
            tel_number='090-1111-2222',
            gender='1',
            employment_status='1',
            privilege='2',
            create_user=self.user,
            update_user=self.user,
        )

        # 受注テストデータ
        sales_order = SalesOrder.objects.create(
            tenant=self.user.tenant,
            assignee=user,
            sales_order_no='SO-001',
            sales_order_date='2025-09-30',
            create_user=self.user,
            update_user=self.user,
        )

        url = reverse('register:delete', args=[user.id])
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertTrue(res_json['success'])

        # ユーザーの削除確認
        self.assertFalse(CustomUser.objects.filter(id=user.id).exists())

        # 受注データの担当者がNullになっていること
        sales_order.refresh_from_db()
        self.assertIsNone(sales_order.assignee)

    def test_4_1_2_1(self):
        '''削除処理（異常系：直リンク）'''
        # 事前データ作成
        user = CustomUser.objects.create(
            tenant=self.user.tenant,
            username='テストユーザー',
            username_kana='テストユーザー',
            email='test@example.com',
            tel_number='090-1111-2222',
            gender='1',
            employment_status='1',
            privilege='2',
            create_user=self.user,
            update_user=self.user,
        )

        # 更新処理のURL作成
        url = reverse('register:delete', args=[user.id])

        # ログアウト
        self.client.logout()

        # 処理実行
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # 遷移後の画面確認
        self.assertRedirects(response, f'/login/?next=/register/{user.id}/delete/')

    def test_4_1_2_2(self):
        '''削除処理（異常系：権限不足）'''

        # 更新ユーザーでログイン
        self.user = get_user_model().objects.get(pk=3)
        self.client.login(email='editor@example.com', password='pass')

        # 事前データ作成
        user = CustomUser.objects.create(
            tenant=self.user.tenant,
            username='テストユーザー',
            username_kana='テストユーザー',
            email='test@example.com',
            tel_number='090-1111-2222',
            gender='1',
            employment_status='1',
            privilege='2',
            create_user=self.user,
            update_user=self.user,
        )

        # 更新処理のURL作成
        url = reverse('register:update', args=[user.id])

        # 処理実行
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_4_1_2_3(self):
        '''
        削除処理（異常系：存在しないデータの削除）
        '''
        url = reverse('register:delete', args=[99999])

        # RequestFactoryでPOSTリクエスト生成
        request = self.factory.post(url,  HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.user
        setattr(request, 'session', self.client.session)

        # メッセージストレージをリクエストに付与
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # View呼び出し
        response = UserDeleteView.as_view()(request, pk=99999)

        # JSONレスポンス構造確認
        self.assertJSONEqual(response.content, {'success': False})

        # ステータスコード確認
        self.assertEqual(response.status_code, 404)

        # messages.error 確認
        storage = list(messages)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, 'このユーザーは既に削除されています。')
        self.assertEqual(storage[0].level_tag, 'error')

    def test_4_1_2_4(self):
        '''
        削除処理（異常系：存在しないデータの削除）
        '''
        url = reverse('register:delete', args=[self.user.pk])

        # RequestFactoryでPOSTリクエスト生成
        request = self.factory.post(url,  HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.user
        setattr(request, 'session', self.client.session)

        # メッセージストレージをリクエストに付与
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # View呼び出し
        response = UserDeleteView.as_view()(request, pk=self.user.pk)

        # JSONレスポンス構造確認
        self.assertJSONEqual(response.content, {'success': False})

        # ステータスコード確認
        self.assertEqual(response.status_code, 400)

        # messages.error 確認
        storage = list(messages)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, 'ログイン中のユーザーは削除できません。')
        self.assertEqual(storage[0].level_tag, 'error')

    #----------------
    # BulkDeleteView
    #----------------
    def test_5_1_1_1(self):
        '''
        一括削除（正常系）
        '''
        # 削除対象データ作成
        user1 = CustomUser.objects.create(
            tenant=self.user.tenant,
            username='テストユーザー1',
            username_kana='テストユーザー1',
            email='test1@example.com',
            tel_number='090-1111-2222',
            gender='1',
            employment_status='1',
            privilege='2',
            create_user=self.user,
            update_user=self.user,
        )
        user2 = CustomUser.objects.create(
            tenant=self.user.tenant,
            username='テストユーザー2',
            username_kana='テストユーザー2',
            email='test2@example.com',
            tel_number='090-1111-2222',
            gender='1',
            employment_status='1',
            privilege='2',
            create_user=self.user,
            update_user=self.user,
        )

        # 受注データ作成
        sales_order_1 = SalesOrder.objects.create(
            tenant=self.user.tenant,
            assignee=user1,
            sales_order_no='SO-001',
            sales_order_date='2025-09-30',
            create_user=self.user,
            update_user=self.user,
        )

        # 受注データ作成
        sales_order_2 = SalesOrder.objects.create(
            tenant=self.user.tenant,
            assignee=user2,
            sales_order_no='SO-002',
            sales_order_date='2025-09-30',
            create_user=self.user,
            update_user=self.user,
        )

        # 処理実行
        url = reverse('register:bulk_delete')
        response = self.client.post(
            url,
            {'ids': [user1.id, user2.id]},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # レスポンス確認
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertIn('2件削除しました', res_json['message'])

        # DB確認
        self.assertFalse(CustomUser.objects.filter(id=user1.id).exists())
        self.assertFalse(CustomUser.objects.filter(id=user2.id).exists())

        # 受注データの担当者がすべてNullになっていること
        sales_order_1.refresh_from_db()
        sales_order_2.refresh_from_db()
        self.assertIsNone(sales_order_1.assignee)
        self.assertIsNone(sales_order_2.assignee)

    def test_5_1_1_2(self):
        '''
        一括削除（正常系：指定なし）
        '''
        # 削除対象データ作成
        user1 = CustomUser.objects.create(
            tenant=self.user.tenant,
            username='テストユーザー1',
            username_kana='テストユーザー1',
            email='test1@example.com',
            tel_number='090-1111-2222',
            gender='1',
            employment_status='1',
            privilege='2',
            create_user=self.user,
            update_user=self.user,
        )
        user2 = CustomUser.objects.create(
            tenant=self.user.tenant,
            username='テストユーザー2',
            username_kana='テストユーザー2',
            email='test2@example.com',
            tel_number='090-1111-2222',
            gender='1',
            employment_status='1',
            privilege='2',
            create_user=self.user,
            update_user=self.user,
        )

        url = reverse('register:bulk_delete')
        response = self.client.post(url, {})  # idなし

        # リダイレクト確認
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('register:list'))

        # メッセージがセットされていることを確認
        storage = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any('削除対象が選択されていません' in str(m) for m in storage))

        # DB確認（削除されていない）
        self.assertTrue(CustomUser.objects.filter(id=user1.id).exists())
        self.assertTrue(CustomUser.objects.filter(id=user2.id).exists())

    def test_5_1_2_1(self):
        '''
        一括削除（異常系：直リンク）
        '''
        # 削除対象データ作成
        user1 = CustomUser.objects.create(
            tenant=self.user.tenant,
            username='テストユーザー1',
            username_kana='テストユーザー1',
            email='test1@example.com',
            tel_number='090-1111-2222',
            gender='1',
            employment_status='1',
            privilege='2',
            create_user=self.user,
            update_user=self.user,
        )
        user2 = CustomUser.objects.create(
            tenant=self.user.tenant,
            username='テストユーザー2',
            username_kana='テストユーザー2',
            email='test2@example.com',
            tel_number='090-1111-2222',
            gender='1',
            employment_status='1',
            privilege='2',
            create_user=self.user,
            update_user=self.user,
        )

        # ログアウト
        self.client.logout()

        # 処理実行
        url = reverse('register:bulk_delete')
        response = self.client.post(
            url,
            {'ids': [user1.id, user2.id]},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # 遷移後の画面確認
        self.assertRedirects(response, '/login/?next=/register/bulk_delete/')

        # DB確認
        self.assertTrue(CustomUser.objects.filter(id=user1.id).exists())
        self.assertTrue(CustomUser.objects.filter(id=user2.id).exists())

    def test_5_1_2_2(self):
        '''一括削除処理（異常系：権限不足）'''

        # 更新ユーザーでログイン
        self.user = get_user_model().objects.get(pk=3)
        self.client.login(email='editor@example.com', password='pass')

        # 削除対象データ作成
        user1 = CustomUser.objects.create(
            tenant=self.user.tenant,
            username='テストユーザー1',
            username_kana='テストユーザー1',
            email='test1@example.com',
            tel_number='090-1111-2222',
            gender='1',
            employment_status='1',
            privilege='2',
            create_user=self.user,
            update_user=self.user,
        )
        user2 = CustomUser.objects.create(
            tenant=self.user.tenant,
            username='テストユーザー2',
            username_kana='テストユーザー2',
            email='test2@example.com',
            tel_number='090-1111-2222',
            gender='1',
            employment_status='1',
            privilege='2',
            create_user=self.user,
            update_user=self.user,
        )

        # 処理実行
        url = reverse('register:bulk_delete')
        response = self.client.post(
            url,
            {'ids': [user1.id, user2.id]},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_5_1_2_3(self):
        '''一括削除処理（異常系：部分失敗-存在しないID）'''

        # テスト用データ作成（1件だけ存在）
        user = CustomUser.objects.create(
            tenant=self.user.tenant,
            username='テストユーザー1',
            username_kana='テストユーザー1',
            email='test1@example.com',
            tel_number='090-1111-2222',
            gender='1',
            employment_status='1',
            privilege='2',
            create_user=self.user,
            update_user=self.user,
        )

        # 実在するIDと存在しないIDを混ぜる
        valid_id = str(user.id)
        nonexistent_id = str(user.id + 9999)
        ids = [valid_id, nonexistent_id]

        # RequestFactory で Ajax POST リクエスト作成
        url = reverse('register:bulk_delete')
        request = self.factory.post(url, {'ids': ids}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.user
        setattr(request, 'session', self.client.session)

        # メッセージストレージを付与
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # View呼び出し
        response = UserBulkDeleteView.as_view()(request)

        # ステータスコード確認
        self.assertEqual(response.status_code, 404)

        # JSONレスポンス内容確認
        self.assertJSONEqual(response.content, {'success': False})

        # メッセージ内容確認
        storage = list(messages)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, 'すでに削除されているユーザーが含まれています。')
        self.assertEqual(storage[0].level_tag, 'error')

        # 削除が実行されていないこと（ロールバック確認）
        self.assertTrue(CustomUser.objects.filter(id=user.id).exists())

    def test_5_1_2_5(self):
        '''一括削除処理（異常系：部分失敗-ログイン中ユーザー）'''

        # テスト用データ作成
        user = CustomUser.objects.create(
            tenant=self.user.tenant,
            username='テストユーザー1',
            username_kana='テストユーザー1',
            email='test1@example.com',
            tel_number='090-1111-2222',
            gender='1',
            employment_status='1',
            privilege='2',
            create_user=self.user,
            update_user=self.user,
        )

        # 実在するIDと存在しないIDを混ぜる
        valid_id = str(user.id)
        loginuser_id = str(self.user.id)
        ids = [valid_id, loginuser_id]

        # RequestFactory で Ajax POST リクエスト作成
        url = reverse('register:bulk_delete')
        request = self.factory.post(url, {'ids': ids}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.user
        setattr(request, 'session', self.client.session)

        # メッセージストレージを付与
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # View呼び出し
        response = UserBulkDeleteView.as_view()(request)

        # ステータスコード確認
        self.assertEqual(response.status_code, 400)

        # JSONレスポンス内容確認
        self.assertJSONEqual(response.content, {'success': False})

        # メッセージ内容確認
        storage = list(messages)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, 'ログイン中のユーザーは削除できません。')
        self.assertEqual(storage[0].level_tag, 'error')

        # 削除が実行されていないこと（ロールバック確認）
        self.assertTrue(CustomUser.objects.filter(id=user.id).exists())


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
        for row, user in zip(rows[1:], queryset):
            expected = []
            for field in field_names:
                if field == 'groups_custom':  # ← 所属グループ列なら特別処理
                    group_names = ", ".join(user.groups_custom.values_list("group_name", flat=True))
                    expected.append(group_names or '')  # ← 空の場合は ''
                else:
                    display_method = f'get_{field}_display'
                    if hasattr(user, display_method):
                        value = getattr(user, display_method)()
                    else:
                        value = getattr(user, field)
                    expected.append(str(value) if value is not None else '')

            self.assertEqual(row, expected)

    def test_6_1_1_1(self):
        '''CSVエクスポート（正常系：n件）'''
        url = reverse('register:export_csv')
        rows = self._request_and_parse(url)

        # 件数チェック
        self.assertEqual(len(rows) - 1, 9)

        users = CustomUser.objects.filter(
            tenant=self.user.tenant,
            is_deleted=False
        ).order_by('id')

        self._assert_csv_matches_queryset(rows, users)


    def test_6_1_1_2(self):
        '''CSVエクスポート（正常系：ユーザー名検索）'''
        target = 'viewer'
        url = reverse('register:export_csv') + f'?search_username={target}'
        rows = self._request_and_parse(url)
        users = CustomUser.objects.filter(
            username__icontains=target,
            tenant=self.user.tenant,
            is_deleted=False
        ).order_by('id')
        self.assertEqual(len(rows) - 1, users.count())
        self._assert_csv_matches_queryset(rows, users)

    def test_6_1_1_3(self):
        '''CSVエクスポート（正常系：更新ユーザー）'''

        # 更新ユーザーでログイン
        self.user = get_user_model().objects.get(pk=3)
        self.client.login(email='editor@example.com', password='pass')

        url = reverse('register:export_csv')
        rows = self._request_and_parse(url)

        # 件数チェック）
        self.assertEqual(len(rows) - 1, 9)

        users = CustomUser.objects.filter(
            tenant=self.user.tenant,
            is_deleted=False
        ).order_by('id')

        self._assert_csv_matches_queryset(rows, users)

    def _create_max_data(self, n):
        data = []
        for i in range(n):
            p = CustomUser.objects.create(
                tenant=self.user.tenant,
                username=f'テストユーザー{i}',
                username_kana=f'テストユーザー{i}',
                email=f'test{i}@example.com',
                tel_number='090-1111-2222',
                gender='1',
                employment_status='1',
                privilege='2',
                create_user=self.user,
                update_user=self.user,
            )
            data.append(p)
        return data

    def test_6_1_1_4(self):
        '''CSVエクスポート（正常系：上限数以上）'''
        self._create_max_data(settings.MAX_EXPORT_ROWS + 1)
        url = reverse('register:export_check')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('warning', data)
        self.assertEqual('出力件数が上限（10,000件）を超えています。先頭10,000件のみを出力します。', data['warning'])
        self.assertNotIn('ok', data)

    def test_6_1_2_1(self):
        '''CSVエクスポート（異常系：直リンク）'''
        url = reverse('register:export_csv')

        # ログアウト
        self.client.logout()

        # アクセス実行
        response = self.client.get(url)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # 遷移後の画面確認
        self.assertRedirects(response, '/login/?next=/register/export/csv')

        # CSVが返却されていないことを確認
        if 'Content-Type' in response:
            self.assertNotEqual(response['Content-Type'], 'text/csv')


    #----------------
    # ImportCSV
    #----------------
    def _make_csv_file(self, rows, encoding='utf-8', header=None):
        '''
        テスト用CSVファイルの作成
        '''
        if header is None:
            fieldnames = [
                'ユーザー名', 'ユーザー名（カナ）', '性別', 'メールアドレス', '電話番号', '雇用状態', '権限', '所属グループ'
            ]
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
        url = reverse('register:import_csv')

        # ログインユーザー以外のデータを削除
        CustomUser.objects.exclude(pk=self.user.pk).delete()

        # 所属グループを作成
        group1 = UserGroup.objects.create(
            tenant=self.user.tenant,
            group_name='開発チーム',
            create_user=self.user,
            update_user=self.user,
        )
        group2 = UserGroup.objects.create(
            tenant=self.user.tenant,
            group_name='営業チーム',
            create_user=self.user,
            update_user=self.user,
        )

        # CSVデータ作成（所属グループ列を追加）
        rows = [
            {
                'ユーザー名': 'テストユーザー',
                'ユーザー名（カナ）': 'テストユーザー',
                'メールアドレス': 'test@example.com',
                '電話番号': '111-1111-1111',
                '性別': '男性',
                '雇用状態': '在職中',
                '権限': '更新',
                '所属グループ': '開発チーム, 営業チーム',
            },
            {
                'ユーザー名': 'テストユーザー2',
                'ユーザー名（カナ）': 'テストユーザー2',
                'メールアドレス': 'test2@example.com',
                '電話番号': '222-2222-2222',
                '性別': '女性',
                '雇用状態': '休職中',
                '権限': '参照',
                '所属グループ': '営業チーム',
            },
        ]

        # CSVファイルの作成
        file = self._make_csv_file(rows)

        # POST実行
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)

        # ステータスコード確認
        self.assertEqual(response.status_code, 200, res_json)
        self.assertEqual('2件をインポートしました。', res_json['message'])

        # 件数確認（ログインユーザー1件 + 新規2件 = 3件）
        self.assertEqual(CustomUser.objects.count(), 3)

        # 登録内容確認
        users = CustomUser.objects.filter(is_deleted=False).exclude(pk=self.user.pk).order_by('email')
        for row, user in zip(sorted(rows, key=lambda x: x['メールアドレス']), users):
            self.assertEqual(user.username, row['ユーザー名'])
            self.assertEqual(user.username_kana, row['ユーザー名（カナ）'])
            self.assertEqual(user.email, row['メールアドレス'])
            self.assertEqual(user.tel_number, row['電話番号'])
            self.assertEqual(user.get_gender_display(), row['性別'])
            self.assertEqual(user.get_employment_status_display(), row['雇用状態'])
            self.assertEqual(user.get_privilege_display(), row['権限'])
            self.assertFalse(user.is_deleted)
            self.assertEqual(user.create_user, self.user)
            self.assertEqual(user.update_user, self.user)
            self.assertEqual(user.tenant, self.user.tenant)
            self.assertLessEqual(abs((user.created_at - timezone.now()).total_seconds()), 5)
            self.assertLessEqual(abs((user.updated_at - timezone.now()).total_seconds()), 5)

            # 所属グループ確認
            groups = list(user.groups_custom.values_list('group_name', flat=True))
            expected_groups = [g.strip() for g in (row.get('所属グループ') or '').split(',') if g.strip()]
            self.assertCountEqual(
                groups,  # DB: ['営業チーム', '開発チーム'] など（順不同）
                expected_groups,  # CSV: ['開発チーム', '営業チーム'] など（順不同で比較）
                f'{user.username} の所属グループが不一致（実際: {groups}, 期待: {expected_groups}）'
            )


    def test_7_1_1_2(self):
        '''CSVインポート（正常系：shift-jis）'''
        url = reverse('register:import_csv')

        # ログインユーザー以外のデータを削除
        CustomUser.objects.exclude(pk=self.user.pk).delete()

        rows = [
            {
                'ユーザー名': 'テストユーザー',
                'ユーザー名（カナ）': 'テストユーザー',
                'メールアドレス': 'test@example.com',
                '電話番号': '111-1111-1111',
                '性別': '女性',
                '雇用状態': '在職中',
                '権限': '管理者',
            },
        ]
        # CSVファイルの作成
        file = self._make_csv_file(rows=rows, encoding='cp932')

        # レスポンス確認
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # メッセージ確認
        self.assertEqual('1件をインポートしました。', res_json['message'])

        # 件数確認
        self.assertEqual(CustomUser.objects.count(), 2)

        # 登録値の確認
        obj = CustomUser.objects.filter(email='test@example.com').first()
        self.assertIsNotNone(obj)
        self.assertEqual(obj.username, 'テストユーザー')
        self.assertEqual(obj.is_deleted, False)
        self.assertEqual(obj.create_user, self.user)
        self.assertEqual(obj.update_user, self.user)
        self.assertEqual(obj.tenant, self.user.tenant)
        self.assertLessEqual(abs((obj.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((obj.updated_at - timezone.now()).total_seconds()), 5)

    def test_7_1_1_3(self):
        '''CSVインポート（正常系：改行混在 CRLF/LF）'''
        url = reverse('register:import_csv')

        # ログインユーザー以外のデータを削除
        CustomUser.objects.exclude(pk=self.user.pk).delete()

        rows = [
            {
                'ユーザー名': 'テストユーザー',
                'ユーザー名（カナ）': 'テストユーザー',
                'メールアドレス': 'test@example.com',
                '電話番号': '111-1111-1111',
                '性別': '女性',
                '雇用状態': '在職中',
                '権限': '管理者',
                '所属グループ': '',
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

        # メッセージ確認
        self.assertEqual('1件をインポートしました。', res_json['message'])

        # 件数確認
        self.assertEqual(CustomUser.objects.count(), 2)

        # 登録値の確認
        obj = CustomUser.objects.filter(email='test@example.com').first()
        self.assertIsNotNone(obj)
        self.assertEqual(obj.username, 'テストユーザー')
        self.assertEqual(obj.is_deleted, False)
        self.assertEqual(obj.create_user, self.user)
        self.assertEqual(obj.update_user, self.user)
        self.assertEqual(obj.tenant, self.user.tenant)
        self.assertLessEqual(abs((obj.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((obj.updated_at - timezone.now()).total_seconds()), 5)

    def test_7_1_1_4(self):
        '''CSVインポート（正常系：空行スキップ）'''
        url = reverse('register:import_csv')

        # ログインユーザー以外のデータを削除
        CustomUser.objects.exclude(pk=self.user.pk).delete()

        # データの作成
        rows = [
            {
                'ユーザー名': 'テストユーザー',
                'ユーザー名（カナ）': 'テストユーザーカナ',
                'メールアドレス': 'test@example.com',
                '電話番号': '111-1111-1111',
                '性別': '女性',
                '雇用状態': '在職中',
                '権限': '管理者',
                '所属グループ': '',
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
        self.assertEqual(CustomUser.objects.count(), 2)

        # 登録値の確認
        user = CustomUser.objects.filter(email='test@example.com').first()
        self.assertEqual(user.username, 'テストユーザー')
        self.assertEqual(user.username_kana, 'テストユーザーカナ')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.tel_number, '111-1111-1111')
        self.assertEqual(user.get_gender_display(), '女性')
        self.assertEqual(user.get_employment_status_display(), '在職中')
        self.assertEqual(user.get_privilege_display(), '管理者')
        self.assertEqual(user.is_deleted, False)
        self.assertEqual(user.is_active, True)
        self.assertEqual(user.create_user, self.user)
        self.assertEqual(user.update_user, self.user)
        self.assertEqual(user.tenant, self.user.tenant)
        self.assertLessEqual(abs((user.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((user.updated_at - timezone.now()).total_seconds()), 5)

    def test_7_1_1_5(self):
        '''CSVインポート（正常系：空行スキップ）'''
        url = reverse('register:import_csv')

        # ログインユーザー以外のデータを削除
        CustomUser.objects.exclude(pk=self.user.pk).delete()

        # データの作成
        fieldnames = [
            'ユーザー名',
            'ユーザー名（カナ）',
            '電話番号',
            '性別',
            'メールアドレス',
            '雇用状態',
            '権限',
            '所属グループ'
        ]
        rows = [
            {
                'ユーザー名': 'テストユーザー',
                'ユーザー名（カナ）': 'テストユーザーカナ',
                '電話番号': '111-1111-1111',
                '性別': '女性',
                'メールアドレス': 'test@example.com',
                '雇用状態': '在職中',
                '権限': '管理者',
                '所属グループ': '',
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
        self.assertEqual(CustomUser.objects.count(), 2)

        # 登録値の確認
        user = CustomUser.objects.filter(email='test@example.com').first()
        self.assertEqual(user.username, 'テストユーザー')
        self.assertEqual(user.username_kana, 'テストユーザーカナ')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.tel_number, '111-1111-1111')
        self.assertEqual(user.get_gender_display(), '女性')
        self.assertEqual(user.get_employment_status_display(), '在職中')
        self.assertEqual(user.get_privilege_display(), '管理者')
        self.assertEqual(user.is_deleted, False)
        self.assertEqual(user.is_active, True)
        self.assertEqual(user.create_user, self.user)
        self.assertEqual(user.update_user, self.user)
        self.assertEqual(user.tenant, self.user.tenant)
        self.assertLessEqual(abs((user.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((user.updated_at - timezone.now()).total_seconds()), 5)

    def test_7_1_2_1(self):
        '''CSVインポート（異常系：直リンク）'''
        self.client.logout()
        url = reverse('register:import_csv')

        # ログインユーザー以外のデータを削除
        CustomUser.objects.exclude(pk=self.user.pk).delete()

        # CSVファイルの作成
        file = self._make_csv_file([
            {
                'ユーザー名': 'テストユーザー',
                'ユーザー名（カナ）': 'テストユーザー',
                'メールアドレス': 'test@example.com',
                '電話番号': '111-1111-1111',
                '性別': '女性',
                '雇用状態': '在職中',
                '権限': '管理者',
                '所属グループ': '',
            },
        ])

        # レスポンスを取得
        response = self.client.post(url, {'file': file})

        # 登録されていないことを確認
        self.assertEqual(CustomUser.objects.count(), 1)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # リダイレクト先を確認
        self.assertRedirects(response, r'/login/?next=/register/import/csv')

    def test_7_1_2_2(self):
        '''CSVインポート（異常系：権限不足）'''
        # 現在ログイン中ユーザーをviewer権限に変更
        self.user.privilege = PRIVILEGE_VIEWER
        self.user.save()
        url = reverse('register:import_csv')

        # ログインユーザー以外のデータを削除
        CustomUser.objects.exclude(pk=self.user.pk).delete()

        # テストデータ
        rows = [{
                'ユーザー名': 'テストユーザー',
                'ユーザー名（カナ）': 'テストユーザー',
                'メールアドレス': 'test@example.com',
                '電話番号': '111-1111-1111',
                '性別': '1',
                '雇用状態': '1',
                '権限': '1',
                '所属グループ': '',
            }]

        # CSVファイルの作成
        file = self._make_csv_file(rows)

        # レスポンスを取得
        response = self.client.post(url, {'file': file})

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

        # 登録されていないことを確認
        self.assertEqual(CustomUser.objects.count(), 1)

    def test_7_1_2_3(self):
        '''CSVインポート（異常系：複数フィールド・複数行エラー）'''
        url = reverse('register:import_csv')

        # ログインユーザー以外のデータを削除
        CustomUser.objects.exclude(pk=self.user.pk).delete()

        rows = [
            {
                'ユーザー名': '',
                'ユーザー名（カナ）': 'テストユーザー',
                'メールアドレス': 'test@example.com',
                '電話番号': '111-1111-1111',
                '性別': 'invalid',
                '雇用状態': '在職中',
                '権限': '管理者',
            },
            {
                'ユーザー名': 'テストユーザー2',
                'ユーザー名（カナ）': 'テストユーザー2',
                'メールアドレス': 'test2@@example.com',
                '電話番号': '222^2222=2222',
                '性別': 'その他',
                '雇用状態': '求職中',
                '権限': '更新',
            }
        ]
        file = self._make_csv_file(rows)

        res = self.client.post(url, {'file': file})
        self.assertEqual(res.status_code, 400)
        res_json = json.loads(res.content)

        # 期待メッセージ確認
        self.assertEqual('CSVに問題があります。', res_json.get('error', ''))
        self.assertIn('2行目:', res_json.get('details', '')[0])
        self.assertIn('この項目は必須です。', res_json.get('details', '')[0])
        self.assertIn('正しく選択してください。 invalid は候補にありません。', res_json.get('details', '')[0])
        self.assertIn('3行目:', res_json.get('details', '')[1])
        self.assertIn('有効なメールアドレスを入力してください。', res_json.get('details', '')[1])
        self.assertIn('数字とハイフンのみ使用できます。', res_json.get('details', '')[1])

    def test_7_1_2_4(self):
        '''CSVインポート（異常系：メールアドレス重複）'''
        url = reverse('register:import_csv')

        # ログインユーザー以外のデータを削除
        CustomUser.objects.exclude(pk=self.user.pk).delete()

        rows = [
            {
                'ユーザー名': 'テストユーザー1',
                'ユーザー名（カナ）': 'テストユーザー',
                'メールアドレス': 'test@example.com',
                '電話番号': '111-1111-1111',
                '性別': '女性',
                '雇用状態': '在職中',
                '権限': '管理者',
            },
            {
                'ユーザー名': 'テストユーザー2',
                'ユーザー名（カナ）': 'テストユーザー2',
                'メールアドレス': 'test@example.com',
                '電話番号': '222-2222-2222',
                '性別': '男性',
                '雇用状態': '休職中',
                '権限': '更新',
            }
        ]
        file = self._make_csv_file(rows)

        res = self.client.post(url, {'file': file})
        self.assertEqual(res.status_code, 400)
        res_json = json.loads(res.content)

        # 期待メッセージ確認
        self.assertEqual('CSVに問題があります。', res_json.get('error', ''))
        self.assertIn('3行目:', res_json.get('details', '')[0])
        self.assertIn('メールアドレス「test@example.com」は既に存在します。', res_json.get('details', '')[0])

    def test_7_1_2_5(self):
        '''CSVインポート（異常系：部分失敗）'''
        url = reverse('register:import_csv')

        # ログインユーザー以外のデータを削除
        CustomUser.objects.exclude(pk=self.user.pk).delete()

        # CSVファイルの作成
        rows = [
            {
                'ユーザー名': 'テストユーザー1',
                'ユーザー名（カナ）': 'テストユーザー',
                'メールアドレス': 'test@example.com',
                '電話番号': '111-1111-1111',
                '性別': '女性',
                '雇用状態': '在職中',
                '権限': '管理者',
            },
            {
                'ユーザー名': 'テストユーザー2',
                'ユーザー名（カナ）': 'テストユーザー2',
                'メールアドレス': '',
                '電話番号': '222-2222-2222',
                '性別': '男性',
                '雇用状態': '休職中',
                '権限': '更新',
            }
        ]
        file = self._make_csv_file(rows)

        # レスポンス確認
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)

        # エラーメッセージ確認
        self.assertEqual('CSVに問題があります。', res_json['error'])
        self.assertTrue(any('必須' in s for s in res_json['details']))

        # 件数確認
        self.assertEqual(CustomUser.objects.count(), 1)


class UserGroupManageViewTests(TestCase):
    """商品マスタ - 商品カテゴリ管理のテスト"""

    def setUp(self):
        '''共通データ作成'''
        self.factory = RequestFactory()

        # テストクライアント生成
        self.client = Client()

        # テストデータ投入
        call_command('loaddata', 'test_tenants.json')
        call_command('loaddata', 'test_registers.json')

        # 基本は管理者ユーザーで実施
        self.user = get_user_model().objects.get(pk=2)
        self.client.login(email='manager@example.com', password='pass')

    def test_8_1_1_1(self):
        """新規登録（正常）"""
        url = reverse('register:group_manage')
        data = {
            'selected_group': '',
            'group_name': '新グループ',
            'action': 'save',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # 成功メッセージ確認
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('ユーザーグループ「新グループ」を新規作成しました。', str(messages[0]))
        self.assertEqual(messages[0].level_tag, 'success')

        # DB登録確認
        ug = UserGroup.objects.filter(tenant=self.user.tenant, group_name='新グループ')
        self.assertTrue(ug.exists())
        ug = ug.first()
        self.assertEqual(ug.group_name, '新グループ')
        self.assertEqual(ug.is_deleted, False)
        self.assertEqual(ug.create_user, self.user)
        self.assertEqual(ug.update_user, self.user)
        self.assertEqual(ug.tenant, self.user.tenant)
        self.assertLessEqual(abs((ug.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((ug.updated_at - timezone.now()).total_seconds()), 5)

    def test_8_1_2_1(self):
        """新規登録：異常系（直リンク）"""
        self.client.logout()
        url = reverse('register:group_manage')
        response = self.client.post(url, {
            'selected_group': '',
            'group_name': '新グループ',
            'action': 'save',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        self.assertIn('next=', response.url)

    def test_8_1_2_2(self):
        """新規登録：異常系（権限不足）"""
        # 更新ユーザーでログイン
        self.user = get_user_model().objects.get(pk=3)
        self.client.login(email='editor@example.com', password='pass')
        url = reverse('register:group_manage')
        response = self.client.post(url, {
            'selected_group': '',
            'group_name': '新グループ',
            'action': 'save',
        })
        self.assertEqual(response.status_code, 403)

    def test_8_2_1_1(self):
        """更新（正常）"""
        create_user = self.user
        url = reverse('register:group_manage')

        # ログインを追加
        self.client.force_login(create_user)

        # 更新対象データ
        data = {
            'selected_group': '',
            'group_name': '対象グループ',
            'action': 'save',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # システムユーザーで更新処理
        update_user = get_user_model().objects.get(pk=1)
        self.client.force_login(update_user)
        data = {
            'selected_group': UserGroup.objects.filter(group_name='対象グループ').first().id,
            'group_name': '更新グループ',
            'action': 'save',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # メッセージ確認
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('ユーザーグループ「更新グループ」を更新しました。', str(messages[1]))
        self.assertEqual(messages[0].level_tag, 'success')

        # DB登録確認
        pc = UserGroup.objects.filter(tenant=self.user.tenant, group_name='更新グループ').first()
        self.assertEqual(pc.group_name, '更新グループ')
        self.assertFalse(pc.is_deleted)
        self.assertEqual(pc.create_user, create_user)
        self.assertEqual(pc.update_user, update_user)
        self.assertEqual(pc.tenant, self.user.tenant)
        self.assertLessEqual(abs((pc.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((pc.updated_at - timezone.now()).total_seconds()), 5)

    def test_8_2_2_1(self):
        """カテゴリ選択＋名称未入力"""
        url = reverse('register:group_manage')
        ug = UserGroup.objects.filter(tenant=self.user.tenant).first()
        ug_name_before = ug.group_name

        data = {
            'selected_group': ug.id,
            'group_name': '',
            'action': 'save',
        }
        response = self.client.post(url, data, follow=True)
        ug.refresh_from_db()
        self.assertEqual(ug.group_name, ug_name_before)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('この項目は必須です。', str(messages[0]))
        self.assertEqual(messages[0].level_tag, 'error')

    def test_8_2_2_2(self):
        """更新 存在しないID指定"""
        url = reverse('register:group_manage')
        ug = UserGroup.objects.filter(tenant=self.user.tenant).first()
        ug_name_before = ug.group_name

        data = {
            'selected_group': 99999,
            'group_name': 'not exists',
            'action': 'save',
        }
        response = self.client.post(url, data, follow=True)
        ug.refresh_from_db()
        self.assertEqual(ug.group_name, ug_name_before)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('エラーが発生しました。', str(messages[0]))
        self.assertEqual(messages[0].level_tag, 'error')

    def test_8_3_1_1(self):
        """削除処理（正常系）"""
        url = reverse('register:group_manage')
        # 削除対象
        ug = UserGroup.objects.create(
            tenant=self.user.tenant,
            group_name='削除対象',
            create_user=self.user,
            update_user=self.user,
        )

        data = {
            'selected_group': ug.id,
            'group_name': '',
            'action': 'delete',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(UserGroup.objects.filter(id=ug.id).exists())
        messages = list(get_messages(response.wsgi_request))
        self.assertIn(f'ユーザーグループ「{ug.group_name}」を削除しました。', str(messages[0]))
        self.assertEqual(messages[0].level_tag, 'success')

    def test_8_3_2_1(self):
        """削除処理（異常系：対象未選択）"""
        url = reverse('register:group_manage')
        ug = UserGroup.objects.filter(tenant=self.user.tenant).first()
        ug_name_before = ug.group_name

        data = {
            'selected_group': '',
            'group_name': '',
            'action': 'delete',
        }
        response = self.client.post(url, data, follow=True)
        ug.refresh_from_db()
        self.assertEqual(ug.group_name, ug_name_before)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn('削除対象のユーザーグループを選択してください。', str(messages[0]))
        self.assertEqual(messages[0].level_tag, 'warning')

    def test_8_3_2_2(self):
        """削除処理（異常系：関連商品あり）"""
        url = reverse('register:group_manage')
        ug = UserGroup.objects.filter(pk=1).first()
        ug_name_before = ug.group_name

        data = {
            'selected_group': 1,
            'group_name': '',
            'action': 'delete',
        }
        response = self.client.post(url, data, follow=True)
        ug.refresh_from_db()
        self.assertEqual(ug.group_name, ug_name_before)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn(f'ユーザーグループ「{ug.group_name}」は使用中のため、削除できません。', str(messages[0]))
        self.assertEqual(messages[0].level_tag, 'warning')


class InitialUserViewTests(TestCase):
    """初期ユーザー登録機能のテスト"""

    def setUp(self):
        self.client = Client()

        # ダミーテナント作成（システムユーザー用）
        self.system_tenant = Tenant.objects.create(
            tenant_name='システムテナント',
            representative_name='管理者',
            email='sys@example.com',
        )

        # システム管理者ユーザー作成
        self.system_user = get_user_model().objects.create_user(
            username='system_admin',
            email='sysadmin@example.com',
            password='pass',
            tenant=self.system_tenant,
            privilege=PRIVILEGE_SYSTEM,
        )

        self.client.login(email='sysadmin@example.com', password='pass')

    # ------------------------------------------------------
    # 正常系
    # ------------------------------------------------------
    def test_9_1_1_1(self):
        """9-1-1-1: 正常 新規登録成功 -> Tenant・CustomUser作成・リダイレクト"""
        url = reverse('register:initial_user_create')
        data = {
            'company_name': 'テスト株式会社',
            'username': '山田太郎',
            'email': 'taro@example.com',
        }

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'register/initial_user_done.html')
        context_info = response.context['register_info']
        self.assertIsNotNone(context_info)
        self.assertEqual(context_info['tenant_name'], 'テスト株式会社')

        # Tenant が作成されたか確認
        tenant = Tenant.objects.filter(tenant_name='テスト株式会社').first()
        self.assertIsNotNone(tenant)
        self.assertEqual(tenant.representative_name, '山田太郎')

        # CustomUser が作成されたか確認
        user = CustomUser.objects.filter(email='taro@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.tenant, tenant)
        self.assertTrue(user.is_active)
        self.assertEqual(user.privilege, PRIVILEGE_MANAGER)
        self.assertIsNotNone(user.password)

    # ------------------------------------------------------
    # 異常系
    # ------------------------------------------------------
    def test_9_1_2_1(self):
        """9-1-2-1: 直リンク"""
        self.client.logout()
        url = reverse('register:initial_user_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_9_1_2_2(self):
        """9-1-2-2: 権限不足"""
        get_user_model().objects.create_user(
            username='test_user',
            email='test@example.com',
            password='pass',
            tenant=self.system_tenant,
            privilege=PRIVILEGE_MANAGER,
        )

        self.client.logout()
        self.client.login(email='test@example.com', password='pass')

        url = reverse('register:initial_user_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_9_1_2_3(self):
        """9-1-2-2: 必須エラー"""
        url = reverse('register:initial_user_create')
        data = {
            'company_name': 'テスト株式会社',
            'username': '',
            'email': 'taro@example.com',
        }

        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # ステータス確認
        self.assertEqual(response.status_code, 200)

        # JSONレスポンス確認
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('この項目は必須です。', form.errors['username'])

    # ------------------------------------------------------
    # 完了画面
    # ------------------------------------------------------
    def test_9_2_1_1(self):
        """9-2-1-1: 完了画面 正常表示 セッション情報取得後に削除される"""
        session = self.client.session
        session['register_info'] = {
            'tenant_name': '株式会社ABC',
            'user_name': '佐藤花子',
            'user_email': 'hana@example.com',
        }
        session.save()

        url = reverse('register:initial_done')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        context_info = response.context['register_info']
        self.assertIsNotNone(context_info)
        self.assertEqual(context_info['tenant_name'], '株式会社ABC')

        # 再アクセス時はセッションが消えている
        response2 = self.client.get(url)
        self.assertIsNone(response2.context['register_info'])


class ProfileUpdateViewTests(TestCase):
    """
    ProfileUpdateView の単体テスト
    """
    def setUp(self):
        # テナント作成
        self.tenant = Tenant.objects.create(
            tenant_name='テストテナント',
            representative_name='代表者テスト',
            email='tenant@example.com'
        )
        # テスト用ユーザー
        self.user = CustomUser.objects.create_user(
            username='テストユーザー',
            email='test@example.com',
            password='testpass123',
            privilege=PRIVILEGE_VIEWER,
            tenant_id=self.tenant.id
        )
        self.client.login(email='test@example.com', password='testpass123')
        self.url = reverse('register:update_profile')

    # --------------------------------------------------------
    # 正常系
    # --------------------------------------------------------
    def test_10_1_1_1(self):
        """
        10-1-1-1: 正常系（全項目正しく入力 -> 更新成功）
        """
        # 参照ユーザーでログイン
        self.client.login(email='test@example.com', password='testpass123')

        data = {
            'username': '更新後ユーザー',
            'username_kana': 'コウシンゴユーザー',
            'email': 'updated@example.com',
            'tel_number': '090-1111-2222',
            'gender': '1',
            'employment_status': '1',
            'privilege': '1',
        }

        response = self.client.post(self.url, data, follow=True)

        # ステータス200＋テンプレート表示
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register/update_profile.html')

        # データ更新確認
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, '更新後ユーザー')
        self.assertEqual(self.user.email, 'updated@example.com')

        # 成功メッセージ確認
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('プロフィールを更新しました。', messages)

    # --------------------------------------------------------
    # 異常系（必須未入力）
    # --------------------------------------------------------
    def test_10_2_1_1(self):
        """
        10-2-1-1: 異常系（必須: username 未入力）
        """
        data = {
            'username': '',
            'email': 'updated@example.com',
        }

        response = self.client.post(self.url, data)

        # ステータス200（再表示）
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register/update_profile.html')

        # フォームエラー確認
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('この項目は必須です。', form.errors['username'])

    # --------------------------------------------------------
    # 異常系（メール形式不正）
    # --------------------------------------------------------
    def test_10_2_2_1(self):
        """
        10-2-2-1: 異常系（email 不正フォーマット）
        """
        data = {
            'username': 'テスト太郎',
            'email': 'invalid_email',
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('有効なメールアドレスを入力してください。', form.errors['email'])

    # --------------------------------------------------------
    # 異常系（ログインなしアクセス）
    # --------------------------------------------------------
    def test_10_3_1_1(self):
        """
        10-3-1-1: 異常系（未ログイン時アクセス）
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)


class UserChangePasswordTests(TestCase):
    """
    UserChangePassword の単体テスト
    """

    def setUp(self):
        # テナント作成
        self.tenant = Tenant.objects.create(
            tenant_name='テストテナント',
            representative_name='代表者テスト',
            email='tenant@example.com'
        )
        # テスト用ユーザー
        self.user = CustomUser.objects.create_user(
            username='テストユーザー',
            email='test@example.com',
            password='oldpass123',
            privilege=PRIVILEGE_VIEWER,
            tenant_id=self.tenant.id
        )
        self.client.login(email='test@example.com', password='oldpass123')
        self.url = reverse('register:change_password')

    # --------------------------------------------------------
    # 11-1-1-1: 正常系（パスワード変更成功）
    # --------------------------------------------------------
    def test_11_1_1_1(self):
        """
        11-1-1-1: 正常系（正しい旧パスワード・新パスワードで変更成功）
        """
        self.client.login(email='test@example.com', password='oldpass123')

        data = {
            'old_password': 'oldpass123',
            'new_password1': 'newpass456',
            'new_password2': 'newpass456',
        }

        response = self.client.post(self.url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('dashboard:top'))

        # メッセージ確認
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('パスワードが変更されました。', messages)

        # DB更新確認
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass456'))

    # --------------------------------------------------------
    # 11-2-1-1: 異常系（旧パスワード誤り）
    # --------------------------------------------------------
    def test_11_2_1_1(self):
        """
        11-2-1-1: 異常系（旧パスワード誤り）
        """
        self.client.login(email='test@example.com', password='oldpass123')

        data = {
            'old_password': 'wrongpass',
            'new_password1': 'newpass456',
            'new_password2': 'newpass456',
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register/password_change.html')

        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('old_password', form.errors)
        self.assertIn('元のパスワードが間違っています。もう一度入力してください。', form.errors['old_password'])

    # --------------------------------------------------------
    # 11-2-2-1: 異常系（新パスワード不一致）
    # --------------------------------------------------------
    def test_11_2_2_1(self):
        """
        11-2-2-1: 異常系（新パスワードが一致しない）
        """
        self.client.login(email='test@example.com', password='oldpass123')

        data = {
            'old_password': 'oldpass123',
            'new_password1': 'newpass456',
            'new_password2': 'newpass789',
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('new_password2', form.errors)
        self.assertIn('確認用パスワードが一致しません。', form.errors['new_password2'])

    # --------------------------------------------------------
    # 11-3-1-1: 異常系（未ログインアクセス）
    # --------------------------------------------------------
    def test_11_3_1_1(self):
        """
        11-3-1-1: 異常系（未ログインアクセス）
        """
        # 直リンク状態でアクセス
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)