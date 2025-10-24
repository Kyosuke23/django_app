from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from tenant_mst.models import Tenant
from bs4 import BeautifulSoup

class TenantViewTests(TestCase):
    """TenantEditView の単体テスト"""

    def setUp(self):
        self.User = get_user_model()

        # まずテナントを作成
        self.tenant = Tenant.objects.create(
            tenant_name='テナントA',
            representative_name='代表A',
            contact_email='a@example.com',
            contact_tel_number='03-1111-1111',
            postal_code='100-0001',
            state='東京都',
            city='千代田区',
            address='丸の内1-1-1',
            address2='テストビル3F',
        )

        # 管理権限ユーザー（privilege=1）
        self.manager_user = self.User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass',
            privilege=1,
            tenant=self.tenant,
        )

        # 更新権限ユーザー（privilege=2）
        self.editor_user = self.User.objects.create_user(
            username='editor',
            email='editor@example.com',
            password='pass',
            privilege=2,
            tenant=self.tenant,
        )

        # テナントにユーザーを紐づけ（create_user / update_user）
        self.tenant.create_user = self.manager_user
        self.tenant.update_user = self.manager_user
        self.tenant.save()

        # 参照API
        self.url = reverse('tenant_mst:edit')

    def test_1_1_1_1(self):
        """正常"""
        self.client.force_login(self.manager_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # 入力フォーム値を確認
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(self.tenant.tenant_name, soup.select_one('#id_tenant_name').get('value'))
        self.assertEqual(self.tenant.representative_name, soup.select_one('#id_representative_name').get('value'))
        self.assertEqual(self.tenant.contact_email, soup.select_one('#id_contact_email').get('value'))
        self.assertEqual(self.tenant.contact_tel_number, soup.select_one('#id_contact_tel_number').get('value'))
        self.assertEqual(self.tenant.postal_code, soup.select_one('#id_postal_code').get('value'))
        self.assertEqual(self.tenant.state, soup.select_one('#id_state').get('value'))
        self.assertEqual(self.tenant.city, soup.select_one('#id_city').get('value'))
        self.assertEqual(self.tenant.address, soup.select_one('#id_address').get('value'))
        self.assertEqual(self.tenant.address2, soup.select_one('#id_address2').get('value'))

    def test_1_1_2_1(self):
        """異常：未ログイン時はログインページへリダイレクト"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/?next=/tenant_mst/edit/', response.url)

    def test_1_1_2_2(self):
        """異常：更新権限ユーザーでは403"""
        self.client.force_login(self.editor_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_1_2_1_1(self):
        """正常：全項目を有効値で更新できる"""
        self.client.force_login(self.manager_user)
        post_data = {
            'tenant_name': '更新後テナント',
            'representative_name': '更新代表',
            'contact_email': 'update@example.com',
            'contact_tel_number': '03-9999-8888',
            'postal_code': '150-0001',
            'state': '東京都',
            'city': '渋谷区',
            'address': '渋谷1-2-3',
            'address2': '新ビル10F',
        }
        response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/tenant_mst/edit/')

        # DB反映確認
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.tenant_name, '更新後テナント')
        self.assertEqual(self.tenant.representative_name, '更新代表')
        self.assertEqual(self.tenant.contact_email, 'update@example.com')
        self.assertEqual(self.tenant.contact_tel_number, '03-9999-8888')
        self.assertEqual(self.tenant.postal_code, '150-0001')
        self.assertEqual(self.tenant.state, '東京都')
        self.assertEqual(self.tenant.city, '渋谷区')
        self.assertEqual(self.tenant.address, '渋谷1-2-3')
        self.assertEqual(self.tenant.address2, '新ビル10F')

    def test_1_2_1_2(self):
        """正常：他テナントに同名・同メールが存在しても更新可能"""
        other_tenant = Tenant.objects.create(
            tenant_name='同名テナント',
            representative_name='代表B',
            contact_email='same@example.com',
            create_user=self.manager_user,
            update_user=self.manager_user,
        )
        self.client.force_login(self.manager_user)
        post_data = {
            'tenant_name': other_tenant.tenant_name,
            'representative_name': '代表A',
            'contact_email': 'other@example.com',
        }
        response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/tenant_mst/edit/')
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.tenant_name, '同名テナント')

    def test_1_2_2_1(self):
        """異常：ログインせずに更新→リダイレクト"""
        post_data = {'tenant_name': '更新テスト'}
        response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/tenant_mst/edit/')

    def test_1_2_2_2(self):
        """異常：更新権限ユーザーで更新時403"""
        self.client.force_login(self.editor_user)
        post_data = {'tenant_name': '更新テナント'}
        response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 403)

    def test_1_2_2_3(self):
        """異常：メール形式が不正な場合エラー"""
        self.client.force_login(self.manager_user)
        post_data = {
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'abc@@example',
        }
        response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertIn('有効なメールアドレスを入力してください。', soup.select_one('#id_contact_email + .invalid-feedback').get_text())
        self.tenant.refresh_from_db()
        self.assertNotEqual(self.tenant.contact_email, 'abc@@example')

    def test_1_2_2_4(self):
        """異常：メール重複で更新不可"""
        other = Tenant.objects.create(
            tenant_name='他テナント',
            representative_name='代表B',
            contact_email='dup@example.com',
            create_user=self.manager_user,
            update_user=self.manager_user,
        )
        self.client.force_login(self.manager_user)
        post_data = {
            'tenant_name': other.tenant_name,
            'representative_name': '代表A',
            'contact_email': other.contact_email,
        }
        response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertIn('同じメールアドレスが既に登録されています。', soup.select_one('#id_contact_email + .invalid-feedback').get_text())
        self.tenant.refresh_from_db()
        self.assertNotEqual(self.tenant.contact_email, 'dup@example.com')

    def test_1_2_2_5(self):
        """異常：存在しないID指定で404"""
        self.client.force_login(self.manager_user)
        self.tenant.delete()
        url = reverse('tenant_mst:edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/tenant_mst/edit/')