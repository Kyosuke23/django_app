from django.test import TestCase
from register.forms import UserSearchForm, SignUpForm, ChangePasswordForm, InitialUserForm
from tenant_mst.form import TenantEditForm
from register.models import UserGroup, CustomUser
from tenant_mst.models import Tenant
from django.contrib.auth.models import AnonymousUser


class UserSearchFormTests(TestCase):
    """UserSearchFormの単体テスト"""

    def setUp(self):
        self.tenant = Tenant.objects.create(tenant_name="テストテナント")
        self.group_valid = UserGroup.objects.create(
            group_name="有効グループ",
            tenant=self.tenant,
            is_deleted=False,
        )
        self.group_deleted = UserGroup.objects.create(
            group_name="削除済グループ",
            tenant=self.tenant,
            is_deleted=True,
        )

    def test_1_1_1_1(self):
        """1-1-1-1: search_keyword 255文字以内"""
        form = UserSearchForm(data={'search_keyword': 'A' * 255})
        self.assertTrue(form.is_valid())

    def test_1_1_2_1(self):
        """1-1-2-1: search_keyword 256文字超"""
        form = UserSearchForm(data={'search_keyword': 'A' * 256})
        self.assertFalse(form.is_valid())

    def test_1_2_1_1(self):
        """1-2-1-1: search_username 100文字以内"""
        form = UserSearchForm(data={'search_username': 'A' * 100})
        self.assertTrue(form.is_valid())

    def test_1_2_2_1(self):
        """1-2-2-1: search_username 101文字超"""
        form = UserSearchForm(data={'search_username': 'A' * 101})
        self.assertFalse(form.is_valid())

    def test_1_3_1_1(self):
        """1-3-1-1: search_email 任意文字列"""
        form = UserSearchForm(data={'search_email': 'not-an-email'})
        self.assertTrue(form.is_valid())

    def test_1_4_1_1(self):
        """1-4-1-1: search_gender 空（全件）"""
        form = UserSearchForm(data={'search_gender': ''})
        self.assertTrue(form.is_valid())

    def test_1_4_1_2(self):
        """1-4-1-2: search_gender 有効選択肢"""
        form = UserSearchForm(data={'search_gender': '1'})
        self.assertTrue(form.is_valid())

    def test_1_4_2_1(self):
        """1-4-2-1: search_gender 不正選択肢"""
        form = UserSearchForm(data={'search_gender': 'X'})
        self.assertFalse(form.is_valid())

    def test_1_5_1_1(self):
        """1-5-1-1: search_tel_number 20文字以内"""
        form = UserSearchForm(data={'search_tel_number': '1' * 20})
        self.assertTrue(form.is_valid())

    def test_1_5_2_1(self):
        """1-5-2-1: search_tel_number 21文字超"""
        form = UserSearchForm(data={'search_tel_number': '1' * 21})
        self.assertFalse(form.is_valid())

    def test_1_6_1_1(self):
        """1-6-1-1: search_employment_status 空"""
        form = UserSearchForm(data={'search_employment_status': ''})
        self.assertTrue(form.is_valid())

    def test_1_6_1_2(self):
        """1-6-1-2: search_employment_status 有効選択肢"""
        form = UserSearchForm(data={'search_employment_status': '1'})
        self.assertTrue(form.is_valid())

    def test_1_6_2_1(self):
        """1-6-2-1: search_employment_status 不正選択肢"""
        form = UserSearchForm(data={'search_employment_status': 'X'})
        self.assertFalse(form.is_valid())

    def test_1_7_1_1(self):
        """1-7-1-1: search_privilege 空"""
        form = UserSearchForm(data={'search_privilege': ''})
        self.assertTrue(form.is_valid())

    def test_1_7_1_2(self):
        """1-7-1-2: search_privilege 有効選択肢"""
        form = UserSearchForm(data={'search_privilege': '3'})
        self.assertTrue(form.is_valid())

    def test_1_7_2_1(self):
        """1-7-2-1: search_privilege 不正選択肢"""
        form = UserSearchForm(data={'search_privilege': 'X'})
        self.assertFalse(form.is_valid())

    def test_1_8_1_1(self):
        """1-8-1-1: search_user_group 有効ID"""
        form = UserSearchForm(data={'search_user_group': self.group_valid.id})
        self.assertTrue(form.is_valid())

    def test_1_8_2_1(self):
        """1-8-2-1: search_user_group is_deleted=True"""
        form = UserSearchForm(data={'search_user_group': self.group_deleted.id})
        self.assertFalse(form.is_valid())

    def test_1_8_2_2(self):
        """1-8-2-2: search_user_group 不存在ID"""
        form = UserSearchForm(data={'search_user_group': 999999})
        self.assertFalse(form.is_valid())

    def test_1_9_1_1(self):
        """1-9-1-1: sort username_kana"""
        form = UserSearchForm(data={'sort': 'username_kana'})
        self.assertTrue(form.is_valid())

    def test_1_9_1_2(self):
        """1-9-1-2: sort -username_kana"""
        form = UserSearchForm(data={'sort': '-username_kana'})
        self.assertTrue(form.is_valid())

    def test_1_9_1_3(self):
        """1-9-1-3: sort email"""
        form = UserSearchForm(data={'sort': 'email'})
        self.assertTrue(form.is_valid())

    def test_1_9_1_4(self):
        """1-9-1-4: sort -email"""
        form = UserSearchForm(data={'sort': '-email'})
        self.assertTrue(form.is_valid())

    def test_1_9_2_1(self):
        """1-9-2-1: sort 不正キー"""
        form = UserSearchForm(data={'sort': 'unknown'})
        self.assertFalse(form.is_valid())

    def test_1_10_1_1(self):
        """1-10-1-1: 全項目空"""
        form = UserSearchForm(data={})
        self.assertTrue(form.is_valid())


