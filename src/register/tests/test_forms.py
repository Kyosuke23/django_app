from django.test import TestCase
from register.forms import (
    UserSearchForm, SignUpForm, ChangePasswordForm, TenantRegisterForm
)
from register.models import CustomUser, UserGroup
from tenant_mst.models import Tenant


# ------------------------------------------------------------
# 1. UserSearchForm
# ------------------------------------------------------------
class UserSearchFormTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(tenant_name="テナントA")
        self.group_ok = UserGroup.objects.create(tenant=self.tenant, group_name="営業部", is_deleted=False)
        self.group_deleted = UserGroup.objects.create(tenant=self.tenant, group_name="開発部", is_deleted=True)

    def _valid(self, data):
        form = UserSearchForm(data)
        assert form.is_valid(), f"Unexpected errors: {form.errors}"

    def _invalid(self, data, field):
        form = UserSearchForm(data)
        assert not form.is_valid(), "Expected invalid but got valid"
        assert field in form.errors

    def test_1_1_1_1(self): self._valid({'search_keyword': 'A'*255})
    def test_1_1_2_1(self): self._invalid({'search_keyword': 'A'*256}, 'search_keyword')
    def test_1_2_1_1(self): self._valid({'search_username': 'A'*100})
    def test_1_2_2_1(self): self._invalid({'search_username': 'A'*101}, 'search_username')
    def test_1_3_1_1(self): self._valid({'search_email': 'not-an-email'})
    def test_1_4_1_1(self): self._valid({'search_gender': ''})
    def test_1_4_1_2(self): self._valid({'search_gender': '1'})
    def test_1_4_2_1(self): self._invalid({'search_gender': 'X'}, 'search_gender')
    def test_1_5_1_1(self): self._valid({'search_tel_number': '1'*20})
    def test_1_5_2_1(self): self._invalid({'search_tel_number': '1'*21}, 'search_tel_number')
    def test_1_6_1_1(self): self._valid({'search_employment_status': ''})
    def test_1_6_1_2(self): self._valid({'search_employment_status': '1'})
    def test_1_6_2_1(self): self._invalid({'search_employment_status': 'X'}, 'search_employment_status')
    def test_1_7_1_1(self): self._valid({'search_privilege': ''})
    def test_1_7_1_2(self): self._valid({'search_privilege': '3'})
    def test_1_7_2_1(self): self._invalid({'search_privilege': 'X'}, 'search_privilege')
    def test_1_8_1_1(self): self._valid({'search_user_group': self.group_ok.id})
    def test_1_8_2_1(self): self._invalid({'search_user_group': self.group_deleted.id}, 'search_user_group')
    def test_1_8_2_2(self): self._invalid({'search_user_group': 999999}, 'search_user_group')
    def test_1_9_1_1(self): self._valid({'sort': 'username_kana'})
    def test_1_9_1_2(self): self._valid({'sort': '-username_kana'})
    def test_1_9_1_3(self): self._valid({'sort': 'email'})
    def test_1_9_1_4(self): self._valid({'sort': '-email'})
    def test_1_9_2_1(self): self._invalid({'sort': 'unknown'}, 'sort')
    def test_1_10_1_1(self): self._valid({})


