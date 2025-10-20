import json
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
from partner_mst.views import PartnerUpdateView


class PartnerViewTests(TestCase):
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
    def test_V01(self):
        '''初期表示（正常系: データあり）'''
        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'))

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # レスポンス内容確認
        self.assertContains(response, '株式会社アルファ')

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 8)
        self.assertTrue(all(tid == 1 for tid in list.values_list('tenant_id', flat=True)))

    def test_V02(self):
        '''検索処理（正常系: キーワード）'''
        # 検索値
        key = '商事'

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'), {'search_keyword': key})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 1)
        self.assertEqual('有限会社ベータ商事', list[0].partner_name)
        self.assertEqual(key, response.context['form']['search_keyword'].value())

    def test_V03(self):
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

    def test_V04(self):
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

    def test_V04(self):
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

    def test_V06(self):
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

    def test_V07(self):
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

    def test_V08(self):
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

    def test_V09(self):
        '''検索処理（正常系: 市町村区）'''
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

    def test_V10(self):
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

    def test_V11(self):
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

    def test_V12(self):
        '''検索処理（正常系: 複合検索）'''
        # 検索値

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'), {
            'search_keyword': '九州',
            'search_partner_type': 'customer',
        })

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 1)
        self.assertEqual('九州産業株式会社', list[0].partner_name)
        self.assertEqual('九州', response.context['form']['search_keyword'].value())
        self.assertEqual('customer', response.context['form']['search_partner_type'].value())

    def test_V13(self):
        '''検索処理（正常系: 結果0件）'''
        # 検索値

        # レスポンス取得
        response = self.client.get(reverse('partner_mst:list'), {'search_keyword': 'ZZZZZZZ',})

        # ステータスコード確認
        self.assertEqual(response.status_code, 200)

        # 取得データ確認
        list = response.context['partners']
        self.assertEqual(list.count(), 0)


    def test_V14(self):
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

    def test_V15(self):
        '''初期表示（正常系: 参照ユーザー）'''
        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        url = reverse('partner_mst:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        html = response.content.decode('utf-8')

        # 新規登録ボタンが非表示
        self.assertNotIn('新規登録', html, '参照ユーザーに新規登録ボタンが表示されてはいけない')

        # 明細行の操作列（編集・削除ボタンなど）が非表示
        self.assertNotRegex(
            html,
            r'<button[^>]+(編集|削除)',
            '参照ユーザーに編集・削除ボタンが表示されてはいけない'
        )

    def test_V16(self):
        '''一覧画面表示（異常系: 未ログイン）'''
        url = reverse('partner_mst:list')

        # 未ログイン状態でアクセス
        self.client.logout()
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # 遷移後の画面確認
        self.assertRedirects(response, '/login/?next=/partner_mst/')

    #----------------
    # CreateView
    #----------------
    def test_V17(self):
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

    def test_V18(self):
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

        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # レスポンス確認
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.content)
        self.assertTrue(res_json['success'])

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

    def test_V19(self):
        '''登録処理（正常系: 異なるテナントで同じ取引先名称）'''
        # テナントを2つ作成
        self.tenant1 = Tenant.objects.create(
            tenant_name='テナントA',
            representative_name='代表A',
            contact_email='a@example.com'
        )
        self.tenant2 = Tenant.objects.create(
            tenant_name='テナントB',
            representative_name='代表B',
            contact_email='b@example.com'
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


    def test_V20(self):
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

    def test_V21(self):
        '''登録処理（異常系: 同一テナント内取引先名称重複）'''
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

    def test_V22(self):
        '''登録画面表示（異常系：権限不足）'''
        # 参照ユーザーでログイン
        self.user = get_user_model().objects.get(pk=1)
        self.client.login(email='viewer@example.com', password='pass')

        url = reverse('partner_mst:create')
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_V23(self):
        '''登録画面表示（異常系：未ログイン）'''
        url = reverse('partner_mst:create')

        # 未ログイン状態でアクセス
        self.client.logout()
        response = self.client.get(url, follow=False)

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # 遷移後の画面確認
        self.assertRedirects(response, '/login/?next=/partner_mst/create/')

    #----------------
    # UpdateView
    #----------------
    def test_V24(self):
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

    def test_V25(self):
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

    def test_V26(self):
        '''更新処理（正常系：異なるテナントで同じ取引先名称に変更）'''
        # テナントを2つ作成
        self.tenant1 = Tenant.objects.create(
            tenant_name='テナントA',
            representative_name='代表A',
            contact_email='a@example.com'
        )
        self.tenant2 = Tenant.objects.create(
            tenant_name='テナントB',
            representative_name='代表B',
            contact_email='b@example.com'
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

        # 更新データ（両方とも同じ名前に更新してみる）
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

    def test_V27(self):
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

    def test_V28(self):
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

    def test_V29(self):
        '''更新画面表示（異常系：権限不足）'''
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

        # 更新処理のURLとデータ作成
        url = reverse('partner_mst:update', args=[partner.id])
        data = {
            'partner_name': 'テスト株式会社',
            'partner_type': 'customer',
            'email': 'test@example.com',
        }

        # 処理実行
        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # ステータスコード確認
        self.assertEqual(response.status_code, 403)

    def test_V30(self):
        '''更新画面表示（異常系：未ログイン）'''
        # 事前データ作成
        partner = Partner.objects.create(
            tenant=self.user.tenant,
            partner_name='ログイン株式会社',
            partner_type='supplier',
            email='login@example.com',
            create_user=self.user,
            update_user=self.user,
        )

        # 更新処理のURLとデータ作成
        url = reverse('partner_mst:update', args=[partner.id])
        data = {
            'partner_name': 'テスト株式会社',
            'partner_type': 'customer',
            'email': 'test@example.com',
        }

        # ログアウト
        self.client.logout()

        # 処理実行
        response = self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # ステータスコード確認
        self.assertEqual(response.status_code, 302)

        # 遷移後の画面確認
        self.assertRedirects(response, f'/login/?next=/partner_mst/{partner.id}/update/')

    def test_V31(self):
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

        # ステータスコード確認
        self.assertEqual(response.status_code, 404)

        # JSONレスポンス構造確認
        self.assertJSONEqual(response.content, {'success': False})

        # メッセージ内容確認
        storage = list(messages)
        self.assertEqual(len(storage), 1)
        self.assertEqual(storage[0].message, 'この取引先は既に削除されています。')
        self.assertEqual(storage[0].level_tag, 'error')