class SignUpFormTests(TestCase):
    """SignUpFormの単体テスト"""

    def setUp(self):
        self.tenant = Tenant.objects.create(tenant_name='テナントA')
        self.user = CustomUser.objects.create_user(
            username='管理者',
            email='admin@example.com',
            password='pass1234',
            privilege='2',
            tenant=self.tenant,
        )
        self.group1 = UserGroup.objects.create(
            group_name='営業部',
            tenant=self.tenant,
            is_deleted=False
        )
        self.group2 = UserGroup.objects.create(
            group_name='開発部',
            tenant=self.tenant,
            is_deleted=False
        )
        self.group_deleted = UserGroup.objects.create(
            group_name='削除済',
            tenant=self.tenant,
            is_deleted=True
        )

        # 正常データの共通セット
        self.valid_base = {
            'username': '山田太郎',
            'username_kana': 'ヤマダタロウ',
            'email': 'test@example.com',
            'tel_number': '090-1234-5678',
            'gender': '1',
            'employment_status': '1',
            'privilege': '2',
            'groups_custom': [],
        }

    # --------------------------------------------------
    # 2-1: username
    # --------------------------------------------------
    def test_2_1_1_1(self):
        """2-1-1-1: username 正常入力"""
        data = self.valid_base | {'username': '山田太郎'}
        form = SignUpForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_2_1_1_2(self):
        """2-1-1-2: username 正常 100文字"""
        data = self.valid_base | {'username': 'A' * 100}
        form = SignUpForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_2_1_2_1(self):
        """2-1-2-1: username 空欄"""
        data = self.valid_base | {'username': ''}
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())

    def test_2_1_2_2(self):
        """2-1-2-2: username 101文字超"""
        data = self.valid_base | {'username': 'A' * 101}
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())

    # --------------------------------------------------
    # 2-2: username_kana
    # --------------------------------------------------
    def test_2_2_1_1(self):
        """2-2-1-1: username_kana 正常入力"""
        data = self.valid_base | {'username_kana': 'ヤマダタロウ'}
        form = SignUpForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_2_2_1_2(self):
        """2-2-1-2: username_kana 空欄（任意）"""
        data = self.valid_base | {'username_kana': ''}
        form = SignUpForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_2_2_2_1(self):
        """2-2-2-1: username_kana 101文字超"""
        data = self.valid_base | {'username_kana': 'ア' * 101}
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())

    # --------------------------------------------------
    # 2-3: email
    # --------------------------------------------------
    def test_2_3_1_1(self):
        """2-3-1-1: email 正常 Email形式"""
        data = self.valid_base | {'email': 'a@b.com'}
        form = SignUpForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_2_3_2_1(self):
        """2-3-2-1: email 不正Email"""
        data = self.valid_base | {'email': 'invalid'}
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())

    # --------------------------------------------------
    # 2-4: tel_number
    # --------------------------------------------------
    def test_2_4_1_1(self):
        """2-4-1-1: tel_number ハイフン数字"""
        data = self.valid_base | {'tel_number': '090-1234-5678'}
        form = SignUpForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_2_4_2_1(self):
        """2-4-2-1: tel_number 英字含む"""
        data = self.valid_base | {'tel_number': '090A1234'}
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())

    # --------------------------------------------------
    # 2-5: gender
    # --------------------------------------------------
    def test_2_5_1_1(self):
        """2-5-1-1: gender 有効選択肢"""
        data = self.valid_base | {'gender': '1'}
        form = SignUpForm(data=data)
        self.assertTrue(form.is_valid())

    def test_2_5_2_1(self):
        """2-5-2-1: gender 不正選択肢"""
        data = self.valid_base | {'gender': 'X'}
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())

    # --------------------------------------------------
    # 2-6: employment_status
    # --------------------------------------------------
    def test_2_6_1_1(self):
        """2-6-1-1: employment_status 有効選択肢"""
        data = self.valid_base | {'employment_status': '1'}
        form = SignUpForm(data=data)
        self.assertTrue(form.is_valid())

    def test_2_6_2_1(self):
        """2-6-2-1: employment_status 不正選択肢"""
        data = self.valid_base | {'employment_status': 'X'}
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())

    # --------------------------------------------------
    # 2-7: privilege
    # --------------------------------------------------
    def test_2_7_1_1(self):
        """2-7-1-1: privilege 権限制御（user_privilege=2）"""
        form = SignUpForm(user=self.user)
        choices = [c[0] for c in form.fields['privilege'].choices]
        self.assertNotIn('1', choices)

    def test_2_7_2_1(self):
        """2-7-2-1: privilege 不正選択肢"""
        data = self.valid_base | {'privilege': '9'}
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())

    # --------------------------------------------------
    # 2-8: groups_custom
    # --------------------------------------------------
    def test_2_8_1_1(self):
        """2-8-1-1: groups_custom 有効グループ複数選択"""
        data = self.valid_base | {'groups_custom': [self.group1.id, self.group2.id]}
        form = SignUpForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_2_8_2_1(self):
        """2-8-2-1: groups_custom is_deleted=True"""
        data = self.valid_base | {'groups_custom': [self.group_deleted.id]}
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())

    # --------------------------------------------------
    # 2-9: is_updateフラグ
    # --------------------------------------------------
    def test_2_9_1_1(self):
        """2-9-1-1: is_update=True で username 空でも通過"""
        data = self.valid_base | {'username': ''}
        form = SignUpForm(data=data, is_update=True)
        form.is_update = True
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_2_9_1_2(self):
        """2-9-1-2: is_update=True で email 空でも通過"""
        data = self.valid_base | {'email': ''}
        form = SignUpForm(data=data, is_update=True)
        self.assertTrue(form.is_valid(), msg=form.errors)

    # --------------------------------------------------
    # 2-10: clean_username
    # --------------------------------------------------
    def test_2_10_2_1(self):
        """2-10-2-1: clean_username 重複（他ユーザー）"""
        CustomUser.objects.create_user(
            username='重複テスト1',
            email='dup@example.com',
            password='pass',
            tenant=self.tenant,
        )
        data = self.valid_base | {'username': '重複テスト2', 'email': 'dup@example.com'}
        form = SignUpForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('この メールアドレス を持った ユーザー が既に存在します。', str(form.errors))

    # --------------------------------------------------
    # 2-11: placeholder
    # --------------------------------------------------
    def test_2_11_1_1(self):
        """2-11-1-1: username placeholder 設定"""
        form = SignUpForm()
        self.assertEqual(form.fields['username'].widget.attrs.get('placeholder'), '例）山田 太郎')

    def test_2_11_1_2(self):
        """2-11-1-2: username_kana placeholder 設定"""
        form = SignUpForm()
        self.assertEqual(form.fields['username_kana'].widget.attrs.get('placeholder'), '例）ヤマダ タロウ')

    def test_2_11_1_3(self):
        """2-11-1-3: email / tel_number placeholder 設定"""
        form = SignUpForm()
        self.assertEqual(form.fields['email'].widget.attrs.get('placeholder'), '例）info@test.com')
        self.assertEqual(form.fields['tel_number'].widget.attrs.get('placeholder'), '例）090-1234-5678')

    # --------------------------------------------------
    # 2-12: エラー時class
    # --------------------------------------------------
    def test_2_12_1_1(self):
        """2-12-1-1: エラー発生時 is-invalid 付与"""
        data = self.valid_base | {'email': 'invalid'}
        form = SignUpForm(data=data)
        form.is_valid()
        for name, field in form.fields.items():
            if name in form.errors:
                self.assertIn('is-invalid', field.widget.attrs.get('class', ''))