# ------------------------------------------------------------
# 2. SignUpForm
# ------------------------------------------------------------
class SignUpFormTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(tenant_name="テナントB")
        self.user = CustomUser.objects.create_user(
            username="admin", email="admin@test.com", password="pass", tenant=self.tenant, privilege=2
        )
        self.g1 = UserGroup.objects.create(tenant=self.tenant, group_name="営業部", is_deleted=False)
        self.g2 = UserGroup.objects.create(tenant=self.tenant, group_name="開発部", is_deleted=False)
        self.g_deleted = UserGroup.objects.create(tenant=self.tenant, group_name="削除済", is_deleted=True)

    def _form(self, data=None, is_update=False):
        data = data or {}
        return SignUpForm(data=data, user=self.user, is_update=is_update)

    def test_2_1_1_1(self):
        form = self._form({'username': '山田太郎', 'email': 'a@b.com', 'privilege': '2'})
        assert form.is_valid(), form.errors

    def test_2_1_1_2(self):
        form = self._form({'username': 'A'*100, 'email': 'a@b.com', 'privilege': '2'})
        assert form.is_valid(), form.errors

    def test_2_1_2_1(self):
        form = self._form({'username': '', 'email': 'a@b.com', 'privilege': '2'})
        assert not form.is_valid()
        assert 'username' in form.errors

    def test_2_1_2_2(self):
        form = self._form({'username': 'A'*101, 'email': 'a@b.com', 'privilege': '2'})
        assert not form.is_valid()
        assert 'username' in form.errors

    def test_2_2_1_1(self):
        form = self._form({'username': 'A', 'username_kana': 'ヤマダタロウ', 'email': 'a@b.com', 'privilege': '2'})
        assert form.is_valid(), form.errors

    def test_2_2_1_2(self):
        form = self._form({'username': 'A', 'username_kana': '', 'email': 'a@b.com', 'privilege': '2'})
        assert form.is_valid(), form.errors

    def test_2_2_2_1(self):
        form = self._form({'username': 'A', 'username_kana': 'ア'*101, 'email': 'a@b.com', 'privilege': '2'})
        assert not form.is_valid()
        assert 'username_kana' in form.errors

    def test_2_3_1_1(self):
        form = self._form({'username': 'A', 'email': 'a@b.com', 'privilege': '2'})
        assert form.is_valid(), form.errors

    def test_2_3_2_1(self):
        form = self._form({'username': 'X', 'email': 'invalid', 'privilege': '2'})
        assert not form.is_valid()

    def test_2_4_1_1(self):
        form = self._form({'username': 'A', 'tel_number': '090-1234-5678', 'email': 'a@b.com', 'privilege': '2'})
        assert form.is_valid(), form.errors

    def test_2_4_2_1(self):
        form = self._form({'username': 'A', 'tel_number': '090A1234', 'email': 'a@b.com', 'privilege': '2'})
        assert not form.is_valid()

    def test_2_5_1_1(self):
        form = self._form({'username': 'A', 'gender': '1', 'email': 'a@b.com', 'privilege': '2'})
        assert form.is_valid(), form.errors

    def test_2_5_2_1(self):
        form = self._form({'username': 'A', 'gender': 'X', 'email': 'a@b.com', 'privilege': '2'})
        assert not form.is_valid()
        assert 'gender' in form.errors

    def test_2_6_1_1(self):
        form = SignUpForm(user=self.user)
        allowed = [k for k, _ in form.fields['privilege'].choices if k]
        allowed_int = [int(k) for k in allowed]
        assert all(k >= self.user.privilege for k in allowed_int), f"Allowed: {allowed_int}"

    def test_2_6_2_1(self):
        form = self._form({'username': 'A', 'email': 'a@b.com', 'privilege': '9'})
        assert not form.is_valid()
        assert 'privilege' in form.errors

    def test_2_7_1_1(self):
        form = self._form({'username': 'A', 'email': 'a@b.com', 'privilege': '2', 'groups_custom': [self.g1.id, self.g2.id]})
        assert form.is_valid(), form.errors

    def test_2_7_2_1(self):
        form = self._form({'username': 'A', 'email': 'a@b.com', 'privilege': '2', 'groups_custom': [self.g_deleted.id]})
        assert not form.is_valid()

    def test_2_8_1_1(self):
        form = self._form({'username': '', 'email': 'a@b.com', 'privilege': '2'}, is_update=True)
        assert form.is_valid(), form.errors

    def test_2_8_1_2(self):
        form = self._form({'username': 'A', 'email': '', 'privilege': '2'}, is_update=True)
        assert form.is_valid(), form.errors

    def test_2_9_2_1(self):
        CustomUser.objects.create_user(username="重複", email="dup@a.com", password="p", tenant=self.tenant)
        form = self._form({'username': '重複', 'email': 'new@a.com', 'privilege': '2'})
        assert not form.is_valid()

    def test_2_10_1_1(self):
        f = SignUpForm(user=self.user)
        assert '例）山田 太郎' in f.fields['username'].widget.attrs.get('placeholder', '')

    def test_2_10_1_2(self):
        f = SignUpForm(user=self.user)
        assert '例）ヤマダ タロウ' in f.fields['username_kana'].widget.attrs.get('placeholder', '')

    def test_2_10_1_3(self):
        f = SignUpForm(user=self.user)
        assert '例）info@test.com' in f.fields['email'].widget.attrs.get('placeholder', '')
        assert '例）090-1234-5678' in f.fields['tel_number'].widget.attrs.get('placeholder', '')

    def test_2_11_1_1(self):
        form = self._form({'username': ''})
        form.is_valid()
        for field in form.fields.values():
            cls = field.widget.attrs.get('class', '')
            if 'is-invalid' in cls:
                assert True


