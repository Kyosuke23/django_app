from django.test import TestCase
from django.contrib.auth import get_user_model
from partner_mst.models import Partner
from tenant_mst.models import Tenant
from partner_mst.form import PartnerForm, PartnerSearchForm


class PartnerFormTests(TestCase):
    '''PartnerForm（登録/更新） 単体テスト：Form項目別テスト（Fxx系）'''

    def setUp(self):
        '''テスト用テナント＆ユーザー、正常データの用意'''
        User = get_user_model()
        self.tenant = Tenant.objects.create(tenant_name='テストテナント')
        self.user = User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='pass',
            tenant=self.tenant
        )

        # 初期データ：登録・更新フォーム用
        self.valid_data = {
            'partner_name': '株式会社テスト',
            'partner_name_kana': 'カブシキガイシャテスト',
            'partner_type': 'customer',
            'contact_name': '担当 太郎',
            'email': 'valid@example.com',
            'tel_number': '090-1234-5678',
            'postal_code': '123-4567',
            'state': '東京都',
            'city': '千代田区',
            'address': '霞が関1-1-1',
            'address2': 'テストビル',
        }

        # 初期データ：検索フォーム用
        self.valid_data_sf = {
            'search_keyword': 'テストキーワード',
            'search_partner_name': '株式会社テスト',
            'search_partner_type': 'customer',
            'search_contact_name': '担当 太郎',
            'search_email': 'valid@example.com',
            'search_tel_number': '090-1234-5678',
            'search_postal_code': '123-4567',
            'search_address': '東京都千代田区霞が関1-1-1テストビル',
        }

    # 便利関数：フォームを保存（commit=False→共通項目付与→save）
    def _save_form(self, form):
        self.assertTrue(form.is_valid(), msg=form.errors.as_text())
        instance = form.save(commit=False)
        instance.tenant = self.tenant
        instance.create_user = self.user
        instance.update_user = self.user
        instance.save()
        return instance

    # 便利関数：エラーメッセージが想定いずれかの断片を含むか確認（翻訳差異・DB差異に強い）
    def _assert_err_contains(self, msg: str, candidates: list, where: str):
        if not any(c in msg for c in candidates):
            self.fail(f'[{where}] 想定外のメッセージ: "{msg}" 期待のいずれか: {candidates}')

    # ------------------------------------------------------
    # F01: partner_name
    # ------------------------------------------------------
    def test_F01(self):
        '''F01: partner_name 正常値'''
        form = PartnerForm(data=self.valid_data)
        obj = self._save_form(form)
        self.assertEqual(obj.partner_name, self.valid_data['partner_name'])

    def test_F01a(self):
        '''F01a: partner_name 桁数上限'''
        data = self.valid_data.copy()
        data['partner_name'] = 'A' * 100
        obj = self._save_form(PartnerForm(data=data))
        self.assertEqual(obj.partner_name, 'A' * 100)

    def test_F01b(self):
        '''F01b: partner_name 必須エラー'''
        data = self.valid_data.copy()
        data['partner_name'] = ''
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('partner_name', form.errors)
        self.assertEqual('この項目は必須です。', form.errors['partner_name'][0])

    def test_F01c(self):
        '''F01c: partner_name 桁数超過'''
        data = self.valid_data.copy()
        data['partner_name'] = 'A' * 101
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('partner_name', form.errors)
        self.assertEqual('この値は 100 文字以下でなければなりません( 101 文字になっています)。', form.errors['partner_name'][0])

    # ------------------------------------------------------
    # F02: partner_name_kana
    # ------------------------------------------------------
    def test_F02(self):
        '''F02: partner_name_kana 正常値'''
        form = PartnerForm(data=self.valid_data)
        obj = self._save_form(form)
        self.assertEqual(obj.partner_name_kana, self.valid_data['partner_name_kana'])

    def test_F02a(self):
        '''F02a: partner_name_kana 桁数上限'''
        data = self.valid_data.copy()
        data['partner_name_kana'] = 'ア' * 100
        obj = self._save_form(PartnerForm(data=data))
        self.assertEqual(obj.partner_name_kana, 'ア' * 100)

    def test_F02b(self):
        '''F02c: partner_name_kana 桁数超過'''
        data = self.valid_data.copy()
        data['partner_name_kana'] = 'ア' * 101
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('partner_name_kana', form.errors)
        self.assertEqual('この値は 100 文字以下でなければなりません( 101 文字になっています)。', form.errors['partner_name_kana'][0])

    # ------------------------------------------------------
    # F03: partner_type
    # ------------------------------------------------------
    def test_F03(self):
        '''F03: partner_type 正常値'''
        form = PartnerForm(data=self.valid_data)
        obj = self._save_form(form)
        self.assertEqual(obj.partner_type, self.valid_data['partner_type'])

    def test_F03a(self):
        '''F03b: partner_type 必須エラー'''
        data = self.valid_data.copy()
        data['partner_type'] = ''
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('partner_type', form.errors)
        self.assertEqual('この項目は必須です。', form.errors['partner_type'][0])

    def test_F03b(self):
        '''F03d: partner_type 不正値（choices外）'''
        data = self.valid_data.copy()
        data['partner_type'] = 'invalid'
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('partner_type', form.errors)
        self.assertEqual('正しく選択してください。 invalid は候補にありません。', form.errors['partner_type'][0])

    # ------------------------------------------------------
    # F04: contact_name
    # ------------------------------------------------------
    def test_F04(self):
        '''F04: contact_name 正常値'''
        obj = self._save_form(PartnerForm(data=self.valid_data))
        self.assertEqual(obj.contact_name, self.valid_data['contact_name'])

    def test_F04a(self):
        '''F04a: contact_name 桁数上限'''
        data = self.valid_data.copy()
        data['contact_name'] = 'A' * 50
        obj = self._save_form(PartnerForm(data=data))
        self.assertEqual(obj.contact_name, 'A' * 50)

    def test_F04b(self):
        '''F04c: contact_name 桁数超過'''
        data = self.valid_data.copy()
        data['contact_name'] = 'A' * 51
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('contact_name', form.errors)
        self.assertEqual('この値は 50 文字以下でなければなりません( 51 文字になっています)。', form.errors['contact_name'][0])

    # ------------------------------------------------------
    # F05: email
    # ------------------------------------------------------
    def test_F05(self):
        '''F05: email 正常値'''
        obj = self._save_form(PartnerForm(data=self.valid_data))
        self.assertEqual(obj.email, self.valid_data['email'])

    def test_F05a(self):
        '''F05a: email 桁数上限'''
        data = self.valid_data.copy()
        data['email'] = ('a' * 248) + '@x.com'
        obj = self._save_form(PartnerForm(data=data))
        self.assertEqual(obj.email, data['email'])

    def test_F05b(self):
        '''F05b: email 必須エラー'''
        data = self.valid_data.copy()
        data['email'] = ''
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual('この項目は必須です。', form.errors['email'][0])

    def test_F05c(self):
        '''F05c: email 桁数超過'''
        data = self.valid_data.copy()
        data['email'] = ('a' * 249) + '@x.com'
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual('この値は 254 文字以下でなければなりません( 255 文字になっています)。', form.errors['email'][0])

    def test_F05d(self):
        '''F05d: email 形式不正'''
        data = self.valid_data.copy()
        data['email'] = 'abc@@example'
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual('有効なメールアドレスを入力してください。', form.errors['email'][0])

    def test_F05e(self):
        '''F05e: tenant + partner_name + email の重複（フォームバリデーション）'''
        # 既存レコードを作成
        Partner.objects.create(
            tenant=self.tenant,
            partner_name=self.valid_data['partner_name'],
            partner_name_kana=self.valid_data['partner_name_kana'],
            partner_type=self.valid_data['partner_type'],
            contact_name=self.valid_data['contact_name'],
            email=self.valid_data['email'],
            tel_number=self.valid_data['tel_number'],
            postal_code=self.valid_data['postal_code'],
            state=self.valid_data['state'],
            city=self.valid_data['city'],
            address=self.valid_data['address'],
            address2=self.valid_data['address2'],
            create_user=self.user,
            update_user=self.user,
        )

        # 同一データをフォーム入力
        form = PartnerForm(data=self.valid_data.copy(), initial={'tenant': self.tenant})
        self.assertFalse(form.is_valid())
        self.assertIn('partner_name', form.errors)
        self.assertEqual('同じ取引先名称とメールアドレスの組み合わせが既に登録されています。', form.errors['partner_name'][0])
        self.assertIn('email', form.errors)
        self.assertEqual('同じ取引先名称とメールアドレスの組み合わせが既に登録されています。', form.errors['email'][0])


    # ------------------------------------------------------
    # F06: tel_number
    # ------------------------------------------------------
    def test_F06(self):
        '''F06: tel_number 正常値'''
        obj = self._save_form(PartnerForm(data=self.valid_data))
        self.assertEqual(obj.tel_number, self.valid_data['tel_number'])

    def test_F06a(self):
        '''F06a: tel_number 桁数上限'''
        data = self.valid_data.copy()
        data['tel_number'] = '1' * 20
        obj = self._save_form(PartnerForm(data=data))
        self.assertEqual(obj.tel_number, '1' * 20)

    def test_F06b(self):
        '''F06c: tel_number 桁数超過'''
        data = self.valid_data.copy()
        data['tel_number'] = '1' * 21
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('tel_number', form.errors)
        self.assertEqual('この値は 20 文字以下でなければなりません( 21 文字になっています)。', form.errors['tel_number'][0])

    def test_F06c(self):
        '''F06d: tel_number 形式不正'''
        data = self.valid_data.copy()
        data['tel_number'] = '090-1234-abc'
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('tel_number', form.errors)
        self.assertEqual('数字とハイフンのみ使用できます。', form.errors['tel_number'][0])

    # ------------------------------------------------------
    # F07: postal_code
    # ------------------------------------------------------
    def test_F07(self):
        '''F07: postal_code 正常値'''
        obj = self._save_form(PartnerForm(data=self.valid_data))
        self.assertEqual(obj.postal_code, self.valid_data['postal_code'])

    def test_F07a(self):
        '''F07a: postal_code 桁数上限'''
        data = self.valid_data.copy()
        data['postal_code'] = '1' * 10
        obj = self._save_form(PartnerForm(data=data))
        self.assertEqual(obj.postal_code, '1' * 10)

    def test_F07b(self):
        '''F07c: postal_code 桁数超過'''
        data = self.valid_data.copy()
        data['postal_code'] = '1' * 11
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('postal_code', form.errors)
        self.assertEqual('この値は 10 文字以下でなければなりません( 11 文字になっています)。', form.errors['postal_code'][0])

    def test_F07c(self):
        '''F07d: postal_code 形式不正'''
        data = self.valid_data.copy()
        data['postal_code'] = 'abc-5678'
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('postal_code', form.errors)
        self.assertEqual('郵便番号の形式が正しくありません。', form.errors['postal_code'][0])

    # ------------------------------------------------------
    # F08: state
    # ------------------------------------------------------
    def test_F08(self):
        '''F08: state 正常値'''
        obj = self._save_form(PartnerForm(data=self.valid_data))
        self.assertEqual(obj.state, self.valid_data['state'])

    def test_F08a(self):
        '''F08a: state 桁数上限'''
        data = self.valid_data.copy()
        data['state'] = 'A' * 10
        obj = self._save_form(PartnerForm(data=data))
        self.assertEqual(obj.state, 'A' * 10)

    def test_F08b(self):
        '''F08c: state 桁数超過'''
        data = self.valid_data.copy()
        data['state'] = 'A' * 11
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('state', form.errors)
        self.assertEqual('この値は 10 文字以下でなければなりません( 11 文字になっています)。', form.errors['state'][0])

    # ------------------------------------------------------
    # F09: city
    # ------------------------------------------------------
    def test_F09(self):
        '''F09: city 正常値'''
        obj = self._save_form(PartnerForm(data=self.valid_data))
        self.assertEqual(obj.city, self.valid_data['city'])

    def test_F09a(self):
        '''F09a: city 桁数上限'''
        data = self.valid_data.copy()
        data['city'] = 'A' * 50
        obj = self._save_form(PartnerForm(data=data))
        self.assertEqual(obj.city, 'A' * 50)

    def test_F09b(self):
        '''F09c: city 桁数超過'''
        data = self.valid_data.copy()
        data['city'] = 'A' * 51
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('city', form.errors)
        self.assertEqual('この値は 50 文字以下でなければなりません( 51 文字になっています)。', form.errors['city'][0])

    # ------------------------------------------------------
    # F10: address
    # ------------------------------------------------------
    def test_F10(self):
        '''F10: address 正常値'''
        obj = self._save_form(PartnerForm(data=self.valid_data))
        self.assertEqual(obj.address, self.valid_data['address'])

    def test_F10a(self):
        '''F10a: address 桁数上限'''
        data = self.valid_data.copy()
        data['address'] = 'A' * 100
        obj = self._save_form(PartnerForm(data=data))
        self.assertEqual(obj.address, 'A' * 100)

    def test_F10b(self):
        '''F10c: address 桁数超過'''
        data = self.valid_data.copy()
        data['address'] = 'A' * 101
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('address', form.errors)
        self.assertEqual('この値は 100 文字以下でなければなりません( 101 文字になっています)。', form.errors['address'][0])

    # ------------------------------------------------------
    # F11: address2
    # ------------------------------------------------------
    def test_F11(self):
        '''F11: address2 正常値'''
        obj = self._save_form(PartnerForm(data=self.valid_data))
        self.assertEqual(obj.address2, self.valid_data['address2'])

    def test_F11a(self):
        '''F11a: address2 桁数上限'''
        data = self.valid_data.copy()
        data['address2'] = 'A' * 150
        obj = self._save_form(PartnerForm(data=data))
        self.assertEqual(obj.address2, 'A' * 150)

    def test_F11b(self):
        '''F11c: address2 桁数超過'''
        data = self.valid_data.copy()
        data['address2'] = 'A' * 151
        form = PartnerForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('address2', form.errors)
        self.assertEqual('この値は 150 文字以下でなければなりません( 151 文字になっています)。', form.errors['address2'][0])

    # ------------------------------------------------------
    # SF01: search_keyword
    # ------------------------------------------------------
    def test_SF01(self):
        '''SF01: search_keyword 正常値'''
        form = PartnerSearchForm(data=self.valid_data_sf)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search_keyword'], self.valid_data_sf['search_keyword'])

    def test_SF01a(self):
        '''SF01a: search_keyword 桁数上限'''
        data = self.valid_data_sf.copy()
        data['search_keyword'] = 'A' * 255
        form = PartnerSearchForm(data=self.valid_data_sf)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search_keyword'], self.valid_data_sf['search_keyword'])

    def test_SF01b(self):
        '''SF01b: search_keyword 桁数超過'''
        data = self.valid_data.copy()
        data['search_keyword'] = 'A' * 256
        form = PartnerSearchForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('search_keyword', form.errors)
        self.assertEqual('この値は 255 文字以下でなければなりません( 256 文字になっています)。', form.errors['search_keyword'][0])

    # ------------------------------------------------------
    # SF02: search_partner_name
    # ------------------------------------------------------
    def test_SF02(self):
        '''SF02: search_partner_name 正常値'''
        form = PartnerSearchForm(data=self.valid_data_sf)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search_partner_name'], self.valid_data_sf['search_partner_name'])

    def test_SF02a(self):
        '''SF02a: search_partner_name 桁数上限'''
        data = self.valid_data_sf.copy()
        data['search_partner_name'] = 'A' * 100
        form = PartnerSearchForm(data=self.valid_data_sf)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search_partner_name'], self.valid_data_sf['search_partner_name'])

    def test_SF02b(self):
        '''SF02b: search_partner_name 桁数超過'''
        data = self.valid_data.copy()
        data['search_partner_name'] = 'A' * 101
        form = PartnerSearchForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('search_partner_name', form.errors)
        self.assertEqual('この値は 100 文字以下でなければなりません( 101 文字になっています)。', form.errors['search_partner_name'][0])

    # ------------------------------------------------------
    # SF03: search_partner_type
    # ------------------------------------------------------
    def test_SF03(self):
        '''SF03: search_partner_type 正常値'''
        form = PartnerSearchForm(data=self.valid_data_sf)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search_partner_type'], self.valid_data_sf['search_partner_type'])

    def test_SF03a(self):
        '''SF03a: search_partner_type 未選択'''
        data = self.valid_data_sf.copy()
        data['search_partner_type'] = ''
        form = PartnerSearchForm(data=self.valid_data_sf)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search_partner_type'], self.valid_data_sf['search_partner_type'])

    def test_SF03b(self):
        '''SF03b: search_partner_type 形式不正'''
        data = self.valid_data.copy()
        data['search_partner_type'] = 'invalid'
        form = PartnerSearchForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('search_partner_type', form.errors)
        self.assertEqual('正しく選択してください。 invalid は候補にありません。', form.errors['search_partner_type'][0])

    # ------------------------------------------------------
    # SF04: search_contact_name
    # ------------------------------------------------------
    def test_SF04(self):
        '''SF04: search_contact_name 正常値'''
        form = PartnerSearchForm(data=self.valid_data_sf)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search_contact_name'], self.valid_data_sf['search_contact_name'])

    def test_SF04a(self):
        '''SF04a: search_contact_name 桁数上限'''
        data = self.valid_data_sf.copy()
        data['search_contact_name'] = 'A' * 50
        form = PartnerSearchForm(data=self.valid_data_sf)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search_contact_name'], self.valid_data_sf['search_contact_name'])

    def test_SF04b(self):
        '''SF04b: search_contact_name 桁数超過'''
        data = self.valid_data.copy()
        data['search_contact_name'] = 'A' * 51
        form = PartnerSearchForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('search_contact_name', form.errors)
        self.assertEqual('この値は 50 文字以下でなければなりません( 51 文字になっています)。', form.errors['search_contact_name'][0])

    # ------------------------------------------------------
    # SF05: search_email
    # ------------------------------------------------------
    def test_SF05(self):
        '''SF05: search_email 正常値'''
        form = PartnerSearchForm(data=self.valid_data_sf)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search_email'], self.valid_data_sf['search_email'])

    def test_SF05a(self):
        '''SF05a: search_email 桁数上限'''
        data = self.valid_data_sf.copy()
        data['search_email'] = 'A' * 254
        form = PartnerSearchForm(data=self.valid_data_sf)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search_email'], self.valid_data_sf['search_email'])

    def test_SF05b(self):
        '''SF05b: search_email 桁数超過'''
        data = self.valid_data.copy()
        data['search_email'] = 'A' * 255
        form = PartnerSearchForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('search_email', form.errors)
        self.assertEqual('この値は 254 文字以下でなければなりません( 255 文字になっています)。', form.errors['search_email'][0])

    # ------------------------------------------------------
    # SF06: search_tel_number
    # ------------------------------------------------------
    def test_SF06(self):
        '''SF06: search_tel_number 正常値'''
        form = PartnerSearchForm(data=self.valid_data_sf)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search_tel_number'], self.valid_data_sf['search_tel_number'])

    def test_SF06a(self):
        '''SF06a: search_tel_number 桁数上限'''
        data = self.valid_data_sf.copy()
        data['search_tel_number'] = '1' * 20
        form = PartnerSearchForm(data=self.valid_data_sf)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search_tel_number'], self.valid_data_sf['search_tel_number'])

    def test_SF06b(self):
        '''SF06b: search_tel_number 桁数超過'''
        data = self.valid_data.copy()
        data['search_tel_number'] = '1' * 21
        form = PartnerSearchForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('search_tel_number', form.errors)
        self.assertEqual('この値は 20 文字以下でなければなりません( 21 文字になっています)。', form.errors['search_tel_number'][0])

    # ------------------------------------------------------
    # SF07: search_address
    # ------------------------------------------------------
    def test_SF07(self):
        '''SF07: search_address 正常値'''
        form = PartnerSearchForm(data=self.valid_data_sf)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search_address'], self.valid_data_sf['search_address'])

    def test_SF07a(self):
        '''SF07a: search_address 桁数上限'''
        data = self.valid_data_sf.copy()
        data['search_address'] = 'A' * 255
        form = PartnerSearchForm(data=self.valid_data_sf)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['search_address'], self.valid_data_sf['search_address'])

    def test_SF07b(self):
        '''SF07b: search_address 桁数超過'''
        data = self.valid_data.copy()
        data['search_address'] = 'A' * 256
        form = PartnerSearchForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('search_address', form.errors)
        self.assertEqual('この値は 255 文字以下でなければなりません( 256 文字になっています)。', form.errors['search_address'][0])