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

    # username
    def test_1_1_1_1(self):
        user = self.create_user_instance(username='A' * 100)
        user.full_clean()
        self.assertTrue(True)

    def test_1_1_2_1(self):
        user = self.create_user_instance(username='')
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_1_1_2_2(self):
        user = self.create_user_instance(username='A' * 101)
        with self.assertRaises(ValidationError):
            user.full_clean()

    # username_kana
    def test_1_2_1_1(self):
        user = self.create_user_instance(username_kana='カ' * 100)
        user.full_clean()

    def test_1_2_1_2(self):
        user = self.create_user_instance(username_kana='')
        user.full_clean()

    def test_1_2_2_1(self):
        user = self.create_user_instance(username_kana='カ' * 101)
        with self.assertRaises(ValidationError):
            user.full_clean()

    # email
    def test_1_3_1_1(self):
        self.create_user(email='valid@example.com')

    def test_1_3_2_1(self):
        user = self.create_user_instance(email='')
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_1_3_2_2(self):
        user = self.create_user_instance(email='invalidmail')
        with self.assertRaises(ValidationError):
            user.full_clean()

    # gender
    def test_1_4_1_1(self):
        self.create_user(gender='1')

    def test_1_4_2_1(self):
        user = self.create_user()
        user.gender = 'X'
        with self.assertRaises(ValidationError):
            user.full_clean()

    # tel_number
    def test_1_5_1_1(self):
        user = self.create_user(tel_number='090-1234-5678')
        self.assertEqual(user.tel_number, '090-1234-5678')

    def test_1_5_2_1(self):
        user = self.create_user()
        user.tel_number = '090A1234'
        with self.assertRaises(ValidationError):
            user.full_clean()

    # postal_code
    def test_1_6_1_1(self):
        user = self.create_user(postal_code='123-4567')
        self.assertEqual(user.postal_code, '123-4567')

    def test_1_6_1_2(self):
        user = self.create_user(postal_code='1234567')
        self.assertEqual(user.postal_code, '1234567')

    def test_1_6_2_1(self):
        user = self.create_user_instance(postal_code='123-456')
        with self.assertRaises(ValidationError):
            user.full_clean()

    # state / city / address / address2
    def test_1_7_2_1(self):
        user = self.create_user_instance(state='A' * 11)
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_1_8_2_1(self):
        user = self.create_user_instance(city='A' * 51)
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_1_9_2_1(self):
        user = self.create_user_instance(address='A' * 101)
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_1_10_2_1(self):
        user = self.create_user_instance(address2='A' * 151)
        with self.assertRaises(ValidationError):
            user.full_clean()

    # birthday
    def test_1_11_1_1(self):
        user = self.create_user(birthday='1990-01-01')
        self.assertEqual(str(user.birthday), '1990-01-01')

    def test_1_11_2_1(self):
        user = self.create_user_instance(birthday='invalid-date')
        with self.assertRaises(ValidationError):
            user.full_clean()

    # employment_status / end_date
    def test_1_12_1_1(self):
        user = self.create_user(employment_status='1')
        self.assertEqual(user.employment_status, '1')

    def test_1_12_2_1(self):
        user = self.create_user()
        user.employment_status = '9'
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_1_13_1_1(self):
        user = self.create_user(employment_end_date='2025-01-01')
        self.assertEqual(str(user.employment_end_date), '2025-01-01')

    # privilege
    def test_1_14_2_1(self):
        user = self.create_user()
        user.privilege = '9'
        with self.assertRaises(ValidationError):
            user.full_clean()

    # groups_custom
    def test_1_15_1_1(self):
        user = self.create_user()
        user.groups_custom.set([self.group1, self.group2])
        self.assertEqual(user.groups_custom.count(), 2)

    # is_employed property
    def test_1_16_1_1(self):
        user = self.create_user(employment_status='1', employment_end_date=None)
        self.assertTrue(user.is_employed)

    def test_1_16_1_2(self):
        user = self.create_user(employment_status='1', employment_end_date=date(2024, 1, 1))
        self.assertFalse(user.is_employed)

    # group_names_display
    def test_1_17_1_1(self):
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
        group = UserGroup(
            group_name='',
            tenant=self.tenant,
            create_user=self.user,
            update_user=self.user
        )
        with self.assertRaises(ValidationError):
            group.full_clean()

    def test_2_1_2_2(self):
        group = UserGroup(
            group_name='A' * 101,
            tenant=self.tenant,
            create_user=self.user,
            update_user=self.user
        )
        with self.assertRaises(ValidationError):
            group.full_clean()

    def test_2_1_2_3(self):
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