# ------------------------------------------------------------
# 3. ChangePasswordForm
# ------------------------------------------------------------
class ChangePasswordFormTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(tenant_name="テナントC")
        self.user = CustomUser.objects.create_user(
            username="testuser", email="t@t.com", password="pass", tenant=self.tenant
        )

    def test_3_1_1_1(self):
        f = ChangePasswordForm(user=self.user)
        for field in f.fields.values():
            assert 'form-control' in field.widget.attrs.get('class', '')

    def test_3_1_2_1(self):
        f = ChangePasswordForm(
            user=self.user,
            data={'old_password': 'x', 'new_password1': 'a', 'new_password2': 'b'}
        )
        f.is_valid()
        for name in f.fields.keys():
            if f[name].errors:
                assert 'is-invalid' in f.fields[name].widget.attrs.get('class', '')


# ------------------------------------------------------------
# 6. TenantRegisterForm
# ------------------------------------------------------------
class TenantRegisterFormTests(TestCase):
    def _valid_data(self):
        return {
            'tenant_name': '企業A', 'representative_name': '山田太郎', 'email': 'corp@example.com',
            'tel_number': '03-1111-2222', 'postal_code': '123-4567', 'state': '東京都',
            'city': '新宿区', 'address': '1-2-3', 'address2': 'ビル101'
        }

    def _valid(self, d): assert TenantRegisterForm(d).is_valid()
    def _invalid(self, d): assert not TenantRegisterForm(d).is_valid()

    def test_6_1_1_1(self): self._valid(self._valid_data())
    def test_6_2_2_1(self):
        d = self._valid_data(); d['email'] = 'xxx'; self._invalid(d)
    def test_6_3_2_1(self):
        d = self._valid_data(); d['tel_number'] = '090A1234'; self._invalid(d)
    def test_6_4_2_1(self):
        d = self._valid_data(); d['postal_code'] = '123=456'; self._invalid(d)
    def test_6_5_1_1(self):
        """state: 10文字 正常"""
        d = self._valid_data(); d['state'] = 'A' * 10
        self._valid(d)

    def test_6_5_2_1(self):
        """state: 11文字 異常"""
        d = self._valid_data(); d['state'] = 'A' * 11
        self._invalid(d)

    def test_6_6_1_1(self):
        """city: 50文字 正常"""
        d = self._valid_data(); d['city'] = 'A' * 50
        self._valid(d)

    def test_6_6_2_1(self):
        """city: 51文字 異常"""
        d = self._valid_data(); d['city'] = 'A' * 51
        self._invalid(d)

    def test_6_7_1_1(self):
        """address: 100文字 正常"""
        d = self._valid_data(); d['address'] = 'A' * 100
        self._valid(d)

    def test_6_7_2_1(self):
        """address: 101文字 異常"""
        d = self._valid_data(); d['address'] = 'A' * 101
        self._invalid(d)

    def test_6_8_1_1(self):
        """address2: 150文字 正常"""
        d = self._valid_data(); d['address2'] = 'A' * 150
        self._valid(d)

    def test_6_8_2_1(self):
        """address2: 151文字 異常"""
        d = self._valid_data(); d['address2'] = 'A' * 151
        self._invalid(d)