class ChangePasswordFormTests(TestCase):
    """ChangePasswordFormの単体テスト"""

    def setUp(self):
        self.tenant = Tenant.objects.create(tenant_name='テナントA')
        self.user = CustomUser.objects.create_user(
            username='管理者',
            email='admin@example.com',
            password='pass1234',
            privilege='2',
            tenant=self.tenant,
        )

    def test_3_1_1_1(self):
        """3-1-1-1: 初期化時に form-control 付与"""
        form = ChangePasswordForm(user=AnonymousUser())
        for field in form.fields.values():
            self.assertIn('form-control', field.widget.attrs['class'])

    def test_3_1_2_1(self):
        """3-1-2-1: エラー時に is-invalid 付与"""
        form = ChangePasswordForm(
            user=self.user,
            data={'old_password': 'wrongpass', 'new_password1': 'a', 'new_password2': 'b'}
        )
        form.is_valid()
        for error in form.errors:
            self.assertIn('is-invalid', form.fields[error].widget.attrs['class'])


class TenantEditFormTests(TestCase):
    """TenantEditFormの単体テスト"""

    def setUp(self):
        # 正常データ共通
        self.valid_data = {
            'tenant_name': '株式会社テスト',
            'representative_name': '山田太郎',
            'email': 'info@test.com',
            'tel_number': '090-1234-5678',
            'postal_code': '123-4567',
            'state': '東京都',
            'city': '渋谷区',
            'address': '道玄坂1-1-1',
            'address2': 'テストビル3F',
        }

    # --------------------------------------------------
    # 4-1: 全体（正常）
    # --------------------------------------------------
    def test_4_1_1_1(self):
        """4-1-1-1: 全体 正常 全項目正しい"""
        form = TenantEditForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    # --------------------------------------------------
    # 4-2: email（異常）
    # --------------------------------------------------
    def test_4_2_2_1(self):
        """4-2-2-1: email 異常 不正Email"""
        data = self.valid_data | {'email': 'xxx'}
        form = TenantEditForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    # --------------------------------------------------
    # 4-3: tel_number（異常）
    # --------------------------------------------------
    def test_4_3_2_1(self):
        """4-3-2-1: tel_number 異常 英字含む"""
        data = self.valid_data | {'tel_number': '090A1234'}
        form = TenantEditForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('tel_number', form.errors)

    # --------------------------------------------------
    # 4-4: postal_code（異常）
    # --------------------------------------------------
    def test_4_4_2_1(self):
        """4-4-2-1: postal_code 異常 不正形式"""
        data = self.valid_data | {'postal_code': '123=456'}
        form = TenantEditForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('postal_code', form.errors)

    # --------------------------------------------------
    # 4-5: state
    # --------------------------------------------------
    def test_4_5_1_1(self):
        """4-5-1-1: state 正常 10文字"""
        data = self.valid_data | {'state': 'A' * 10}
        form = TenantEditForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_4_5_2_1(self):
        """4-5-2-1: state 異常 11文字超"""
        data = self.valid_data | {'state': 'A' * 11}
        form = TenantEditForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('state', form.errors)

    # --------------------------------------------------
    # 4-6: city
    # --------------------------------------------------
    def test_4_6_1_1(self):
        """4-6-1-1: city 正常 50文字"""
        data = self.valid_data | {'city': 'A' * 50}
        form = TenantEditForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_4_6_2_1(self):
        """4-6-2-1: city 異常 51文字超"""
        data = self.valid_data | {'city': 'A' * 51}
        form = TenantEditForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('city', form.errors)

    # --------------------------------------------------
    # 4-7: address
    # --------------------------------------------------
    def test_4_7_1_1(self):
        """4-7-1-1: address 正常 100文字"""
        data = self.valid_data | {'address': 'A' * 100}
        form = TenantEditForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_4_7_2_1(self):
        """4-7-2-1: address 異常 101文字超"""
        data = self.valid_data | {'address': 'A' * 101}
        form = TenantEditForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('address', form.errors)

    # --------------------------------------------------
    # 4-8: address2
    # --------------------------------------------------
    def test_4_8_1_1(self):
        """4-8-1-1: address2 正常 150文字"""
        data = self.valid_data | {'address2': 'A' * 150}
        form = TenantEditForm(data=data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_4_8_2_1(self):
        """4-8-2-1: address2 異常 151文字超"""
        data = self.valid_data | {'address2': 'A' * 151}
        form = TenantEditForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('address2', form.errors)

class InitialUserFormTests(TestCase):
    """InitialUserForm の単体テスト"""

    def test_5_1_1_1(self):
        """5-1-1-1: company_name 正常 255文字以内"""
        form = InitialUserForm({'company_name': 'A' * 255, 'username': '山田', 'email': 'yamada@example.com'})
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_5_1_2_1(self):
        """5-1-2-1: company_name 異常 256文字超"""
        form = InitialUserForm({'company_name': 'A' * 256, 'username': '山田', 'email': 'yamada@example.com'})
        self.assertFalse(form.is_valid())
        self.assertIn('company_name', form.errors)

    def test_5_2_1_1(self):
        """5-2-1-1: username 正常 100文字以内"""
        form = InitialUserForm({'company_name': '株式会社テスト', 'username': 'A' * 100, 'email': 'user@example.com'})
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_5_2_2_1(self):
        """5-2-2-1: username 異常 101文字超"""
        form = InitialUserForm({'company_name': '株式会社テスト', 'username': 'A' * 101, 'email': 'user@example.com'})
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_5_3_1_1(self):
        """5-3-1-1: email 正常 正しいメール形式"""
        form = InitialUserForm({'company_name': 'テスト株式会社', 'username': '山田太郎', 'email': 'valid@example.com'})
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_5_3_2_1(self):
        """5-3-2-1: email 異常 メール形式不正"""
        form = InitialUserForm({'company_name': 'テスト株式会社', 'username': '山田太郎', 'email': 'invalid-email'})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_5_3_2_2(self):
        """5-3-2-2: email 異常 unique=True により同一Email重複"""
        self.tenant = Tenant.objects.create(tenant_name='テナントA')
        CustomUser.objects.create_user(
                    username='重複ユーザー',
                    email='dup@example.com',
                    password='pass1234',
                    privilege='2',
                    tenant=self.tenant,
                )
        form = InitialUserForm({'company_name': '株式会社テスト', 'username': '山田', 'email': 'dup@example.com'})
        # unique=True はModelFormではなくDB制約で動くため、ここでは同一メールでもエラーにはならない
        # ただし clean_email 実装があれば ValidationError を期待
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('このメールアドレスは既に登録されています。', form.errors['email'][0])

    def test_5_4_1_1(self):
        """5-4-1-1: 全項目 正常 すべて正しい入力"""
        data = {'company_name': '株式会社テスト', 'username': '山田太郎', 'email': 'taro@example.com'}
        form = InitialUserForm(data)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_5_4_2_1(self):
        """5-4-2-1: 全項目 異常 必須項目未入力"""
        form = InitialUserForm({})
        self.assertFalse(form.is_valid())
        self.assertIn('company_name', form.errors)
        self.assertIn('username', form.errors)
        self.assertIn('email', form.errors)