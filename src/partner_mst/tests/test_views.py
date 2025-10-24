import json
import csv
import io
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from partner_mst.models import Partner
from django.core.management import call_command
from bs4 import BeautifulSoup
from django.utils import timezone
from tenant_mst.models import Tenant
from partner_mst.views import HEADER_MAP
from django.contrib.messages.storage.fallback import FallbackStorage
from partner_mst.views import PartnerUpdateView, PartnerDeleteView, PartnerBulkDeleteView
from sales_order.models import SalesOrder
from django.conf import settings
from django.contrib import messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages


class PartnerViewTests(TestCase):
    '''取引先マスタ 単体テスト'''

    def setUp(self):
        '''共通データ作成'''
        self.factory = RequestFactory()

        # テストクライアント生成
        self.client = Client()

        # テストデータ投入
        call_command('loaddata', 'test_tenants.json')
        call_command('loaddata', 'test_registers.json')
        call_command('loaddata', 'test_partners.json')

        # 更新ユーザーで実施
        self.user = get_user_model().objects.get(pk=3)
        self.client.login(email='editor@example.com', password='pass')

    #----------------
    # ListView
    #----------------
    def test_1_1_1_1(self):
        '''初期表示（正常系: データあり）'''
        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'))

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # レスポンス内容確認
        self.assertContains(response, '株式会社アルファ')

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 18)
        self.assertTrue(all(tid == 1 for tid in list.values_list('tenant_id', flat=True)))

        # 要素の取得を確認
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertIsNotNone(soup.select_one('#import-btn'))
        self.assertIsNotNone(soup.select_one('#create-btn'))
        self.assertIsNotNone(soup.select_one('.edit-btn'))
        self.assertIsNotNone(soup.select_one('#bulk-delete-btn'))
        self.assertIsNotNone(soup.select_one('#check-all'))
        self.assertIsNotNone(soup.select_one('.check-item'))

    def test_1_1_1_2(self):
        '''初期表示（正常系: 参照ユーザー）'''

        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'))

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # レスポンス内容確認
        self.assertContains(response, '株式会社アルファ')

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 18)
        self.assertTrue(all(tid == 1 for tid in list.values_list('tenant_id', flat=True)))

        # 要素の取得を確認
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertIsNone(soup.select_one('#import-btn'))
        self.assertIsNone(soup.select_one('#create-btn'))
        self.assertIsNone(soup.select_one('.edit-btn'))
        self.assertIsNone(soup.select_one('#bulk-delete-btn'))
        self.assertIsNone(soup.select_one('#check-all'))
        self.assertIsNone(soup.select_one('.check-item'))

    def test_1_1_1_3(self):
        '''検索処理（正常系: 結果0件）'''
        # 検索値

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'), {'search_keyword': 'ZZZZZZZ',})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 0)

    def test_1_1_2_1(self):
        '''一覧画面表示（異常系: 直リンク）'''
        url = reverse('partner_mst:list')

        # 直リンク状態でアクセス
        self.client.logout()
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # 遷移後の画面確認
        self.assertRedirects(response, '/login/?next=/partner_mst/')

    def test_1_2_1_1(self):
        '''検索処理（正常系: キーワード->取引先区分以外）'''
        # 検索値
        key = '999'

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'), {'search_keyword': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 10)

        # 取引先区分以外に "999" が含まれていることを確認
        for p in list:
            text_values = [
                str(p.partner_name or ''),
                str(p.partner_name_kana or ''),
                str(p.contact_name or ''),
                str(p.email or ''),
                str(p.tel_number or ''),
                str(p.postal_code or ''),
                str(p.state or ''),
                str(p.city or ''),
                str(p.address or ''),
                str(p.address2 or ''),
            ]
            # どれか一つでも '999' を含めばOK
            self.assertTrue(
                any(key in v for v in text_values),
                f"{p.id} のいずれのプロパティにも '{key}' が含まれていません。: {text_values}"
            )

        # 検索後のフォーム確認
        self.assertEqual(key, response.context['form']['search_keyword'].value())

    def test_1_2_1_2(self):
        '''検索処理（正常系: キーワード->取引先区分）'''
        # 検索値
        key = '仕入'

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'), {'search_keyword': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 3)

        # 取引先区分がすべて仕入先であることを確認
        for p in list:
            self.assertEqual('仕入先', p.get_partner_type_display())

        # 検索後のフォーム確認
        self.assertEqual(key, response.context['form']['search_keyword'].value())

    def test_1_2_1_3(self):
        '''検索処理（正常系: 取引先名称）'''
        # 検索値
        key = '会社アル'

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'), {'search_partner_name': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 1)
        self.assertEqual('株式会社アルファ', list[0].partner_name)
        self.assertEqual(key, response.context['form']['search_partner_name'].value())

    def test_1_2_1_4(self):
        '''検索処理（正常系: 取引先区分）'''
        # 検索値
        key = 'both'

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'), {'search_partner_type': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 1)
        self.assertEqual('有限会社ベータ商事', list[0].partner_name)
        self.assertEqual(key, response.context['form']['search_partner_type'].value())

    def test_1_2_1_5(self):
        '''検索処理（正常系: 担当者名）'''
        # 検索値
        key = '山田'

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'), {'search_contact_name': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 1)
        self.assertEqual('大阪商会', list[0].partner_name)
        self.assertEqual(key, response.context['form']['search_contact_name'].value())

    def test_1_2_1_6(self):
        '''検索処理（正常系: メールアドレス）'''
        # 検索値
        key = '@hokkaido'

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'), {'search_email': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 1)
        self.assertEqual('北海道フーズ', list[0].partner_name)
        self.assertEqual(key, response.context['form']['search_email'].value())

    def test_1_2_1_7(self):
        '''検索処理（正常系: 電話番号）'''
        # 検索値
        key = '06-'

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'), {'search_tel_number': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 1)
        self.assertEqual('大阪商会', list[0].partner_name)
        self.assertEqual(key, response.context['form']['search_tel_number'].value())

    def test_1_2_1_8(self):
        '''検索処理（正常系: 都道府県）'''
        # 検索値
        key = '北海道'

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'), {'search_address': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 1)
        self.assertEqual('北海道', list[0].state)
        self.assertEqual(key, response.context['form']['search_address'].value())

    def test_1_2_1_9(self):
        '''検索処理（正常系: シク長槍ん）'''
        # 検索値
        key = '千代田'

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'), {'search_address': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 1)
        self.assertEqual('千代田区千代田1-1', list[0].city)
        self.assertEqual(key, response.context['form']['search_address'].value())

    def test_1_2_1_10(self):
        '''検索処理（正常系: 住所）'''
        # 検索値
        key = 'フーズビル'

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'), {'search_address': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 1)
        self.assertEqual('フーズビル', list[0].address)
        self.assertEqual(key, response.context['form']['search_address'].value())

    def test_1_2_1_11(self):
        '''検索処理（正常系: 住所2）'''
        # 検索値
        key = 'セカンドアドレス'

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'), {'search_address': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 1)
        self.assertEqual('セカンドアドレス', list[0].address2)
        self.assertEqual(key, response.context['form']['search_address'].value())

    def test_1_2_1_12(self):
        '''ページング（正常系: 1ページあたり20件、21件目が次ページに表示）'''
        url = reverse('partner_mst:list')

        # テスト初期データを削除
        Partner.objects.all().delete()

        # 21件の取引先データを作成（ページング確認用）
        Partner.objects.bulk_create([
            Partner(
                tenant=self.user.tenant,
                partner_name=f'テスト商事{i+1:02}',
                partner_name_kana=f'テストショウジ{i+1:02}',
                partner_type='customer',
                contact_name=f'担当者{i+1:02}',
                email=f'user{i+1:02}@example.com',
                tel_number=f'090-0000-{i+1:04}',
                postal_code='100-0001',
                state='東京都',
                city='千代田区',
                address='霞が関1-1-1',
                address2='ビルA',
                create_user=self.user,
                update_user=self.user,
            )
            for i in range(21)
        ])

        # 1ページ目
        response_page1 = self.client.get(url)
        self.assertEqual(response_page1.status_code, 200)

        partners_page1 = response_page1.context['partners']
        self.assertEqual(len(partners_page1), 20, '1ページ目の件数が20件であること')

        # 21件目が含まれていない
        self.assertFalse(any('テスト商事21' in p.partner_name for p in partners_page1))

        # 2ページ目
        response_page2 = self.client.get(url + '?page=2')
        self.assertEqual(response_page2.status_code, 200)

        partners_page2 = response_page2.context['partners']
        self.assertEqual(len(partners_page2), 1, '2ページ目の件数が1件であること')

        # 21件目が2ページ目に含まれる
        self.assertTrue(any('テスト商事21' in p.partner_name for p in partners_page2))


    #----------------
    # CreateView
    #----------------
    def test_2_1_1_1(self):
        '''登録画面表示（正常系）'''
        # レスポンス取得
        response = self.client.get(reverse('partner_mst:create'))

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # JSONをロード
        data = json.loads(response.content)
        html = data['html']

        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(html, 'html.parser')
        modal_title = soup.select_one('.modal-title').get_text(strip=True)

        # モーダルタイトル確認
        self.assertEqual(modal_title, '取引先: 新規登録')

    def test_2_1_2_1(self):
        '''登録画面表示（異常系：直リンク）'''
        url = reverse('partner_mst:create')

        # 直リンク状態でアクセス
        self.client.logout()
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # 遷移後の画面確認
        self.assertRedirects(response, '/login/?next=/partner_mst/create/')

    def test_2_1_2_2(self):
        '''登録画面表示（異常系：権限不足）'''

        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        url = reverse('partner_mst:create')
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_2_2_1_1(self):
        '''
        登録処理（正常系: 全項目に有効値）
        '''
        url = reverse('partner_mst:create')
        data = {
            'partner_name': 'テスト株式会社',
            'partner_name_kana': 'テストカブシキガイシャ',
            'partner_type': 'customer',
            'contact_name': '山田太郎',
            'tel_number': '0312345678',
            'email': 'test@example.com',
            'postal_code': '1000001',
            'state': '東京都',
            'city': '千代田区',
            'address': '丸の内1-1-1',
            'address2': 'ビル3F',
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
        self.assertEqual(messages[0].message, '取引先「テスト株式会社」を登録しました。')
        self.assertEqual(messages[0].level_tag, 'success')

        # DB登録確認
        partner = Partner.objects.get(partner_name='テスト株式会社')
        self.assertEqual(partner.partner_name, 'テスト株式会社')
        self.assertEqual(partner.partner_name_kana, 'テストカブシキガイシャ')
        self.assertEqual(partner.partner_type, 'customer')
        self.assertEqual(partner.contact_name, '山田太郎')
        self.assertEqual(partner.tel_number, '0312345678')
        self.assertEqual(partner.email, 'test@example.com')
        self.assertEqual(partner.postal_code, '1000001')
        self.assertEqual(partner.state, '東京都')
        self.assertEqual(partner.city, '千代田区')
        self.assertEqual(partner.address, '丸の内1-1-1')
        self.assertEqual(partner.address2, 'ビル3F')
        self.assertEqual(partner.is_deleted, False)
        self.assertEqual(partner.create_user, self.user)
        self.assertEqual(partner.update_user, self.user)
        self.assertEqual(partner.tenant, self.user.tenant)
        self.assertLessEqual(abs((partner.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((partner.updated_at - timezone.now()).total_seconds()), 5)

    def test_2_2_1_2(self):
        '''登録処理（正常系: 異なるテナントで同じ取引先名称）'''
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

        url = reverse('partner_mst:create')
        data = {
            'partner_name': '重複テスト株式会社',
            'partner_type': 'customer',
            'email': 'test@example.com'
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
        partners_t1 = Partner.objects.filter(tenant=self.tenant1, partner_name='重複テスト株式会社')
        partners_t2 = Partner.objects.filter(tenant=self.tenant2, partner_name='重複テスト株式会社')

        # 件数確認
        self.assertEqual(partners_t1.count(), 1)
        self.assertEqual(partners_t2.count(), 1)

    def test_2_2_2_1(self):
        '''
        登録処理（異常系: 直リンク）
        '''
        url = reverse('partner_mst:create')

        # ログインせずにアクセス
        self.client.logout()

        data = {
            'partner_name': 'テスト株式会社',
            'partner_name_kana': 'テストカブシキガイシャ',
            'partner_type': 'customer',
            'contact_name': '山田太郎',
            'tel_number': '0312345678',
            'email': 'test@example.com',
            'postal_code': '1000001',
            'state': '東京都',
            'city': '千代田区',
            'address': '丸の内1-1-1',
            'address2': 'ビル3F',
        }

        # 処理実行
        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # レスポンス確認
        self.assertEqual(response.status_code, 302)

    def test_2_2_2_2(self):
        '''
        登録処理（異常系: 権限不足）
        '''
        url = reverse('partner_mst:create')

        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        data = {
            'partner_name': 'テスト株式会社',
            'partner_name_kana': 'テストカブシキガイシャ',
            'partner_type': 'customer',
            'contact_name': '山田太郎',
            'tel_number': '0312345678',
            'email': 'test@example.com',
            'postal_code': '1000001',
            'state': '東京都',
            'city': '千代田区',
            'address': '丸の内1-1-1',
            'address2': 'ビル3F',
        }

        # 処理実行
        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # レスポンス確認
        self.assertEqual(response.status_code, 403)

    def test_2_2_2_3(self):
        '''登録処理（異常系: メールアドレス形式不正）'''
        url = reverse('partner_mst:create')
        data = {
            'partner_name': 'テスト株式会社',
            'partner_type': 'customer',
            'email': 'test@@test',
        }

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
        self.assertEqual(Partner.objects.filter(partner_name='テスト株式会社').count(), 0)

        # エラーメッセージをHTMLから抽出
        soup = BeautifulSoup(res_json['html'], 'html.parser')
        self.assertIn('有効なメールアドレスを入力してください。', soup.select_one('#id_email + .invalid-feedback').get_text())

    def test_2_2_2_4(self):
        '''登録処理（異常系: 同一テナント内重複）'''
        url = reverse('partner_mst:create')

        # 先に1件目を登録
        data1 = {
            'partner_name': 'テスト株式会社',
            'partner_type': 'customer',
            'email': 'test@example.com',
        }
        response1 = self.client.post(
            url,
            data1,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response1.status_code, 200)
        res_json1 = json.loads(response1.content)
        self.assertTrue(res_json1['success'])

        # 同じ取引先名称で2件目を登録
        data2 = {
            'partner_name': 'テスト株式会社',
            'partner_type': 'customer',
            'email': 'test@example.com',
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
        self.assertEqual(Partner.objects.filter(email='test@example.com').count(), 1)

        # エラーメッセージをHTMLから抽出
        soup = BeautifulSoup(res_json2['html'], 'html.parser')
        self.assertIn('同じ取引先名称とメールアドレスの組み合わせが既に登録されています。', soup.select_one('#id_partner_name + .invalid-feedback').get_text())
        self.assertIn('同じ取引先名称とメールアドレスの組み合わせが既に登録されています。', soup.select_one('#id_email + .invalid-feedback').get_text())


    #----------------
    # UpdateView
    #----------------
    def test_3_1_1_1(self):
        '''更新画面表示'''
        # レスポンス取得
        response = self.client.get(reverse('partner_mst:update', args=[1]))

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # JSONをロード
        data = json.loads(response.content)
        html = data['html']

        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(html, 'html.parser')
        modal_title = soup.select_one('.modal-title').get_text(strip=True)

        # モーダルタイトル確認
        self.assertEqual(modal_title, '取引先更新: 株式会社アルファ')

    def test_3_1_2_1(self):
        '''更新画面表示（異常系：直リンク）'''
        url = reverse('partner_mst:update', args=[1])

        # 直リンク状態でアクセス
        self.client.logout()
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # 遷移後の画面確認
        self.assertRedirects(response, '/login/?next=/partner_mst/1/update/')

    def test_3_1_2_2(self):
        '''更新画面表示（異常系：権限不足）'''
        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        url = reverse('partner_mst:update', args=[1])
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_3_1_2_3(self):
        '''
        更新処理（異常系：存在しないデータを開く）
        '''
        # リクエスト作成
        url = reverse('partner_mst:update', args=[99999])
        request = self.factory.get(url)
        request.user = self.user
        setattr(request, 'session', self.client.session)

        # メッセージストレージ設定
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # View実行
        response = PartnerUpdateView.as_view()(request, pk=99999)

        # JSONレスポンス構造確認
        self.assertJSONEqual(response.content, {'success': False})

        # ステータスコード確認
        self.assertEqual(response.status_code, 404)

        # メッセージ内容確認
        storage = list(messages)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, 'この取引先は既に削除されています。')
        self.assertEqual(storage[0].level_tag, 'error')


    def test_3_2_1_1(self):
        '''
        更新処理（正常系：全項目更新）
        '''
        # 事前データ作成
        partner = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='旧テスト株式会社',
            partner_name_kana='キュウテストカブシキガイシャ',
            partner_type='supplier',
            contact_name='佐藤一郎',
            tel_number='0311111111',
            email='old@example.com',
            postal_code='1500001',
            state='東京都',
            city='渋谷区',
            address='渋谷1-1-1',
            address2='旧ビル2F',
            create_user=self.user,
            update_user=self.user,
        )
        create_user = self.user

        # 事前データ作成ユーザーとは別のユーザーで実施
        self.user = get_user_model().objects.get(pk=2)
        self.client.login(email='manager@example.com', password='pass')

        url = reverse('partner_mst:update', args=[partner.id])
        data = {
            'partner_name': 'テスト株式会社',
            'partner_name_kana': 'テストカブシキガイシャ',
            'partner_type': 'customer',
            'contact_name': '山田太郎',
            'tel_number': '0312345678',
            'email': 'test@example.com',
            'postal_code': '1000001',
            'state': '東京都',
            'city': '千代田区',
            'address': '丸の内1-1-1',
            'address2': 'ビル3F',
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
        self.assertEqual(messages[0].message, '取引先「テスト株式会社」を更新しました。')
        self.assertEqual(messages[0].level_tag, 'success')

        # DB更新確認
        partner.refresh_from_db()
        self.assertEqual(partner.partner_name, 'テスト株式会社')
        self.assertEqual(partner.partner_name_kana, 'テストカブシキガイシャ')
        self.assertEqual(partner.partner_type, 'customer')
        self.assertEqual(partner.contact_name, '山田太郎')
        self.assertEqual(partner.tel_number, '0312345678')
        self.assertEqual(partner.email, 'test@example.com')
        self.assertEqual(partner.postal_code, '1000001')
        self.assertEqual(partner.state, '東京都')
        self.assertEqual(partner.city, '千代田区')
        self.assertEqual(partner.address, '丸の内1-1-1')
        self.assertEqual(partner.address2, 'ビル3F')
        self.assertEqual(partner.is_deleted, False)
        self.assertEqual(partner.create_user, create_user)
        self.assertEqual(partner.update_user, self.user)
        self.assertEqual(partner.tenant, self.user.tenant)
        self.assertLess((timezone.now() - partner.created_at).total_seconds(), 60)
        self.assertLessEqual(abs((partner.updated_at - timezone.now()).total_seconds()), 5)

    def test_3_2_1_2(self):
        '''更新処理（正常系：異なるテナントで同じ取引先名称+メールアドレスに変更）'''
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

        # 各テナントに取引先データを事前作成（名前は異なる）
        partner1 = Partner.objects.create(
            tenant=self.tenant1,
            partner_name='テナントA取引先',
            email='a-partner@example.com',
            partner_type='customer',
            create_user=self.user1,
            update_user=self.user1,
        )
        partner2 = Partner.objects.create(
            tenant=self.tenant2,
            partner_name='テナントB取引先',
            email='b-partner@example.com',
            partner_type='customer',
            create_user=self.user2,
            update_user=self.user2,
        )

        # 更新データ（両方とも同じ名前+メールアドレスに更新してみる）
        data = {
            'partner_name': '重複テスト株式会社',
            'partner_type': 'customer',
            'email': 'test@example.com'
        }

        # テナント1で更新
        self.client.login(email='user1@example.com', password='pass')
        url1 = reverse('partner_mst:update', args=[partner1.id])
        response = self.client.post(url1, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])

        # テナント2で更新
        self.client.logout()
        self.client.login(email='user2@example.com', password='pass')
        url2 = reverse('partner_mst:update', args=[partner2.id])
        response = self.client.post(url2, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])

        # DB確認（両テナントで同じ名前が登録されている）
        partners_t1 = Partner.objects.filter(tenant=self.tenant1, partner_name='重複テスト株式会社')
        partners_t2 = Partner.objects.filter(tenant=self.tenant2, partner_name='重複テスト株式会社')

        # 件数確認
        self.assertEqual(partners_t1.count(), 1)
        self.assertEqual(partners_t2.count(), 1)

    def test_3_2_2_1(self):
        '''
        更新処理（異常系: 直リンク）
        '''
        url = reverse('partner_mst:update', args=[1])

        # ログインせずにアクセス
        self.client.logout()

        # 事前データ作成
        Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='旧テスト株式会社',
            partner_name_kana='キュウテストカブシキガイシャ',
            partner_type='supplier',
            contact_name='佐藤一郎',
            tel_number='0311111111',
            email='old@example.com',
            postal_code='1500001',
            state='東京都',
            city='渋谷区',
            address='渋谷1-1-1',
            address2='旧ビル2F',
            create_user=self.user,
            update_user=self.user,
        )

        data = {
            'partner_name': 'テスト株式会社',
            'partner_name_kana': 'テストカブシキガイシャ',
            'partner_type': 'customer',
            'contact_name': '山田太郎',
            'tel_number': '0312345678',
            'email': 'test@example.com',
            'postal_code': '1000001',
            'state': '東京都',
            'city': '千代田区',
            'address': '丸の内1-1-1',
            'address2': 'ビル3F',
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
        登録処理（異常系: 権限不足）
        '''
        url = reverse('partner_mst:create')

        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        data = {
            'partner_name': 'テスト株式会社',
            'partner_name_kana': 'テストカブシキガイシャ',
            'partner_type': 'customer',
            'contact_name': '山田太郎',
            'tel_number': '0312345678',
            'email': 'test@example.com',
            'postal_code': '1000001',
            'state': '東京都',
            'city': '千代田区',
            'address': '丸の内1-1-1',
            'address2': 'ビル3F',
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
        '''更新処理（異常系：メールアドレス形式不正）'''
        partner = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='テスト株式会社',
            email='old@example.com',
            partner_type='customer',
            create_user=self.user,
            update_user=self.user,
        )

        url = reverse('partner_mst:update', args=[partner.id])
        data = {
            'partner_name': 'テスト株式会社',
            'partner_type': 'customer',
            'email': 'test@@test',
        }

        # レスポンス確認
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertFalse(res_json['success'])

        # 更新されていないこと
        partner.refresh_from_db()
        self.assertEqual(partner.email, 'old@example.com')

        # エラーメッセージ確認
        soup = BeautifulSoup(res_json['html'], 'html.parser')
        self.assertEqual('有効なメールアドレスを入力してください。', soup.select_one('#id_email + .invalid-feedback').get_text())

    def test_3_2_2_4(self):
        '''更新処理（異常系：同一テナント内で取引先名称＋メールアドレス重複）'''
        # 既存データ1
        partner1 = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='テスト株式会社',
            email='test@example.com',
            partner_type='customer',
            create_user=self.user,
            update_user=self.user,
        )
        # 更新対象
        partner2 = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='別会社',
            email='test2@example.com',
            partner_type='customer',
            create_user=self.user,
            update_user=self.user,
        )

        url = reverse('partner_mst:update', args=[partner2.id])
        data = {
            'partner_name': 'テスト株式会社',
            'partner_type': 'customer',
            'email': 'test@example.com',
        }

        # レスポンス確認
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertFalse(res_json['success'])

        # 更新されていないこと
        partner2.refresh_from_db()
        self.assertEqual(partner2.partner_name, '別会社')  # 更新されていない

        # エラーメッセージ確認
        soup = BeautifulSoup(res_json['html'], 'html.parser')
        self.assertIn('同じ取引先名称とメールアドレスの組み合わせが既に登録されています。', soup.select_one('#id_partner_name + .invalid-feedback').get_text())
        self.assertIn('同じ取引先名称とメールアドレスの組み合わせが既に登録されています。', soup.select_one('#id_email + .invalid-feedback').get_text())

    def test_3_2_2_5(self):
        '''
        更新処理（異常系：存在しないデータの更新）
        '''
        url = reverse('partner_mst:update', args=[99999])
        data = {
            'partner_name': 'テスト株式会社',
            'partner_name_kana': 'テストカブシキガイシャ',
            'partner_type': 'customer',
            'contact_name': '山田太郎',
            'tel_number': '0312345678',
            'email': 'test@example.com',
            'postal_code': '1000001',
            'state': '東京都',
            'city': '千代田区',
            'address': '丸の内1-1-1',
            'address2': 'ビル3F',
        }

        # RequestFactoryでPOSTリクエスト生成
        request = self.factory.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.user
        setattr(request, 'session', self.client.session)

        # メッセージストレージをリクエストに付与
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # View呼び出し
        response = PartnerUpdateView.as_view()(request, pk=99999)

        # JSONレスポンス構造確認
        self.assertJSONEqual(response.content, {'success': False})

        # ステータスコード確認
        self.assertEqual(response.status_code, 404)

        # messages.error 確認
        storage = list(messages)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, 'この取引先は既に削除されています。')
        self.assertEqual(storage[0].level_tag, 'error')

    #----------------
    # DeleteView
    #----------------
    def test_4_1_1_1(self):
        '''
        削除処理（正常系）
        '''
        # 取引先のテストデータ
        partner = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='テスト株式会社',
            email='delete@example.com',
            partner_type='customer',
            create_user=self.user,
            update_user=self.user,
        )

        # 受注テストデータ
        sales_order = SalesOrder.objects.create(
            tenant=self.user.tenant,
            partner=partner,
            sales_order_no='SO-001',
            sales_order_date='2025-09-30',
            create_user=self.user,
            update_user=self.user,
        )

        url = reverse('partner_mst:delete', args=[partner.id])
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertTrue(res_json['success'])

        # 取引先の削除確認
        self.assertFalse(Partner.objects.filter(id=partner.id).exists())

        # 受注データの取引先がNullになっていること
        sales_order.refresh_from_db()
        self.assertIsNone(sales_order.partner)

    def test_4_1_2_1(self):
        '''削除処理（異常系：直リンク）'''
        # 事前データ作成
        partner = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='ログイン株式会社',
            partner_type='supplier',
            email='login@example.com',
            create_user=self.user,
            update_user=self.user,
        )

        # 更新処理のURL作成
        url = reverse('partner_mst:delete', args=[partner.id])

        # ログアウト
        self.client.logout()

        # 処理実行
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # 遷移後の画面確認
        self.assertRedirects(response, f'/login/?next=/partner_mst/{partner.id}/delete/')

    def test_4_1_2_2(self):
        '''削除処理（異常系：権限不足）'''

        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        # 事前データ作成
        partner = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='ログイン株式会社',
            partner_type='supplier',
            email='login@example.com',
            create_user=self.user,
            update_user=self.user,
        )

        # 更新処理のURL作成
        url = reverse('partner_mst:update', args=[partner.id])

        # 処理実行
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_4_1_2_3(self):
        '''
        削除処理（異常系：存在しないデータの削除）
        '''
        url = reverse('partner_mst:delete', args=[99999])

        # RequestFactoryでPOSTリクエスト生成
        request = self.factory.post(url,  HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        request.user = self.user
        setattr(request, 'session', self.client.session)

        # メッセージストレージをリクエストに付与
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # View呼び出し
        response = PartnerDeleteView.as_view()(request, pk=99999)

        # JSONレスポンス構造確認
        self.assertJSONEqual(response.content, {'success': False})

        # ステータスコード確認
        self.assertEqual(response.status_code, 404)

        # messages.error 確認
        storage = list(messages)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, 'この取引先は既に削除されています。')
        self.assertEqual(storage[0].level_tag, 'error')


    #----------------
    # BulkDeleteView
    #----------------
    def test_5_1_1_1(self):
        '''
        一括削除（正常系）
        '''
        # 削除対象データ作成
        partner1 = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='削除対象1',
            email='p1@example.com',
            partner_type='customer',
            create_user=self.user,
            update_user=self.user,
        )
        partner2 = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='削除対象2',
            email='p2@example.com',
            partner_type='customer',
            create_user=self.user,
            update_user=self.user,
        )

        # 受注データ作成
        sales_order_1 = SalesOrder.objects.create(
            tenant=self.user.tenant,
            partner=partner1,
            sales_order_no='SO-001',
            sales_order_date='2025-09-30',
            create_user=self.user,
            update_user=self.user,
        )

        # 受注データ作成
        sales_order_2 = SalesOrder.objects.create(
            tenant=self.user.tenant,
            partner=partner2,
            sales_order_no='SO-002',
            sales_order_date='2025-09-30',
            create_user=self.user,
            update_user=self.user,
        )

        # 処理実行
        url = reverse('partner_mst:bulk_delete')
        response = self.client.post(
            url,
            {'ids': [partner1.id, partner2.id]},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # レスポンス確認
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertIn('件削除しました', res_json['message'])
        self.assertIn('2件削除しました', res_json['message'])

        # DB確認
        self.assertFalse(Partner.objects.filter(id=partner1.id).exists())
        self.assertFalse(Partner.objects.filter(id=partner2.id).exists())

        # 受注データの取引先がすべてNullになっていること
        sales_order_1.refresh_from_db()
        sales_order_2.refresh_from_db()
        self.assertIsNone(sales_order_1.partner)
        self.assertIsNone(sales_order_2.partner)

    def test_5_1_1_2(self):
        '''
        一括削除（正常系：指定なし）
        '''
        # 削除対象データ作成
        partner1 = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='削除対象1',
            email='p1@example.com',
            partner_type='customer',
            create_user=self.user,
            update_user=self.user,
        )
        partner2 = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='削除対象2',
            email='p2@example.com',
            partner_type='customer',
            create_user=self.user,
            update_user=self.user,
        )

        url = reverse('partner_mst:bulk_delete')
        response = self.client.post(url, {})  # idなし

        # リダイレクト確認
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('partner_mst:list'))

        # メッセージがセットされていることを確認
        storage = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any('削除対象が選択されていません' in str(m) for m in storage))

        # DB確認（削除されていない）
        self.assertTrue(Partner.objects.filter(id=partner1.id).exists())
        self.assertTrue(Partner.objects.filter(id=partner2.id).exists())

    def test_5_1_2_1(self):
        '''
        一括削除（異常系：直リンク）
        '''
        # 削除対象データ作成
        partner1 = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='削除対象1',
            email='p1@example.com',
            partner_type='customer',
            create_user=self.user,
            update_user=self.user,
        )
        partner2 = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='削除対象2',
            email='p2@example.com',
            partner_type='customer',
            create_user=self.user,
            update_user=self.user,
        )

        # ログアウト
        self.client.logout()

        # 処理実行
        url = reverse('partner_mst:bulk_delete')
        response = self.client.post(
            url,
            {'ids': [partner1.id, partner2.id]},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # 遷移後の画面確認
        self.assertRedirects(response, '/login/?next=/partner_mst/bulk_delete/')

        # DB確認
        self.assertTrue(Partner.objects.filter(id=partner1.id).exists())
        self.assertTrue(Partner.objects.filter(id=partner2.id).exists())

    def test_5_1_2_2(self):
        '''一括削除処理（異常系：権限不足）'''

        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        # 削除対象データ作成
        partner1 = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='削除対象1',
            email='p1@example.com',
            partner_type='customer',
            create_user=self.user,
            update_user=self.user,
        )
        partner2 = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='削除対象2',
            email='p2@example.com',
            partner_type='customer',
            create_user=self.user,
            update_user=self.user,
        )

        # 処理実行
        url = reverse('partner_mst:bulk_delete')
        response = self.client.post(
            url,
            {'ids': [partner1.id, partner2.id]},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_5_1_2_3(self):
        '''一括削除処理（異常系：部分失敗）'''

        # テスト用データ作成（1件だけ存在）
        partner = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='テスト削除',
            email='test@example.com',
            partner_type='customer',
            create_user=self.user,
            update_user=self.user,
    )

        # 実在するIDと存在しないIDを混ぜる
        valid_id = str(partner.id)
        nonexistent_id = str(partner.id + 9999)
        ids = [valid_id, nonexistent_id]

        # RequestFactory で Ajax POST リクエスト作成
        url = reverse('partner_mst:bulk_delete')
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
        response = PartnerBulkDeleteView.as_view()(request)

        # ステータスコード確認
        self.assertEqual(response.status_code, 404)

        # JSONレスポンス内容確認
        self.assertJSONEqual(response.content, {'success': False})

        # メッセージ内容確認
        storage = list(messages)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, 'すでに削除されている取引先が含まれています。')
        self.assertEqual(storage[0].level_tag, 'error')

        # 削除が実行されていないこと（ロールバック確認）
        self.assertTrue(Partner.objects.filter(id=partner.id).exists())

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
        url = reverse('partner_mst:export_csv')
        rows = self._request_and_parse(url)

        # 件数チェック（事前に8件のデータがある想定）
        self.assertEqual(len(rows) - 1, 18)

        partners = Partner.objects.filter(
            tenant=self.user.tenant,
            is_deleted=False
        ).order_by('id')

        self._assert_csv_matches_queryset(rows, partners)

    def test_6_1_1_2(self):
        '''CSVエクスポート（正常系：取引先名称検索）'''
        target = '株式会社アルファ'
        url = reverse('partner_mst:export_csv') + f'?search_partner_name={target}'
        rows = self._request_and_parse(url)
        partners = Partner.objects.filter(
            partner_name__icontains=target,
            tenant=self.user.tenant,
            is_deleted=False
        ).order_by('id')
        self.assertEqual(len(rows) - 1, partners.count())
        self._assert_csv_matches_queryset(rows, partners)

    def test_6_1_1_3(self):
        '''CSVエクスポート（正常系：0件）'''
        Partner.objects.all().delete()
        url = reverse('partner_mst:export_csv')
        rows = self._request_and_parse(url)
        # ヘッダのみ
        self.assertEqual(len(rows), 1)

    def test_6_1_1_4(self):
        '''CSVエクスポート（正常系：参照ユーザー）'''

        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        url = reverse('partner_mst:export_csv')
        rows = self._request_and_parse(url)

        # 件数チェック（事前に8件のデータがある想定）
        self.assertEqual(len(rows) - 1, 18)

        partners = Partner.objects.filter(
            tenant=self.user.tenant,
            is_deleted=False
        ).order_by('id')

        self._assert_csv_matches_queryset(rows, partners)

    def _create_max_data(self, n):
        data = []
        for i in range(n):
            p = Partner.objects.create(
                tenant=self.user.tenant,
                partner_name=f'取引先{i}',
                partner_name_kana=f'トリヒキサキ{i}',
                contact_name=f'担当者{i}',
                email=f'user{i}@example.com',
                is_deleted=False,
            )
            data.append(p)
        return data

    def test_6_1_1_5(self):
        '''CSVエクスポート（正常系：上限数以上）'''
        self._create_max_data(settings.MAX_EXPORT_ROWS + 1)
        url = reverse('partner_mst:export_check')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('warning', data)
        self.assertEqual('出力件数が上限（10,000件）を超えています。先頭10,000件のみを出力します。', data['warning'])
        self.assertNotIn('ok', data)

    def test_6_1_2_1(self):
        '''CSVエクスポート（異常系：直リンク）'''
        url = reverse('partner_mst:export_csv')

        # ログアウト
        self.client.logout()

        # アクセス実行
        response = self.client.get(url)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # 遷移後の画面確認
        self.assertRedirects(response, '/login/?next=/partner_mst/export/csv')

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
                '取引先名称', '取引先名称（カナ）', '取引先区分',
                '担当者名', 'メールアドレス', '電話番号', '郵便番号',
                '都道府県', '市区町村', '住所', '住所2'
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
        url = reverse('partner_mst:import_csv')

        # 取引先データを全削除
        Partner.objects.all().delete()

        rows = [
            {
                '取引先名称': 'テスト株式会社',
                '取引先名称（カナ）': 'テストカブシキガイシャ',
                '取引先区分': 'customer',
                '担当者名': '山田太郎',
                'メールアドレス': 'test1@example.com',
                '電話番号': '0312345678',
                '郵便番号': '1000001',
                '都道府県': '東京都',
                '市区町村': '千代田区',
                '住所': '丸の内1-1-1',
                '住所2': 'ビル3F',
            },
            {
                '取引先名称': 'サンプル商事',
                '取引先名称（カナ）': 'サンプルショウジ',
                '取引先区分': 'supplier',
                '担当者名': '佐藤花子',
                'メールアドレス': 'test2@example.com',
                '電話番号': '0459876543',
                '郵便番号': '2200002',
                '都道府県': '神奈川県',
                '市区町村': '横浜市西区',
                '住所': 'みなとみらい2-2-2',
                '住所2': 'ランドタワー10F',
            },
            {
                '取引先名称': 'グローバル合同会社',
                '取引先名称（カナ）': 'グローバルゴウドウガイシャ',
                '取引先区分': 'both',
                '担当者名': '鈴木一郎',
                'メールアドレス': 'test3@example.com',
                '電話番号': '0521234567',
                '郵便番号': '4500003',
                '都道府県': '愛知県',
                '市区町村': '名古屋市中村区',
                '住所': '名駅3-3-3',
                '住所2': 'サウスタワー5F',
            },
            {
                '取引先名称': '未来産業株式会社',
                '取引先名称（カナ）': 'ミライサンギョウカブシキガイシャ',
                '取引先区分': 'customer',
                '担当者名': '高橋次郎',
                'メールアドレス': 'test4@example.com',
                '電話番号': '0665432109',
                '郵便番号': '5300004',
                '都道府県': '大阪府',
                '市区町村': '大阪市北区',
                '住所': '梅田4-4-4',
                '住所2': 'グランビル8F',
            },
            {
                '取引先名称': 'クリエイト有限会社',
                '取引先名称（カナ）': 'クリエイトユウゲンガイシャ',
                '取引先区分': 'supplier',
                '担当者名': '田中三郎',
                'メールアドレス': 'test5@example.com',
                '電話番号': '0753456789',
                '郵便番号': '6000005',
                '都道府県': '京都府',
                '市区町村': '京都市下京区',
                '住所': '四条通5-5-5',
                '住所2': '中央ビル2F',
            },
        ]

        # CSVファイルの作成
        file = self._make_csv_file(rows)

        # レスポンス取得
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)
        # メッセージ確認
        self.assertEqual('5件をインポートしました。', res_json['message'])

        # 件数確認
        self.assertEqual(Partner.objects.count(), 5)

        # 登録値の確認
        partners = Partner.objects.order_by('email')  # email で並べて rows と突き合わせやすくする
        for row, partner in zip(sorted(rows, key=lambda x: x['メールアドレス']), partners):
            self.assertEqual(partner.partner_name, row['取引先名称'])
            self.assertEqual(partner.partner_name_kana, row['取引先名称（カナ）'])
            self.assertEqual(partner.partner_type, row['取引先区分'])
            self.assertEqual(partner.contact_name, row['担当者名'])
            self.assertEqual(partner.email, row['メールアドレス'])
            self.assertEqual(partner.tel_number, row['電話番号'])
            self.assertEqual(partner.postal_code, row['郵便番号'])
            self.assertEqual(partner.state, row['都道府県'])
            self.assertEqual(partner.city, row['市区町村'])
            self.assertEqual(partner.address, row['住所'])
            self.assertEqual(partner.address2, row['住所2'])
            self.assertEqual(partner.is_deleted, False)
            self.assertEqual(partner.create_user, self.user)
            self.assertEqual(partner.update_user, self.user)
            self.assertEqual(partner.tenant, self.user.tenant)
            self.assertLessEqual(abs((partner.created_at - timezone.now()).total_seconds()), 5)
            self.assertLessEqual(abs((partner.updated_at - timezone.now()).total_seconds()), 5)

    def test_7_1_1_2(self):
        '''CSVインポート（正常系：shift-jis）'''
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Partner.objects.all().delete()

        rows = [
            {
                '取引先名称': 'テスト株式会社',
                '取引先名称（カナ）': 'テストカブシキガイシャ',
                '取引先区分': 'customer',
                '担当者名': '山田太郎',
                'メールアドレス': 'test1@example.com',
                '電話番号': '0312345678',
                '郵便番号': '1000001',
                '都道府県': '東京都',
                '市区町村': '千代田区',
                '住所': '丸の内1-1-1',
                '住所2': 'ビル3F',
            }
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
        self.assertEqual(Partner.objects.count(), 1)

        # 登録値の確認
        partner = Partner.objects.first()
        self.assertEqual(partner.partner_name, 'テスト株式会社')
        self.assertEqual(partner.partner_name_kana, 'テストカブシキガイシャ')
        self.assertEqual(partner.partner_type, 'customer')
        self.assertEqual(partner.contact_name, '山田太郎')
        self.assertEqual(partner.email, 'test1@example.com')
        self.assertEqual(partner.tel_number, '0312345678')
        self.assertEqual(partner.postal_code, '1000001')
        self.assertEqual(partner.state, '東京都')
        self.assertEqual(partner.city, '千代田区')
        self.assertEqual(partner.address, '丸の内1-1-1')
        self.assertEqual(partner.address2, 'ビル3F')
        self.assertEqual(partner.create_user, self.user)
        self.assertEqual(partner.update_user, self.user)
        self.assertEqual(partner.tenant, self.user.tenant)
        self.assertLessEqual(abs((partner.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((partner.updated_at - timezone.now()).total_seconds()), 5)

    def test_7_1_1_3(self):
        '''CSVインポート（正常系：改行混在 CRLF/LF）'''
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Partner.objects.all().delete()

        rows = [
            {
                '取引先名称': '改行混在株式会社',
                '取引先名称（カナ）': 'カイコウコンザイカブシキガイシャ',
                '取引先区分': 'customer',
                '担当者名': '佐々木進',
                'メールアドレス': 'crlf@example.com',
                '電話番号': '0312349999',
                '郵便番号': '1000001',
                '都道府県': '東京都',
                '市区町村': '港区',
                '住所': '芝公園1-1-1',
                '住所2': '',
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
        self.assertEqual(Partner.objects.count(), 1)

        # 登録値の確認
        partner = Partner.objects.first()
        self.assertEqual(partner.partner_name, '改行混在株式会社')
        self.assertEqual(partner.partner_name_kana, 'カイコウコンザイカブシキガイシャ')
        self.assertEqual(partner.partner_type, 'customer')
        self.assertEqual(partner.contact_name, '佐々木進')
        self.assertEqual(partner.email, 'crlf@example.com')
        self.assertEqual(partner.tel_number, '0312349999')
        self.assertEqual(partner.postal_code, '1000001')
        self.assertEqual(partner.state, '東京都')
        self.assertEqual(partner.city, '港区')
        self.assertEqual(partner.address, '芝公園1-1-1')
        self.assertEqual(partner.address2, None)
        self.assertEqual(partner.create_user, self.user)
        self.assertEqual(partner.update_user, self.user)
        self.assertEqual(partner.tenant, self.user.tenant)
        self.assertLessEqual(abs((partner.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((partner.updated_at - timezone.now()).total_seconds()), 5)

    def test_7_1_1_4(self):
        '''CSVインポート（正常系：空行スキップ）'''
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Partner.objects.all().delete()

        # データの作成
        rows = [
            {'取引先名称': '空行スキップ株式会社', '取引先名称（カナ）': 'クウギョウスキップカブシキガイシャ',
             '取引先区分': 'customer', '担当者名': '田原正義', 'メールアドレス': 'skip@example.com',
             '電話番号': '0311111111', '郵便番号': '1000001', '都道府県': '東京都',
             '市区町村': '千代田区', '住所': '丸の内1-1-1', '住所2': ''}
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
        self.assertEqual(Partner.objects.count(), 1)

        # 登録値の確認
        partner = Partner.objects.first()
        self.assertEqual(partner.partner_name, '空行スキップ株式会社')
        self.assertEqual(partner.partner_name_kana, 'クウギョウスキップカブシキガイシャ')
        self.assertEqual(partner.partner_type, 'customer')
        self.assertEqual(partner.contact_name, '田原正義')
        self.assertEqual(partner.email, 'skip@example.com')
        self.assertEqual(partner.tel_number, '0311111111')
        self.assertEqual(partner.postal_code, '1000001')
        self.assertEqual(partner.state, '東京都')
        self.assertEqual(partner.city, '千代田区')
        self.assertEqual(partner.address, '丸の内1-1-1')
        self.assertEqual(partner.address2, None)
        self.assertEqual(partner.create_user, self.user)
        self.assertEqual(partner.update_user, self.user)
        self.assertEqual(partner.tenant, self.user.tenant)
        self.assertLessEqual(abs((partner.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((partner.updated_at - timezone.now()).total_seconds()), 5)

    def test_7_1_1_5(self):
        '''CSVインポート（正常系：ヘッダ順入替え）'''
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Partner.objects.all().delete()

        # データの作成
        header = ['メールアドレス', '取引先名称', '取引先区分', '取引先名称（カナ）', '担当者名',
                  '電話番号', '郵便番号', '都道府県', '市区町村', '住所', '住所2']
        rows = [
            {
                'メールアドレス': 'order@example.com',
                '取引先名称': '順序入替株式会社',
                '取引先区分': 'supplier',
                '取引先名称（カナ）': 'ジュンジョイレカエカブシキガイシャ',
                '担当者名': '並木優',
                '電話番号': '0422222222',
                '郵便番号': '1800001',
                '都道府県': '東京都',
                '市区町村': '武蔵野市',
                '住所': '吉祥寺1-2-3',
                '住所2': '順序ビル5F',
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
        self.assertEqual(Partner.objects.count(), 1)

        # 登録値確認
        partner = Partner.objects.first()
        self.assertEqual(partner.partner_name, '順序入替株式会社')
        self.assertEqual(partner.partner_name_kana, 'ジュンジョイレカエカブシキガイシャ')
        self.assertEqual(partner.partner_type, 'supplier')
        self.assertEqual(partner.contact_name, '並木優')
        self.assertEqual(partner.email, 'order@example.com')
        self.assertEqual(partner.tel_number, '0422222222')
        self.assertEqual(partner.postal_code, '1800001')
        self.assertEqual(partner.state, '東京都')
        self.assertEqual(partner.city, '武蔵野市')
        self.assertEqual(partner.address, '吉祥寺1-2-3')
        self.assertEqual(partner.address2, '順序ビル5F')
        self.assertEqual(partner.create_user, self.user)
        self.assertEqual(partner.update_user, self.user)
        self.assertEqual(partner.tenant, self.user.tenant)
        self.assertLessEqual(abs((partner.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((partner.updated_at - timezone.now()).total_seconds()), 5)

    def test_7_1_1_6(self):
        '''CSVインポート（正常系：住所に改行含む）'''
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Partner.objects.all().delete()

        # CSVファイルの作成
        rows = [{
            '取引先名称': '改行住所株式会社',
            '取引先名称（カナ）': 'カイギョウジュウショカブシキガイシャ',
            '取引先区分': 'customer',
            '担当者名': '改行一郎',
            'メールアドレス': 'newline@example.com',
            '電話番号': '0333333333',
            '郵便番号': '1000001',
            '都道府県': '東京都',
            '市区町村': '中央区',
            '住所': '日本橋1-1-1\nオフィスA',
            '住所2': '',
        }]
        file = self._make_csv_file(rows)

        # レスポンス確認
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # エラーメッセージ確認
        self.assertEqual('1件をインポートしました。', res_json['message'])

        # 件数確認
        self.assertEqual(Partner.objects.count(), 1)

        # 登録値の確認
        partner = Partner.objects.first()
        self.assertEqual(partner.address, '日本橋1-1-1オフィスA')
        self.assertEqual(partner.partner_name, '改行住所株式会社')
        self.assertEqual(partner.partner_type, 'customer')
        self.assertEqual(partner.email, 'newline@example.com')
        self.assertEqual(partner.create_user, self.user)
        self.assertEqual(partner.update_user, self.user)
        self.assertEqual(partner.tenant, self.user.tenant)
        self.assertLessEqual(abs((partner.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((partner.updated_at - timezone.now()).total_seconds()), 5)

    def test_7_1_2_1(self):
        '''CSVインポート（異常系：直リンク）'''
        self.client.logout()
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Partner.objects.all().delete()

        # CSVファイルの作成
        file = self._make_csv_file([{'取引先名称':'直リンク株式会社','取引先区分':'customer','メールアドレス':'nologin@example.com'}])

        # レスポンスを取得
        response = self.client.post(url, {'file': file})

        # 登録されていないことを確認
        self.assertEqual(Partner.objects.count(), 0)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # リダイレクト先を確認
        self.assertRedirects(response, r'/login/?next=/partner_mst/import/csv')

    def test_7_1_2_2(self):
        '''CSVインポート（異常系：権限不足）'''
        # 現在ログイン中ユーザーをviewer権限に変更
        self.user.privilege = '3'
        self.user.save()
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Partner.objects.all().delete()

        # テストデータ
        rows = [{
            '取引先名称': '権限不足株式会社',
            '取引先名称（カナ）': 'ケンゲンフソクカブシキガイシャ',
            '取引先区分': 'customer',
            '担当者名': '制限太郎',
            'メールアドレス': 'viewer@example.com',
            '電話番号': '0300000000',
            '郵便番号': '1000001',
            '都道府県': '東京都',
            '市区町村': '港区',
            '住所': '芝公園1-1-1',
            '住所2': ''
        }]

        # CSVファイルの作成
        file = self._make_csv_file(rows)

        # レスポンスを取得
        response = self.client.post(url, {'file': file})

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

        # 登録されていないことを確認
        self.assertEqual(Partner.objects.count(), 0)

    def test_7_1_2_3(self):
        '''CSVインポート（異常系：複数フィールド・複数行エラー）'''
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Partner.objects.all().delete()

        rows = [
            {
                '取引先名称': '',
                '取引先名称（カナ）': 'テストカブシキガイシャ',
                '取引先区分': 'testtype',
                '担当者名': '山田太郎',
                'メールアドレス': 'test1@example.com',
                '電話番号': '0312345678',
                '郵便番号': '1000001',
                '都道府県': '東京都',
                '市区町村': '千代田区',
                '住所': '丸の内1-1-1',
                '住所2': 'ビル3F',
            },
            {
                '取引先名称': 'サンプル商事',
                '取引先名称（カナ）': 'サンプルショウジ',
                '取引先区分': 'supplier',
                '担当者名': '佐藤花子',
                'メールアドレス': 'test2@@example.com',
                '電話番号': '04598@76543',
                '郵便番号': '2200002',
                '都道府県': '神奈川県',
                '市区町村': '横浜市西区',
                '住所': 'みなとみらい2-2-2',
                '住所2': 'ランドタワー10F',
            },
        ]
        file = self._make_csv_file(rows)

        res = self.client.post(url, {'file': file})
        self.assertEqual(res.status_code, 400)
        res_json = json.loads(res.content)

        # 期待メッセージ確認
        self.assertEqual('CSVに問題があります。', res_json.get('error', ''))
        self.assertIn('2行目:', res_json.get('details', '')[0])
        self.assertIn('この項目は必須です。', res_json.get('details', '')[0])
        self.assertIn('正しく選択してください。 testtype は候補にありません。', res_json.get('details', '')[0])
        self.assertIn('3行目:', res_json.get('details', '')[1])
        self.assertIn('有効なメールアドレスを入力してください。', res_json.get('details', '')[1])
        self.assertIn('数字とハイフンのみ使用できます。', res_json.get('details', '')[1])

    def test_7_1_2_4(self):
        '''CSVインポート（異常系：重複エラー）'''
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Partner.objects.all().delete()

        # 先行データ
        Partner.objects.create(
            tenant=self.user.tenant, partner_name='既存株式会社',
            email='dup@example.com', partner_type='both',
            contact_name='既存太郎', create_user=self.user, update_user=self.user
        )

        # 重複発生用データ
        rows = [{
            '取引先名称': '既存株式会社',
            '取引先名称（カナ）': 'キゾンカブシキガイシャ',
            '取引先区分': 'customer',
            '担当者名': '新太郎',
            'メールアドレス': 'dup@example.com',
            '電話番号': '0312340000',
            '郵便番号': '1000001',
            '都道府県': '東京都',
            '市区町村': '港区',
            '住所': '芝1-1-1',
            '住所2': ''
        }]

        # CSVファイルを作成する
        file = self._make_csv_file(rows)

        # レスポンス確認
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)

        # ステータスコード確認
        self.assertEqual(response.status_code, 400)

        # メッセージ確認
        self.assertEqual('CSVに問題があります。', res_json['error'])
        self.assertTrue(any('既に存在' in s for s in res_json['details']))

        # 件数確認
        self.assertEqual(Partner.objects.count(), 1)

    def test_7_1_2_5(self):
        '''CSVインポート（異常系：部分失敗）'''
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Partner.objects.all().delete()

        # CSVファイルの作成
        rows = [
            {'取引先名称': '正常株式会社', '取引先名称（カナ）': 'セイジョウカブシキガイシャ',
             '取引先区分': 'customer', '担当者名': '正常太郎',
             'メールアドレス': 'ok@example.com', '電話番号': '0312345678',
             '郵便番号': '1000001', '都道府県': '東京都', '市区町村': '千代田区',
             '住所': '丸の内1-1-1', '住所2': ''},
            {'取引先名称': '', '取引先名称（カナ）': '', '取引先区分': '',
             '担当者名': '', 'メールアドレス': 'ng@example.com', '電話番号': '',
             '郵便番号': '', '都道府県': '', '市区町村': '', '住所': '', '住所2': ''}
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
        self.assertEqual(Partner.objects.count(), 0)

    def test_7_1_2_6(self):
        '''CSVインポート（異常系：ヘッダ欠落）'''
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Partner.objects.all().delete()

        # CSVファイルの作成
        header = ['取引先名称', '取引先名称（カナ）', '取引先区分', 'メールアドレス',
                  '電話番号', '郵便番号', '都道府県', '市区町村', '住所', '住所2']
        rows = [
            {'取引先名称': '正常株式会社', '取引先名称（カナ）': 'セイジョウカブシキガイシャ',
             '取引先区分': 'customer',
             'メールアドレス': 'ok@example.com', '電話番号': '0312345678',
             '郵便番号': '1000001', '都道府県': '東京都', '市区町村': '千代田区',
             '住所': '丸の内1-1-1', '住所2': ''},
        ]
        file = self._make_csv_file(rows=rows, header=header)

        res = self.client.post(url, {'file': file})
        self.assertEqual(res.status_code, 400)
        res_json = json.loads(res.content)
        self.assertEqual('CSVヘッダが正しくありません。', res_json.get('error', ''))
        self.assertEqual("不足: ['担当者名'] / 期待: ['取引先名称', '取引先名称（カナ）', '取引先区分', '担当者名', 'メールアドレス', '電話番号', '郵便番号', '都道府県', '市区町村', '住所', '住所2'] / 実際: ['取引先名称', '取引先名称（カナ）', '取引先区分', 'メールアドレス', '電話番号', '郵便番号', '都道府県', '市区町村', '住所', '住所2']", res_json.get('details', ''))

    def test_7_1_2_7(self):
        '''CSVインポート（異常系：ヘッダ過多）'''
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Partner.objects.all().delete()

        # ヘッダ指定でデータ作成
        header = ['取引先名称', '取引先名称（カナ）', '取引先区分', '担当者名', 'メールアドレス',
                  '電話番号', '郵便番号', '都道府県', '市区町村', '住所', '住所2', 'テナント']
        rows = [
            {'取引先名称': '正常株式会社', '取引先名称（カナ）': 'セイジョウカブシキガイシャ',
             '取引先区分': 'customer', '担当者名': 'テスト担当者',
             'メールアドレス': 'ok@example.com', '電話番号': '0312345678',
             '郵便番号': '1000001', '都道府県': '東京都', '市区町村': '千代田区',
             '住所': '丸の内1-1-1', '住所2': '', 'テナント': 'X'},
        ]

        # CSVファイルの作成
        file = self._make_csv_file(rows, header=header)

        # レスポンス確認
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)

        # エラーメッセージ確認
        self.assertEqual('想定外のヘッダが含まれています。', res_json['error'])
        self.assertEqual("不要: ['テナント'] / 許可: ['取引先名称', '取引先名称（カナ）', '取引先区分', '担当者名', 'メールアドレス', '電話番号', '郵便番号', '都道府県', '市区町村', '住所', '住所2']", res_json['details'])

        # 件数確認
        self.assertEqual(Partner.objects.count(), 0)

    def test_7_1_2_8(self):
        '''CSVインポート（異常系：重複ヘッダ）'''
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Partner.objects.all().delete()

        # ヘッダ指定でデータ作成
        header = ['取引先名称', '取引先名称（カナ）', '取引先名称（カナ）', '取引先区分', '担当者名', 'メールアドレス',
                  '電話番号', '郵便番号', '都道府県', '市区町村', '住所', '住所2']
        rows = [
            {'取引先名称': '正常株式会社', '取引先名称（カナ）': 'セイジョウカブシキガイシャ', '取引先名称（カナ）': 'セイジョウカブシキガイシャ',
             '取引先区分': 'customer', '担当者名': 'テスト担当者',
             'メールアドレス': 'ok@example.com', '電話番号': '0312345678',
             '郵便番号': '1000001', '都道府県': '東京都', '市区町村': '千代田区',
             '住所': '丸の内1-1-1', '住所2': ''},
        ]

        # CSVファイルの作成
        file = self._make_csv_file(rows, header=header)

        # レスポンス確認
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)

        # エラーメッセージ確認
        self.assertEqual('CSVヘッダが重複しています。', res_json['error'])
        self.assertEqual("重複: ['取引先名称（カナ）']", res_json['details'])

        # 件数確認
        self.assertEqual(Partner.objects.count(), 0)

    def test_7_1_2_9(self):
        '''CSVインポート（異常系：拡張子不正）'''
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Partner.objects.all().delete()

         # CSVファイルの作成
        file = SimpleUploadedFile('test.txt', b'dummy text', content_type='text/plain')

        # レスポンス確認
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)

        # エラーメッセージ確認
        self.assertEqual('CSVファイル（.csv）のみアップロード可能です。', res_json['error'])

        # 件数確認
        self.assertEqual(Partner.objects.count(), 0)

    def test_7_1_2_10(self):
        '''CSVインポート（異常系：サイズ超過）'''
        url = reverse('partner_mst:import_csv')

        # データを削除しておく
        Partner.objects.all().delete()

        # サイズ超過分のデータ値作成
        large_content = b'a' * (settings.MAX_FILE_SIZE + 1)

        # CSVファイルの作成
        file = SimpleUploadedFile('large.csv', large_content, content_type='text/csv')

        # レスポンス取得
        response = self.client.post(url, {'file': file})
        res_json = json.loads(response.content)
        self.assertEqual(response.status_code, 400)

        # エラーメッセージ確認
        self.assertEqual('ファイルサイズが上限を超えています。', res_json['error'])

        # 件数確認
        self.assertEqual(Partner.objects.count(), 0)