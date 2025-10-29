from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date
from register.models import CustomUser, UserGroup
from tenant_mst.models import Tenant


class CustomUserModelTests(TestCase):
    """CustomUserモデルの単体テスト"""

    def setUp(self):
        # テナント作成
        self.tenant = Tenant.objects.create(tenant_name='テストテナント')

        # 共通ユーザー作成
        self.user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass',
            tenant=self.tenant
        )

        # グループ作成
        self.group1 = UserGroup.objects.create(
            group_name='営業部',
            tenant=self.tenant,
            create_user=self.user,
            update_user=self.user
        )
        self.group2 = UserGroup.objects.create(
            group_name='開発部',
            tenant=self.tenant,
            create_user=self.user,
            update_user=self.user
        )

    def create_user(self, **kwargs):
        """保存付きのCustomUser作成"""
        defaults = {
            'username': 'テストユーザー',
            'email': 'test@example.com',
            'password': 'pass1234',
            'tenant': self.tenant,
            'create_user': self.user,
            'update_user': self.user,
        }
        defaults.update(kwargs)
        user = CustomUser(**defaults)
        user.full_clean()
        user.save()
        return user

    def create_user_instance(self, **kwargs):
        """保存しないCustomUser（バリデーション専用）"""
        defaults = {
            'username': 'テストユーザー',
            'email': 'test@example.com',
            'password': 'pass1234',
            'tenant': self.tenant,
            'create_user': self.user,
            'update_user': self.user,
        }
        defaults.update(kwargs)
        return CustomUser(**defaults)

    # 1-1 username
    def test_1_1_1_1(self):
        """1-1-1-1: username 正常 100文字以内で登録できること"""
        user = self.create_user_instance(username='A' * 100)
        user.full_clean()

    def test_1_1_2_1(self):
        """1-1-2-1: username 異常 未入力"""
        user = self.create_user_instance(username='')
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_1_1_2_2(self):
        """1-1-2-2: username 異常 101文字超"""
        user = self.create_user_instance(username='A' * 101)
        with self.assertRaises(ValidationError):
            user.full_clean()

    # 1-2 username_kana
    def test_1_2_1_1(self):
        """1-2-1-1: username_kana 正常 カナ100文字以内"""
        user = self.create_user_instance(username_kana='カ' * 100)
        user.full_clean()

    def test_1_2_1_2(self):
        """1-2-1-2: username_kana 正常 任意項目"""
        user = self.create_user_instance(username_kana='')
        user.full_clean()

    def test_1_2_2_1(self):
        """1-2-2-1: username_kana 異常 101文字超"""
        user = self.create_user_instance(username_kana='カ' * 101)
        with self.assertRaises(ValidationError):
            user.full_clean()

    # 1-3 email
    def test_1_3_1_1(self):
        """1-3-1-1: email 正常 正しい形式"""
        self.create_user(email='valid@example.com')

    def test_1_3_2_1(self):
        """1-3-2-1: email 異常 未入力"""
        user = self.create_user_instance(email='')
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_1_3_2_2(self):
        """1-3-2-2: email 異常 不正形式"""
        user = self.create_user_instance(email='invalidmail')
        with self.assertRaises(ValidationError):
            user.full_clean()

    # 1-4 gender
    def test_1_4_1_1(self):
        """1-4-1-1: gender 正常 choices内"""
        self.create_user(gender='1')

    def test_1_4_2_1(self):
        """1-4-2-1: gender 異常 choices外"""
        user = self.create_user()
        user.gender = 'X'
        with self.assertRaises(ValidationError):
            user.full_clean()

    # 1-5 tel_number
    def test_1_5_1_1(self):
        """1-5-1-1: tel_number 正常 ハイフン付き"""
        user = self.create_user(tel_number='090-1234-5678')
        self.assertEqual(user.tel_number, '090-1234-5678')

    def test_1_5_2_1(self):
        """1-5-2-1: tel_number 異常 不正文字含む"""
        user = self.create_user()
        user.tel_number = '090A1234'
        with self.assertRaises(ValidationError):
            user.full_clean()

    # 1-6 employment_status
    def test_1_6_1_1(self):
        """1-6-1-1: employment_status 正常 choices内"""
        user = self.create_user(employment_status='1')
        self.assertEqual(user.employment_status, '1')

    def test_1_6_2_1(self):
        """1-6-2-1: employment_status 異常 choices外"""
        user = self.create_user()
        user.employment_status = '9'
        with self.assertRaises(ValidationError):
            user.full_clean()

    # 1-7 privilege
    def test_1_7_1_1(self):
        """1-7-1-1: privilege 正常 choices内"""
        user = self.create_user(privilege='3')
        self.assertEqual(user.privilege, '3')

    def test_1_7_2_1(self):
        """1-7-2-1: privilege 異常 choices外"""
        user = self.create_user()
        user.privilege = '9'
        with self.assertRaises(ValidationError):
            user.full_clean()

    # 1-8 groups_custom
    def test_1_8_1_1(self):
        """1-8-1-1: groups_custom 正常 複数登録可"""
        user = self.create_user()
        user.groups_custom.set([self.group1, self.group2])
        self.assertEqual(user.groups_custom.count(), 2)

    # 1-10 group_names_display
    def test_1_9_1_1(self):
        """1-10-1-1: group_names_display 正常 カンマ区切り"""
        user = self.create_user()
        user.groups_custom.set([self.group1, self.group2])
        result = user.group_names_display
        self.assertIn('営業部', result)
        self.assertIn('開発部', result)


class UserGroupModelTests(TestCase):
    """UserGroupモデルの単体テスト"""

    def setUp(self):
        self.tenant = Tenant.objects.create(tenant_name='テストテナント')
        self.user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass',
            tenant=self.tenant
        )

    def test_2_1_1_1(self):
        """2-1-1-1: group_name 正常 100文字以内"""
        group = UserGroup(
            group_name='営業部',
            tenant=self.tenant,
            create_user=self.user,
            update_user=self.user
        )
        group.full_clean()
        group.save()
        self.assertEqual(UserGroup.objects.count(), 1)

    def test_2_1_2_1(self):
        """2-1-2-1: group_name 異常 未入力"""
        group = UserGroup(
            group_name='',
            tenant=self.tenant,
            create_user=self.user,
            update_user=self.user
        )
        with self.assertRaises(ValidationError):
            group.full_clean()

    def test_2_1_2_2(self):
        """2-1-2-2: group_name 異常 101文字超"""
        group = UserGroup(
            group_name='A' * 101,
            tenant=self.tenant,
            create_user=self.user,
            update_user=self.user
        )
        with self.assertRaises(ValidationError):
            group.full_clean()

    def test_2_1_2_3(self):
        """2-1-2-3: group_name 異常 一意制約"""
        UserGroup.objects.create(
            group_name='営業部',
            tenant=self.tenant,
            create_user=self.user,
            update_user=self.user
        )
        with self.assertRaises(IntegrityError):
            UserGroup.objects.create(
                group_name='営業部',
                tenant=self.tenant,
                create_user=self.user,
                update_user=self.user
            )
