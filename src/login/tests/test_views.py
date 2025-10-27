from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from tenant_mst.models import Tenant
from bs4 import BeautifulSoup

User = get_user_model()


class LoginViewTests(TestCase):
    """LoginView関連テスト"""

    def setUp(self):
        self.client = Client()
        self.password = 'testpass123'

        # テナント作成
        self.tenant = Tenant.objects.create(
            tenant_name='テストテナント',
            representative_name='代表者テスト',
            email='tenant@example.com'
        )

        # ユーザー作成
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=self.password,
            privilege=2,  # 更新権限
            tenant=self.tenant,
        )

    def test_1_1_1_1(self):
        """1-1-1-1: 正常系 ログイン成功"""
        response = self.client.post(reverse('login:login'), {
            'username': 'test@example.com',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard:top'))

    def test_1_1_2_1(self):
        """1-1-2-1: 異常系 ログイン失敗"""
        response = self.client.post(reverse('login:login'), {
            'username': 'test@example.com',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            '正しいメールアドレスとパスワードを入力してください。どちらのフィールドも大文字と小文字は区別されます。',
            response.context['form'].non_field_errors()
        )


class LogoutViewTests(TestCase):
    """LogoutView関連テスト"""

    def setUp(self):
        self.client = Client()
        # テナント作成
        self.tenant = Tenant.objects.create(
            tenant_name='テストテナント',
            representative_name='代表者テスト',
            email='tenant@example.com'
        )
        # ユーザー作成
        self.password = 'testpass123'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=self.password,
            privilege=2,  # 更新権限
            tenant=self.tenant,
        )
        self.client.force_login(self.user)

    def test_1_2_1_1(self):
        """1-2-1-1: 正常系 ログアウト処理"""
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login:login'))


class PasswordResetViewTests(TestCase):
    """PasswordResetView の単体テスト"""

    def setUp(self):
        self.client = Client()
        self.url = reverse('login:password_reset')
        # テナント作成
        self.tenant = Tenant.objects.create(
            tenant_name='テストテナント',
            representative_name='代表者テスト',
            email='tenant@example.com'
        )
        # ユーザー作成
        self.password = 'testpass123'
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=self.password,
            privilege=2,  # 更新権限
            tenant=self.tenant,
        )
        self.client.force_login(self.user)

    def test_1_3_1_1(self):
        """正常系 - 登録済みメールアドレスで送信成功"""
        response = self.client.post(self.url, {'email': 'test@example.com'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login:password_reset_done'))

    def test_1_3_2_1(self):
        """異常系 - 未登録メールでエラー"""
        response = self.client.post(self.url, {'email': 'notfound@example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '入力されたメールアドレスは登録されていません。')
        self.assertIn('email', response.context['form'].errors)

    def test_1_3_2_2(self):
        """異常系 - メールアドレス未入力"""
        response = self.client.post(self.url, {'email': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'この項目は必須です。')
        self.assertIn('email', response.context['form'].errors)

    def test_1_3_2_3(self):
        """異常系 - 不正なメール形式"""
        response = self.client.post(self.url, {'email': 'aaa'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '有効なメールアドレスを入力してください。')
        self.assertIn('email', response.context['form'].errors)


class PasswordResetDoneViewTests(TestCase):
    """PasswordResetDoneView関連テスト"""

    def test_1_4_1_1(self):
        """1-4-1-1: 正常系 画面表示"""
        response = self.client.get(reverse('login:password_reset_done'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/password_reset_done.html')


class PasswordResetConfirmViewTests(TestCase):
    """PasswordResetConfirmViewの単体テスト"""

    def setUp(self):
        # テナント作成
        self.tenant = Tenant.objects.create(
            tenant_name='テストテナント',
            representative_name='代表者テスト',
            email='tenant@example.com'
        )
        # ユーザー作成
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpassword',
            privilege=2,  # 更新権限
            tenant=self.tenant,
        )
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)
        self.url = reverse('login:password_reset_confirm', kwargs={
            'uidb64': self.uidb64,
            'token': self.token
        })

    def test_1_5_1_1(self):
        """正常系：トークン有効時に画面表示される"""
        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/password_reset_confirm.html')
        self.assertContains(response, '新しいパスワード')

    # def test_1_5_1_2(self):
    #     """正常系：有効トークンでパスワード変更成功"""
    #     data = {
    #         'new_password1': 'newpass123!',
    #         'new_password2': 'newpass123!',
    #     }
    #     response = self.client.post(self.url, data)
    #     print(response)
    #     self.assertRedirects(response, reverse('login:password_reset_complete'))

    #     # パスワードが更新されたことを確認
    #     self.user.refresh_from_db()
    #     self.assertTrue(self.user.check_password('newpass123!'))

    # def test_1_5_2_1_invalid_token_redirect(self):
    #     """異常系：無効トークンはエラー画面へリダイレクト"""
    #     invalid_url = reverse('login:password_reset_confirm', kwargs={
    #         'uidb64': self.uidb64,
    #         'token': 'invalid-token'
    #     })
    #     response = self.client.get(invalid_url)
    #     self.assertRedirects(response, reverse('login:password_reset_invalid'))

    # def test_1_5_2_2_invalid_uid_redirect(self):
    #     """異常系：UIDが不正な場合エラー画面へ"""
    #     invalid_uid = urlsafe_base64_encode(force_bytes(99999))
    #     url = reverse('login:password_reset_confirm', kwargs={
    #         'uidb64': invalid_uid,
    #         'token': self.token
    #     })
    #     response = self.client.get(url)
    #     self.assertRedirects(response, reverse('login:password_reset_invalid'))

    # def test_1_5_2_3_password_mismatch(self):
    #     """異常系：パスワードが一致しない"""
    #     data = {
    #         'new_password1': 'abc12345!',
    #         'new_password2': 'xyz67890!',
    #     }
    #     response = self.client.post(self.url, data)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertFormError(response, 'form', 'new_password2', 'パスワードが一致しません。')


class PasswordResetCompleteViewTests(TestCase):
    """PasswordResetCompleteView関連テスト"""

    def test_1_6_1_1(self):
        """1-6-1-1: 正常系 画面表示"""
        response = self.client.get(reverse('login:password_reset_complete'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/password_reset_complete.html')
