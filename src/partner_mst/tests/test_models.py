from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from partner_mst.models import Partner
from tenant_mst.models import Tenant
from django.utils import timezone


class PartnerModelTests(TestCase):
    '''Partnerモデル単体テスト（全50ケース）'''

    def setUp(self):
        '''共通のTenantとUserを作成'''
        User = get_user_model()
        self.tenant = Tenant.objects.create(tenant_name='テストテナント')

        # tenant紐付けありユーザー作成
        self.user = User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='pass',
            tenant=self.tenant
        )

    def create_partner(self, **kwargs):
        '''共通フィールド付きPartner生成'''
        defaults = dict(
            tenant=self.tenant,
            create_user=self.user,
            update_user=self.user,
            partner_name='取引先A',
            email='a@example.com'
        )
        defaults.update(kwargs)
        return Partner(**defaults)

    # M01 partner_name
    def test_M01(self):
        '''M01: partner_name 正常登録の確認'''
        p = self.create_partner(partner_name='有効な取引先', email='valid@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, '有効な取引先')
        self.assertEqual(saved.email, 'valid@example.com')
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M01a(self):
        '''M01a: partner_name 桁数上限（100文字）'''
        p = self.create_partner(partner_name='A' * 100, email='valid@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A' * 100)
        self.assertEqual(saved.email, 'valid@example.com')
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M01b(self):
        '''M01b: partner_name 必須エラー'''
        p = self.create_partner(partner_name='')
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_M01c(self):
        '''M01c: partner_name 桁数超過（101文字）'''
        p = self.create_partner(partner_name='A' * 101, email='valid@example.com')
        with self.assertRaises(ValidationError):
            p.full_clean()

    # M02 partner_name_kana
    def test_M02(self):
        '''M01: partner_name 正常登録の確認'''
        p = self.create_partner(partner_name_kana='ﾄﾘﾋｷｻｷ', partner_name='A', email='kana@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.partner_name_kana, 'ﾄﾘﾋｷｻｷ')
        self.assertEqual(saved.email, 'kana@example.com')
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M02a(self):
        '''M01a: partner_name_kana 桁数上限（100文字）'''
        p = self.create_partner(partner_name_kana='ｱ' * 100, partner_name='A', email='kana@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.partner_name_kana, 'ｱ' * 100)
        self.assertEqual(saved.email, 'kana@example.com')
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M02b(self):
        '''M02b: partner_name_kana 桁数超過（101文字）'''
        p = self.create_partner(partner_name_kana='ｱ' * 101, partner_name='A',  email='kana@example.com')
        with self.assertRaises(ValidationError):
            p.full_clean()

    # M03 partner_type
    def test_M03(self):
        '''M03: partner_type 正常登録の確認'''
        p = self.create_partner(partner_type='customer', partner_name='A', email='type@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.partner_type, 'customer')
        self.assertEqual(saved.email, 'type@example.com')
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M03a(self):
        '''M03a: partner_type デフォルト値の確認'''
        p = self.create_partner(partner_name='A', email='type@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.partner_type, 'customer')
        self.assertEqual(saved.email, 'type@example.com')
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M03b(self):
        '''M03b: partner_type 不正値登録'''
        p = Partner(partner_type='invalid', partner_name='A', email='type@example.com')
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_M03c(self):
        '''M03c: partner_type Null登録'''
        p = Partner(partner_type=None, partner_name='A', email='type@example.com')
        with self.assertRaises(ValidationError):
            p.full_clean()

    # M04 contact_name
    def test_M04(self):
        '''M04: contact_name 正常登録の確認'''
        p = self.create_partner(contact_name='担当 太郎', partner_name='A', email='contact@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.contact_name, '担当 太郎')
        self.assertEqual(saved.email, 'contact@example.com')
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M04a(self):
        '''M04a: contact_name 桁数上限（50文字）'''
        p = self.create_partner(contact_name='A' * 50, partner_name='A', email='contact@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.contact_name, 'A' * 50)
        self.assertEqual(saved.email, 'contact@example.com')
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M04b(self):
        '''M04b: contact_name 桁数超過（51文字）'''
        p = Partner(contact_name='A' * 51, partner_name='A', email='contact@example.com')
        with self.assertRaises(ValidationError):
            p.full_clean()

    # M05 email
    def test_M05(self):
        '''M05: email 正常登録の確認'''
        p = self.create_partner(email='mail@example.com', partner_name='A')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.email, 'mail@example.com')
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M05a(self):
        '''M05a: email 桁数上限（254文字）'''
        email = ('a' * 248) + '@x.com'
        p = self.create_partner(email=email, partner_name='A')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.email, email)
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M05b(self):
        '''M05b: partner_name 必須エラー'''
        p = Partner(email='', partner_name='A')
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_M05c(self):
        '''M05c: email 桁数超過（255文字）'''
        p = Partner(email=('a' * 249) + '@x.com', partner_name='A')
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_M05d(self):
        '''M05d: email 形式エラー'''
        p = Partner(email='test@@example', partner_name='A')
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_M05e(self):
        '''M05e: email 重複エラー（テナント+取引先名称+メールアドレス）'''
        Partner.objects.create(
            partner_name='A',
            email='dup@example.com',
            tenant=self.tenant,
            create_user=self.user,
            update_user=self.user
        )

        with self.assertRaises(IntegrityError):
            Partner.objects.create(
                partner_name='A',
                email='dup@example.com',
                tenant=self.tenant,
                create_user=self.user,
                update_user=self.user
            )

    # M06 tel_number
    def test_M06(self):
        '''M06: tel_number 正常登録の確認'''
        p = self.create_partner(tel_number='090-1234-5678', partner_name='A', email='tel@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.email, 'tel@example.com')
        self.assertEqual(saved.tel_number, '090-1234-5678')
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M06a(self):
        '''M06a: tel_number 桁数上限（20文字）'''
        tel_number = '1' * 20
        p = self.create_partner(tel_number=tel_number, partner_name='A', email='tel@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.email, 'tel@example.com')
        self.assertEqual(saved.tel_number, tel_number)
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M06b(self):
        '''M06b: tel_number 桁数超過（21文字）'''
        tel_number = '1' * 21
        p = self.create_partner(tel_number=tel_number, partner_name='A', email='tel@example.com')
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_M06c(self):
        '''M06b: tel_number 入力形式エラー'''
        p = Partner(tel_number='090-1234-abc', partner_name='A', email='tel@example.com')
        with self.assertRaises(ValidationError):
            p.full_clean()

    # M07 postal_code
    def test_M07(self):
        '''M07: postal_code 正常登録の確認'''
        p = self.create_partner(postal_code='123-4567', partner_name='A', email='postal@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.email, 'postal@example.com')
        self.assertEqual(saved.postal_code, '123-4567')
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M07a(self):
        '''M07a: postal_code 桁数上限（10文字）'''
        postal_code = '1' * 10
        p = self.create_partner(postal_code=postal_code, partner_name='A', email='postal@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.email, 'postal@example.com')
        self.assertEqual(saved.postal_code, postal_code)
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M07b(self):
        '''M06b: postal_code 桁数超過（11文字）'''
        p = Partner(postal_code='1' * 11, partner_name='A', email='postal@example.com')
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_M07c(self):
        '''M07b: postal_code 入力形式エラー'''
        p = Partner(postal_code='abc-5678', partner_name='A', email='postal@example.com')
        with self.assertRaises(ValidationError):
            p.full_clean()

    # M08 state
    def test_M08(self):
        '''M08: state 正常登録の確認'''
        p = self.create_partner(state='東京都', partner_name='A', email='addr@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.email, 'addr@example.com')
        self.assertEqual(saved.state, '東京都')
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M08a(self):
        '''M08a: postal_code 桁数上限（10文字）'''
        state = 'A' * 10
        p = self.create_partner(state=state, partner_name='A', email='addr@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.email, 'addr@example.com')
        self.assertEqual(saved.state, state)
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M08b(self):
        '''M08b: state 桁数超過（11文字）'''
        state = 'A' * 11
        p = self.create_partner(state=state, partner_name='A', email='addr@example.com')
        with self.assertRaises(ValidationError):
            p.full_clean()

    # M09 city
    def test_M09(self):
        '''M09: city 正常登録の確認'''
        p = self.create_partner(city='千代田区', partner_name='A', email='addr@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.email, 'addr@example.com')
        self.assertEqual(saved.city, '千代田区')
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M09a(self):
        '''M09a: city 桁数上限（50文字）'''
        city = 'A' * 50
        p = self.create_partner(city=city, partner_name='A', email='addr@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.email, 'addr@example.com')
        self.assertEqual(saved.city, city)
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M09b(self):
        '''M09b: city 桁数超過（51文字）'''
        city = 'A' * 51
        p = self.create_partner(city=city, partner_name='A', email='addr@example.com')
        with self.assertRaises(ValidationError):
            p.full_clean()

    # M10 address
    def test_M10(self):
        '''M10: address 正常登録の確認'''
        p = self.create_partner(address='住所1', partner_name='A', email='addr@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.email, 'addr@example.com')
        self.assertEqual(saved.address, '住所1')
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M10a(self):
        '''M10a: address 桁数上限（100文字）'''
        address = 'A' * 100
        p = self.create_partner(address=address, partner_name='A', email='addr@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.email, 'addr@example.com')
        self.assertEqual(saved.address, address)
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M10b(self):
        '''M10b: address 桁数超過（101文字）'''
        address = 'A' * 101
        p = self.create_partner(address=address, partner_name='A', email='addr@example.com')
        with self.assertRaises(ValidationError):
            p.full_clean()

    # M11 address2
    def test_M11(self):
        '''M11: address2 正常登録の確認'''
        p = self.create_partner(address2='住所1', partner_name='A', email='addr@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.email, 'addr@example.com')
        self.assertEqual(saved.address2, '住所1')
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M11a(self):
        '''M11a: address2 桁数上限（150文字）'''
        address2 = 'A' * 150
        p = self.create_partner(address2=address2, partner_name='A', email='addr@example.com')

        # バリデーション通過
        p.full_clean()

        # 保存成功確認
        p.save()
        self.assertIsNotNone(p.pk)

        # DBから取得して値が正しいか確認
        saved = Partner.objects.get(pk=p.pk)
        self.assertEqual(saved.partner_name, 'A')
        self.assertEqual(saved.email, 'addr@example.com')
        self.assertEqual(saved.address2, address2)
        self.assertEqual(saved.tenant, self.tenant)
        self.assertEqual(saved.create_user, self.user)
        self.assertEqual(saved.update_user, self.user)
        self.assertLessEqual(abs((saved.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((saved.updated_at - timezone.now()).total_seconds()), 5)

    def test_M11b(self):
        '''M11b: address2 桁数超過（151文字）'''
        address2 = 'A' * 151
        p = self.create_partner(address2=address2, partner_name='A', email='addr@example.com')
        with self.assertRaises(ValidationError):
            p.full_clean()