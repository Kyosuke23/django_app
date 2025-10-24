# tenant_mst/tests/test_models.py
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from tenant_mst.models import Tenant
import uuid


class TenantModelTests(TestCase):
    """Tenantモデルの単体テスト"""

    def setUp(self):
        self.tenant = Tenant.objects.create(tenant_name='テストテナント')
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='user@example.com',
            password='pass',
            tenant=self.tenant,
        )

    # ------------------------------------------------------------
    # tenant_name
    # ------------------------------------------------------------
    def test_1_1_1_1(self):
        """テナント名称を100文字以内で登録できること"""
        tenant = Tenant(
            tenant_name='株式会社テスト',
            representative_name='代表太郎',
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        tenant.full_clean()  # ValidationErrorが出ないことを確認
        tenant.save()
        self.assertEqual(Tenant.objects.count(), 2)

    def test_1_1_2_1(self):
        """テナント名称が空欄の場合エラー"""
        tenant = Tenant(
            tenant_name='',
            representative_name='代表太郎',
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            tenant.full_clean()

    def test_1_1_2_2(self):
        """テナント名称が101文字の場合エラー"""
        tenant = Tenant(
            tenant_name='A' * 101,
            representative_name='代表太郎',
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            tenant.full_clean()

    # ------------------------------------------------------------
    # representative_name
    # ------------------------------------------------------------
    def test_1_2_1_1(self):
        """代表者名が100文字以内で保存できる"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='A' * 100,
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        tenant.full_clean()  # エラーなし

    def test_1_2_2_1(self):
        """代表者名が101文字の場合エラー"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='A' * 101,
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            tenant.full_clean()

    # ------------------------------------------------------------
    # email
    # ------------------------------------------------------------
    def test_1_3_1_1(self):
        """正しいメールアドレス形式で保存できる"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='代表A',
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        tenant.full_clean()

    def test_1_3_2_1(self):
        """メールアドレス形式が不正な場合エラー"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='代表A',
            email='invalid@@example',
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            tenant.full_clean()

    # ------------------------------------------------------------
    # tel_number
    # ------------------------------------------------------------
    def test_1_4_1_1(self):
        """電話番号が数字＋ハイフン形式で保存できる"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com',
            tel_number='03-1234-5678',
            create_user=self.user,
            update_user=self.user,
        )
        tenant.full_clean()

    def test_1_4_2_1(self):
        """電話番号に不正文字がある場合エラー"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com',
            tel_number='03-12A4-5678',
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            tenant.full_clean()

    # ------------------------------------------------------------
    # postal_code
    # ------------------------------------------------------------
    def test_1_5_1_1(self):
        """郵便番号がハイフン付きで保存できる"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com',
            postal_code='123-4567',
            create_user=self.user,
            update_user=self.user,
        )
        tenant.full_clean()

    def test_1_5_1_2(self):
        """郵便番号がハイフンなしでも保存できる"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com',
            postal_code='1234567',
            create_user=self.user,
            update_user=self.user,
        )
        tenant.full_clean()

    def test_1_5_2_1(self):
        """郵便番号が不正形式の場合エラー"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com',
            postal_code='１２３-４５６７',
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            tenant.full_clean()

    # ------------------------------------------------------------
    # state
    # ------------------------------------------------------------
    def test_1_6_1_1(self):
        """都道府県が10文字以内で保存できる"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com',
            state='東京都',
            create_user=self.user,
            update_user=self.user,
        )
        tenant.full_clean()

    def test_1_6_2_1(self):
        """都道府県が11文字以上の場合エラー"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com',
            state='A' * 11,
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            tenant.full_clean()

    # ------------------------------------------------------------
    # city
    # ------------------------------------------------------------
    def test_1_7_1_1(self):
        """市区町村が50文字以内で保存できる"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com',
            city='千代田区',
            create_user=self.user,
            update_user=self.user,
        )
        tenant.full_clean()

    def test_1_7_2_1(self):
        """市区町村が51文字以上の場合エラー"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com',
            city='A' * 51,
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            tenant.full_clean()

    # ------------------------------------------------------------
    # address
    # ------------------------------------------------------------
    def test_1_8_1_1(self):
        """住所が100文字以内で保存できる"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com',
            address='丸の内1-1-1',
            create_user=self.user,
            update_user=self.user,
        )
        tenant.full_clean()

    def test_1_8_2_1(self):
        """住所が101文字以上の場合エラー"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com',
            address='A' * 101,
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            tenant.full_clean()

    # ------------------------------------------------------------
    # address2
    # ------------------------------------------------------------
    def test_1_9_1_1(self):
        """住所2が150文字以内で保存できる"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com',
            address2='テストビル3F',
            create_user=self.user,
            update_user=self.user,
        )
        tenant.full_clean()

    def test_1_9_2_1(self):
        """住所2が151文字以上の場合エラー"""
        tenant = Tenant(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com',
            address2='A' * 151,
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            tenant.full_clean()

    # ------------------------------------------------------------
    # constraints
    # ------------------------------------------------------------
    def test_1_10_1_1(self):
        """tenant_codeが一意であること"""
        t1 = Tenant.objects.create(
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        t2 = Tenant.objects.create(
            tenant_name='テナントB',
            representative_name='代表B',
            email='b@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        self.assertNotEqual(t1.tenant_code, t2.tenant_code)

    def test_1_10_2_1(self):
        """tenant_code重複時はIntegrityError発生"""
        code = uuid.uuid4()
        Tenant.objects.create(
            tenant_code=code,
            tenant_name='テナントA',
            representative_name='代表A',
            email='a@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(Exception):
            Tenant.objects.create(
                tenant_code=code,
                tenant_name='テナントB',
                representative_name='代表B',
                email='b@example.com',
                create_user=self.user,
                update_user=self.user,
            )
