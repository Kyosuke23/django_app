from django.test import TestCase
from django.core.exceptions import ValidationError
from ..models import *
import datetime


class TestModelsClass(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_user0 = CustomUser.objects.create(
            username='9'*50
            , password='test@pass'
        )

    def test_01_01_01_01_field_max_length(self):
        '''
        username: 桁数
        正常系
        '''
        test_user = CustomUser(
            username='1'*50
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(len(test_user.username), 50)

    def test_01_01_02_01_field_max_length(self):
        '''
        username: 桁数
        異常系
        '''
        test_user = CustomUser(
            username='1'*51
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_01_02_01_01_field_unique(self):
        '''
        username: ユニーク
        正常系
        '''
        test_user = CustomUser(
            username='2'*50
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.username, '2'*50)

    def test_01_02_02_01_field_unique(self):
        '''
        username: ユニーク
        異常系
        '''
        test_user = CustomUser(
            username='9'*50
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_01_03_01_01_field_ASCIIUsernameValidator(self):
        '''
        username: 使用不可文字
        正常系
        '''
        target_str_list = ['@', '.', '+', '-', '_']
        for str in target_str_list:
            test_user = CustomUser(
                username=str
                , password='test@pass'
            )
            test_user.full_clean()
            self.assertEqual(test_user.username, str)

    def test_01_03_02_01_field_ASCIIUsernameValidator(self):
        '''
        username: 使用不可文字
        異常系
        '''
        target_str_list = ['あ', '!', '#', '$', '%', '^', '&', '*', '(', ')', '=', '¥', '|', '`', '~']
        for str in target_str_list:
            test_user = CustomUser(
                username=str
                , password='test@pass'
            )
            with self.assertRaises(ValidationError):
                test_user.full_clean()

    def test_01_03_02_02_field_Null(self):
        '''
        username: Null
        異常系
        '''
        test_user = CustomUser(
            password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_01_03_02_03_field_Null(self):
        '''
        username: Blank
        異常系
        '''
        test_user = CustomUser(
            username=''
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_02_01_01_01_field_max_length(self):
        '''
        gender: 桁数
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , gender='1'
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.gender, '1')

    def test_02_01_01_02_field_max_length(self):
        '''
        gender: 桁数(Null)
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.gender, None)

    def test_02_01_01_03_field_max_length(self):
        '''
        gender: 桁数(空白)
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , gender=''
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.gender, '')

    def test_02_01_02_01_field_max_length(self):
        '''
        gender: 桁数
        異常系
        '''
        test_user = CustomUser(
            username='test'
            , gender='11'
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_03_01_01_01_field_pattern(self):
        '''
        tel_number: パターン
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , tel_number='12345678900'
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.tel_number, '12345678900')

    def test_03_01_01_02_field_pattern(self):
        '''
        tel_number: パターン
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , tel_number='123'
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.tel_number, '123')

    def test_03_01_02_01_field_pattern(self):
        '''
        tel_number: パターン
        異常系
        '''
        test_user = CustomUser(
            username='test'
            , tel_number='test'
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_03_01_02_02_field_pattern(self):
        '''
        tel_number: パターン
        異常系
        '''
        test_user = CustomUser(
            username='test'
            , tel_number='テスト'
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_03_01_02_03_field_pattern(self):
        '''
        tel_number: パターン
        異常系
        '''
        test_user = CustomUser(
            username='test'
            , tel_number='123-4567-8900'
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_03_02_01_01_field_max_length(self):
        '''
        tel_number: 桁数
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , tel_number='1' * 15
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(len(test_user.tel_number), 15)

    def test_03_02_02_01_field_max_length(self):
        '''
        tel_number: 桁数
        異常系
        '''
        test_user = CustomUser(
            username='test'
            , tel_number='1' * 16
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_03_02_01_01_field_null(self):
        '''
        tel_number: Null
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.tel_number, None)

    def test_03_02_01_02_field_blank(self):
        '''
        tel_number: Blank
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , tel_number=''
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.tel_number, '')

    def test_04_01_01_01_field_pattern(self):
        '''
        postal_cd: パターン
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , postal_cd='1234567'
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.postal_cd, '1234567')

    def test_04_01_02_01_field_pattern(self):
        '''
        postal_cd: パターン
        異常系
        '''
        test_user = CustomUser(
            username='test'
            , postal_cd='test'
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_04_01_02_02_field_pattern(self):
        '''
        postal_cd: パターン
        異常系
        '''
        test_user = CustomUser(
            username='test'
            , postal_cd='テスト'
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_04_01_02_03_field_pattern(self):
        '''
        postal_cd: パターン
        異常系
        '''
        test_user = CustomUser(
            username='test'
            , postal_cd='123-4567'
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_04_02_01_01_field_null(self):
        '''
        postal_cd: Null
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.postal_cd, None)

    def test_04_02_01_02_field_blank(self):
        '''
        postal_cd: Blank
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , postal_cd=''
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.postal_cd, '')

    def test_05_01_01_01_field_max_length(self):
        '''
        state: 桁数
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , state='あ'*5
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(len(test_user.state), 5)

    def test_05_01_01_02_field_max_length(self):
        '''
        state: 桁数
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , state='a'*5
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(len(test_user.state), 5)

    def test_05_01_02_01_field_max_length(self):
        '''
        state: 桁数
        異常系
        '''
        test_user = CustomUser(
            username='test'
            , state='あ'*6
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_05_02_01_01_field_null(self):
        '''
        state: Null
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.state, None)

    def test_05_02_01_02_field_blank(self):
        '''
        state: Blank
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , state=''
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.state, '')

    def test_06_01_01_01_field_max_length(self):
        '''
        city: 桁数
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , city='あ'*255
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(len(test_user.city), 255)

    def test_06_01_01_02_field_max_length(self):
        '''
        city: 桁数
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , city='a'*255
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(len(test_user.city), 255)

    def test_06_01_02_01_field_max_length(self):
        '''
        city: 桁数
        異常系
        '''
        test_user = CustomUser(
            username='test'
            , city='あ'*256
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_06_02_01_01_field_null(self):
        '''
        city: Null
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.city, None)

    def test_06_02_01_02_field_blank(self):
        '''
        city: Blank
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , city=''
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.city, '')

    def test_07_01_01_01_field_max_length(self):
        '''
        address: 桁数
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , address='あ'*255
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(len(test_user.address), 255)

    def test_07_01_01_02_field_max_length(self):
        '''
        address: 桁数
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , address='a'*255
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(len(test_user.address), 255)

    def test_07_01_02_01_field_max_length(self):
        '''
        address: 桁数
        異常系
        '''
        test_user = CustomUser(
            username='test'
            , address='あ'*256
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_07_02_01_01_field_null(self):
        '''
        address: Null
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.address, None)

    def test_07_02_01_02_field_blank(self):
        '''
        address: Blank
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , address=''
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.address, '')

    def test_08_01_01_01_field_max_length(self):
        '''
        address2: 桁数
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , address2='あ'*255
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(len(test_user.address2), 255)

    def test_08_01_01_02_field_max_length(self):
        '''
        address2: 桁数
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , address2='a'*255
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(len(test_user.address2), 255)

    def test_08_01_02_01_field_max_length(self):
        '''
        address2: 桁数
        異常系
        '''
        test_user = CustomUser(
            username='test'
            , address2='あ'*256
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_08_02_01_01_field_null(self):
        '''
        address2: Null
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.address2, None)

    def test_08_02_01_02_field_blank(self):
        '''
        address2: Blank
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , address2=''
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.address2, '')

    def test_09_01_01_01_field_null(self):
        '''
        birthday: Null
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.birthday, None)

    def test_09_01_01_01_field_null(self):
        '''
        birthday: Blank
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , birthday=''
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.birthday, '')

    def test_09_02_01_01_field_date(self):
        '''
        birthday: 日付形式
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , birthday='1988-01-01'
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.birthday, datetime.date(1988, 1, 1))

    def test_09_02_02_01_field_date(self):
        '''
        birthday: 日付形式
        異常系
        '''
        test_user = CustomUser(
            username='test'
            , birthday='test'
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_10_01_01_01_field_max_length(self):
        '''
        privilege: 桁数
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , privilege='1'
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(len(test_user.privilege), 1)

    def test_10_01_02_01_field_max_length(self):
        '''
        privilege: 桁数
        異常系
        '''
        test_user = CustomUser(
            username='test'
            , privilege='11'
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()

    def test_10_02_01_02_field_null(self):
        '''
        privilege: Null
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , password='test@pass'
        )
        test_user.full_clean()
        self.assertEqual(test_user.privilege, '3')

    def test_10_02_01_02_field_blank(self):
        '''
        privilege: Blank
        正常系
        '''
        test_user = CustomUser(
            username='test'
            , privilege=''
            , password='test@pass'
        )
        with self.assertRaises(ValidationError):
            test_user.full_clean()