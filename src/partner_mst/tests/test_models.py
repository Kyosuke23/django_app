from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from tenant_mst.models import Tenant
from partner_mst.models import Partner


class PartnerModelTests(TestCase):
    """Partnerモデルの単体テスト"""

    def setUp(self):
        self.tenant_a = Tenant.objects.create(tenant_name='TenantA')
        self.tenant_b = Tenant.objects.create(tenant_name='TenantB')
        self.user = get_user_model().objects.create_user(
            username='test_user', email='user@example.com', password='pass', tenant=self.tenant_a
        )

    # ------------------------------------------------------------
    # partner_name
    # ------------------------------------------------------------
    def test_1_1_1_1(self):
        """取引先名称を100文字以内で登録できること"""
        partner = Partner(
            tenant=self.tenant_a,
            partner_name='株式会社テスト',
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        partner.full_clean()  # ValidationErrorが出ないこと

    def test_1_1_1_2(self):
        """取引先名称が上限100文字で保存できること"""
        name = "A" * 100
        partner = Partner(
            tenant=self.tenant_a,
            partner_name=name,
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        partner.full_clean()  # 問題なし
        partner.save()
        self.assertEqual(Partner.objects.count(), 1)

    def test_1_1_1_3(self):
        """異なるtenantで同一名称を登録できること"""
        Partner.objects.create(
            tenant=self.tenant_a,
            partner_name='同名企業',
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        Partner.objects.create(
            tenant=self.tenant_b,
            partner_name='同名企業',
            email='test2@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        self.assertEqual(Partner.objects.count(), 2)

    def test_1_1_2_1(self):
        """取引先名称を空欄にした場合エラーになること"""
        partner = Partner(
            tenant=self.tenant_a,
            partner_name='',
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            partner.full_clean()

    def test_1_1_2_2(self):
        """取引先名称が101文字を超える場合エラーとなること"""
        partner = Partner(
            tenant=self.tenant_a,
            partner_name='A' * 101,
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            partner.full_clean()

    # ------------------------------------------------------------
    # partner_name_kana
    # ------------------------------------------------------------
    def test_1_2_1_1(self):
        """カナ名称を入力して登録できること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='株式会社テスト',
            partner_name_kana='カブシキガイシャテスト',
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        p.full_clean()

    def test_1_2_1_2(self):
        """カナ名称が上限100文字で保存できること"""
        kana = "ア" * 100
        p = Partner(
            tenant=self.tenant_a,
            partner_name='株式会社テスト',
            partner_name_kana=kana,
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        p.full_clean()
        p.save()
        self.assertEqual(Partner.objects.count(), 1)

    def test_1_2_2_1(self):
        """カナ名称が101文字以上で登録できないこと"""
        kana = "ア" * 101
        p = Partner(
            tenant=self.tenant_a,
            partner_name='株式会社テスト',
            partner_name_kana=kana,
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            p.full_clean()

    # ------------------------------------------------------------
    # partner_type
    # ------------------------------------------------------------
    def test_1_3_1_1(self):
        """顧客・仕入先・両方を選択して登録できること"""
        for val in ['customer', 'supplier', 'both']:
            p = Partner(
                tenant=self.tenant_a,
                partner_name=f'テスト{val}',
                partner_type=val,
                email='test@example.com',
                create_user=self.user,
                update_user=self.user,
            )
            p.full_clean()

    def test_1_3_2_1(self):
        """定義外の値を指定した場合エラーとなること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='不正取引先',
            partner_type='unknown',
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            p.full_clean()

    # ------------------------------------------------------------
    # contact_name
    # ------------------------------------------------------------
    def test_1_4_1_1(self):
        """担当者名を50文字以内で登録できること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            contact_name='担当太郎',
            create_user=self.user,
            update_user=self.user,
        )
        p.full_clean()

    def test_1_4_1_2(self):
        """担当者名が上限50文字で保存できること"""
        name = "A" * 50
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            contact_name=name,
            create_user=self.user,
            update_user=self.user,
        )
        p.full_clean()

    def test_1_4_2_1(self):
        """担当者名が51文字以上の場合エラーになること"""
        name = "A" * 51
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            contact_name=name,
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            p.full_clean()

    # ------------------------------------------------------------
    # tel_number
    # ------------------------------------------------------------
    def test_1_5_1_1(self):
        """電話番号を数字＋ハイフン形式で登録できること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            tel_number='03-1234-5678',
            create_user=self.user,
            update_user=self.user,
        )
        p.full_clean()

    def test_1_5_2_1(self):
        """電話番号に数字・ハイフン以外を含む場合エラーになること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            tel_number='03-12A4-5678',
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            p.full_clean()

    # ------------------------------------------------------------
    # email
    # ------------------------------------------------------------
    def test_1_6_1_1(self):
        """メールアドレス形式を満たす場合保存できること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        p.full_clean()

    def test_1_6_2_1(self):
        """メールアドレス形式が不正な場合エラーになること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@@example',
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            p.full_clean()

    # ------------------------------------------------------------
    # postal_code
    # ------------------------------------------------------------
    def test_1_7_1_1(self):
        """郵便番号を「数字＋ハイフン」で登録できること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            postal_code='123-4567',
            create_user=self.user,
            update_user=self.user,
        )
        p.full_clean()

    def test_1_7_2_1(self):
        """郵便番号に数字・ハイフン以外を含む場合エラーになること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            postal_code='１２３-４５６７',
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            p.full_clean()

    # ------------------------------------------------------------
    # state
    # ------------------------------------------------------------
    def test_1_8_1_1(self):
        """都道府県を10文字以内で登録できること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            state='東京都',
            create_user=self.user,
            update_user=self.user,
        )
        p.full_clean()

    def test_1_8_1_2(self):
        """都道府県が上限10文字で保存できること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            state='A' * 10,
            create_user=self.user,
            update_user=self.user,
        )
        p.full_clean()

    def test_1_8_2_1(self):
        """都道府県が11文字以上の場合エラーになること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            state='A' * 11,
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            p.full_clean()

    # ------------------------------------------------------------
    # city
    # ------------------------------------------------------------
    def test_1_9_1_1(self):
        """市区町村を50文字以内で登録できること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            city='千代田区',
            create_user=self.user,
            update_user=self.user,
        )
        p.full_clean()

    def test_1_9_1_2(self):
        """市区町村が上限50文字で保存できること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            city='A' * 50,
            create_user=self.user,
            update_user=self.user,
        )
        p.full_clean()

    def test_1_9_2_1(self):
        """市区町村が51文字以上の場合エラーになること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            city='A' * 51,
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            p.full_clean()

    # ------------------------------------------------------------
    # address / address2
    # ------------------------------------------------------------
    def test_1_10_1_1(self):
        """住所1を100文字以内で登録できること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            address='丸の内1-1-1',
            create_user=self.user,
            update_user=self.user,
        )
        p.full_clean()

    def test_1_10_2_1(self):
        """住所1が101文字以上の場合エラーになること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            address='A' * 101,
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_1_11_1_1(self):
        """住所2を150文字以内で登録できること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            address2='テストビル3F',
            create_user=self.user,
            update_user=self.user,
        )
        p.full_clean()

    def test_1_11_2_1(self):
        """住所2が151文字以上の場合エラーになること"""
        p = Partner(
            tenant=self.tenant_a,
            partner_name='A社',
            email='test@example.com',
            address2='A' * 151,
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(ValidationError):
            p.full_clean()

    # ------------------------------------------------------------
    # constraints
    # ------------------------------------------------------------
    def test_1_12_1_1(self):
        """tenant＋partner_name＋emailの組合せが一意であること"""
        Partner.objects.create(
            tenant=self.tenant_a,
            partner_name='A社',
            email='a@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        Partner.objects.create(
            tenant=self.tenant_a,
            partner_name='A社B',
            email='a@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        self.assertEqual(Partner.objects.count(), 2)

    def test_1_12_2_1(self):
        """tenant＋partner_name＋emailが重複する場合保存できないこと"""
        Partner.objects.create(
            tenant=self.tenant_a,
            partner_name='A社',
            email='a@example.com',
            create_user=self.user,
            update_user=self.user,
        )
        with self.assertRaises(IntegrityError):
            Partner.objects.create(
                tenant=self.tenant_a,
                partner_name='A社',
                email='a@example.com',
                create_user=self.user,
                update_user=self.user,
            )