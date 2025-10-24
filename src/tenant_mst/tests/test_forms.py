from django.test import TestCase
from tenant_mst.form import TenantEditForm


class TenantEditFormTests(TestCase):
    """TenantEditFormの単体テスト"""

    # ------------------------------------------------------------
    # tenant_name
    # ------------------------------------------------------------
    def test_2_1_1_1(self):
        """正常：テナント名称を100文字以内で入力した場合、有効"""
        form = TenantEditForm(data={
            'tenant_name': '株式会社テスト',
            'representative_name': '代表太郎',
            'contact_email': 'test@example.com',
        })
        self.assertTrue(form.is_valid())

    def test_2_1_2_1(self):
        """異常：テナント名称が空欄の場合エラー"""
        form = TenantEditForm(data={
            'tenant_name': '',
            'representative_name': '代表太郎',
            'contact_email': 'test@example.com',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('この項目は必須です。', form.errors['tenant_name'][0])

    def test_2_1_2_2(self):
        """異常：テナント名称が101文字以上の場合エラー"""
        form = TenantEditForm(data={
            'tenant_name': 'A' * 101,
            'representative_name': '代表太郎',
            'contact_email': 'test@example.com',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('この値は 100 文字以下でなければなりません( 101 文字になっています)。', form.errors['tenant_name'][0])

    # ------------------------------------------------------------
    # representative_name
    # ------------------------------------------------------------
    def test_2_2_1_1(self):
        """正常：代表者名が100文字以内で有効"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': 'A' * 100,
            'contact_email': 'test@example.com',
        })
        self.assertTrue(form.is_valid())

    def test_2_2_2_1(self):
        """異常：代表者名が101文字以上でエラー"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': 'A' * 101,
            'contact_email': 'test@example.com',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('この値は 100 文字以下でなければなりません( 101 文字になっています)。', form.errors['representative_name'][0])

    # ------------------------------------------------------------
    # contact_email
    # ------------------------------------------------------------
    def test_2_3_1_1(self):
        """正常：正しいメール形式で有効"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'valid@example.com',
        })
        self.assertTrue(form.is_valid())

    def test_2_3_2_1(self):
        """異常：不正なメール形式でエラー"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'invalid@@example',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('有効なメールアドレスを入力してください。', form.errors['contact_email'][0])

    # ------------------------------------------------------------
    # contact_tel_number
    # ------------------------------------------------------------
    def test_2_4_1_1(self):
        """正常：数字＋ハイフン形式で有効"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'a@example.com',
            'contact_tel_number': '03-1234-5678'
        })
        self.assertTrue(form.is_valid())

    def test_2_4_1_2(self):
        """正常：空欄でも有効"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'a@example.com',
            'contact_tel_number': ''
        })
        self.assertTrue(form.is_valid())

    def test_2_4_2_1(self):
        """異常：不正文字を含む場合エラー"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'a@example.com',
            'contact_tel_number': '03-12A4-5678'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('数字とハイフンのみ使用できます。', form.errors['contact_tel_number'][0])

    # ------------------------------------------------------------
    # postal_code
    # ------------------------------------------------------------
    def test_2_5_1_1(self):
        """正常：郵便番号「123-4567」で有効"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'a@example.com',
            'postal_code': '123-4567'
        })
        self.assertTrue(form.is_valid())

    def test_2_5_1_2(self):
        """正常：郵便番号「1234567」で有効"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'a@example.com',
            'postal_code': '1234567'
        })
        self.assertTrue(form.is_valid())

    def test_2_5_1_3(self):
        """正常：郵便番号が空欄でも有効"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'a@example.com',
            'postal_code': ''
        })
        self.assertTrue(form.is_valid())

    def test_2_5_2_1(self):
        """異常：不正形式（全角数字）でエラー"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'a@example.com',
            'postal_code': '１２３-４５６７'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('郵便番号の形式が正しくありません。', form.errors['postal_code'][0])

    # ------------------------------------------------------------
    # state
    # ------------------------------------------------------------
    def test_2_6_1_1(self):
        """正常：都道府県10文字以内で有効"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'a@example.com',
            'state': '東京都'
        })
        self.assertTrue(form.is_valid())

    def test_2_6_2_1(self):
        """異常：都道府県が11文字以上でエラー"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'a@example.com',
            'state': 'A' * 11
        })
        self.assertFalse(form.is_valid())
        self.assertIn('この値は 10 文字以下でなければなりません( 11 文字になっています)。', form.errors['state'][0])

    # ------------------------------------------------------------
    # city
    # ------------------------------------------------------------
    def test_2_7_1_1(self):
        """正常：市区町村50文字以内で有効"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'a@example.com',
            'city': '千代田区'
        })
        self.assertTrue(form.is_valid())

    def test_2_7_2_1(self):
        """異常：市区町村が51文字以上でエラー"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'a@example.com',
            'city': 'A' * 51
        })
        self.assertFalse(form.is_valid())
        self.assertIn('この値は 50 文字以下でなければなりません( 51 文字になっています)。', form.errors['city'][0])

    # ------------------------------------------------------------
    # address
    # ------------------------------------------------------------
    def test_2_8_1_1(self):
        """正常：住所100文字以内で有効"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'a@example.com',
            'address': '丸の内1-1-1'
        })
        self.assertTrue(form.is_valid())

    def test_2_8_2_1(self):
        """異常：住所が101文字以上でエラー"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'a@example.com',
            'address': 'A' * 101
        })
        self.assertFalse(form.is_valid())
        self.assertIn('この値は 100 文字以下でなければなりません( 101 文字になっています)。', form.errors['address'][0])

    # ------------------------------------------------------------
    # address2
    # ------------------------------------------------------------
    def test_2_9_1_1(self):
        """正常：住所2が150文字以内で有効"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'a@example.com',
            'address2': 'テストビル3F'
        })
        self.assertTrue(form.is_valid())

    def test_2_9_2_1(self):
        """異常：住所2が151文字以上でエラー"""
        form = TenantEditForm(data={
            'tenant_name': 'テナントA',
            'representative_name': '代表A',
            'contact_email': 'a@example.com',
            'address2': 'A' * 151
        })
        self.assertFalse(form.is_valid())
        self.assertIn('この値は 150 文字以下でなければなりません( 151 文字になっています)。', form.errors['address2'][0])
