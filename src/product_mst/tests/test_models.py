from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from datetime import date
from product_mst.models import Product, ProductCategory
from django.contrib.auth import get_user_model


class ProductCategoryModelTest(TestCase):
    def test_str_returns_name(self):
        '''__str__ がカテゴリ名を返す'''
        cat = ProductCategory.objects.create(product_category_name='家電')
        self.assertEqual(str(cat), '家電')

    def test_unique_constraint_on_name(self):
        '''カテゴリ名がユニーク制約に違反すると IntegrityError'''
        ProductCategory.objects.create(product_category_name='食品')
        with self.assertRaises(IntegrityError):
            ProductCategory.objects.create(product_category_name='食品')


class ProductModelTest(TestCase):
    def setUp(self):
        '''共通で使うカテゴリを作成'''
        self.category = ProductCategory.objects.create(product_category_name='文房具')
        self.user = get_user_model().objects.create_user(
            username='tester', password='password123'
        )

    def test_str_representation(self):
        '''__str__ が「商品名(商品コード)」形式で返る'''
        product = Product.objects.create(
            product_code='ABC123',
            product_name='えんぴつ',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            product_category=self.category,
            price=100,
            description='HB',
            create_user=self.user,
            update_user=self.user
        )
        self.assertEqual(str(product), 'えんぴつ(ABC123)')

    def test_get_absolute_url(self):
        '''get_absolute_url が正しいURLを返す'''
        product = Product.objects.create(
            product_code='XYZ999',
            product_name='ノート',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            product_category=self.category,
            create_user=self.user,
            update_user=self.user
        )
        expected_url = reverse('product_mst:product_update', kwargs={'pk': product.pk})
        self.assertEqual(product.get_absolute_url(), expected_url)

    def test_product_code_validation(self):
        '''product_code が正規表現違反なら ValidationError'''
        product = Product(
            product_code='INVALID$',
            product_name='不正コード',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            create_user=self.user,
            update_user=self.user
        )
        with self.assertRaises(ValidationError):
            product.full_clean()  # RegexValidator を発火させる

    def test_unique_constraint_product_code_period(self):
        '''(product_code, start_date, end_date) の複合ユニーク制約'''
        Product.objects.create(
            product_code='DUP001',
            product_name='商品A',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 6, 30),
            product_category=self.category,
            create_user=self.user,
            update_user=self.user
        )
        with self.assertRaises(ValidationError):
            Product.objects.create(
                product_code='DUP001',
                product_name='商品B',
                start_date=date(2025, 1, 1),
                end_date=date(2025, 6, 30),
                product_category=self.category
            )

    def test_end_date_before_start_date_invalid(self):
        '''終了日が開始日より前なら ValidationError'''
        product = Product(
            product_code='ERR001',
            product_name='不正商品',
            start_date=date(2025, 1, 10),
            end_date=date(2025, 1, 5),
            product_category=self.category,
            create_user=self.user,
            update_user=self.user
        )
        with self.assertRaises(ValidationError):
            product.full_clean()  # clean() 内でエラー発生