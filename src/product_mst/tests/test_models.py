from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from tenant_mst.models import Tenant
from product_mst.models import Product, ProductCategory
from django.utils import timezone
from decimal import Decimal


class ProductModelTests(TestCase):
    '''Productモデル単体テスト'''

    def setUp(self):
        '''共通データ作成'''
        User = get_user_model()
        self.tenant = Tenant.objects.create(tenant_name='テストテナント')
        self.user = User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='pass',
            tenant=self.tenant
        )
        self.category = ProductCategory.objects.create(
            tenant=self.tenant,
            product_category_name='食品',
            create_user=self.user,
            update_user=self.user
        )

    def create_product(self, **kwargs):
        '''共通フィールド付きProduct生成'''
        defaults = dict(
            tenant=self.tenant,
            create_user=self.user,
            update_user=self.user,
            product_name='テスト商品',
            unit='個',
        )
        defaults.update(kwargs)
        return Product(**defaults)

    # --------------------------
    # product_name
    # --------------------------
    def test_M01(self):
        '''M01: product_name 正常登録'''
        p = self.create_product(product_name='有効商品')
        p.full_clean()
        p.save()
        saved = Product.objects.get(pk=p.pk)
        self.assertEqual(saved.product_name, '有効商品')
        self.assertEqual(saved.unit, '個')
        self.assertEqual(saved.tenant, self.tenant)

    def test_M01a(self):
        '''M01a: product_name 桁数上限（100文字）'''
        p = self.create_product(product_name='A' * 100)
        p.full_clean()
        p.save()
        self.assertEqual(Product.objects.get(pk=p.pk).product_name, 'A' * 100)

    def test_M01b(self):
        '''M01b: product_name 必須エラー'''
        p = self.create_product(product_name='')
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_M01c(self):
        '''M01c: product_name 桁数超過（101文字）'''
        p = self.create_product(product_name='A' * 101)
        with self.assertRaises(ValidationError):
            p.full_clean()

    # --------------------------
    # product_category
    # --------------------------
    def test_M02(self):
        '''M02: product_category 正常登録（カテゴリ紐付け）'''
        p = self.create_product(product_category=self.category)
        p.full_clean()
        p.save()
        saved = Product.objects.get(pk=p.pk)
        self.assertEqual(saved.product_category, self.category)

    def test_M02a(self):
        '''M02a: product_category None許可'''
        p = self.create_product(product_category=None)
        p.full_clean()
        p.save()
        self.assertIsNone(Product.objects.get(pk=p.pk).product_category)

    def test_M02b(self):
        '''M02b: product_category 不正ID'''
        fake = ProductCategory(id=9999)
        p = self.create_product(product_category=fake)
        with self.assertRaises(ValidationError):
            p.full_clean()

    # --------------------------
    # unit
    # --------------------------
    def test_M03(self):
        '''M03: unit 正常登録'''
        p = self.create_product(unit='箱')
        p.full_clean()
        p.save()
        self.assertEqual(Product.objects.get(pk=p.pk).unit, '箱')

    def test_M03a(self):
        '''M03a: unit 桁数上限（20文字）'''
        p = self.create_product(unit='A' * 20)
        p.full_clean()
        p.save()
        self.assertEqual(Product.objects.get(pk=p.pk).unit, 'A' * 20)

    def test_M03b(self):
        '''M03b: unit 桁数超過（21文字）'''
        p = self.create_product(unit='A' * 21)
        with self.assertRaises(ValidationError):
            p.full_clean()

    # --------------------------
    # unit_price
    # --------------------------
    def test_M04(self):
        '''M04: unit_price 正常登録（小数2桁）'''
        p = self.create_product(unit_price=Decimal('1234.56'))
        p.full_clean()
        p.save()
        self.assertEqual(Product.objects.get(pk=p.pk).unit_price, Decimal('1234.56'))

    def test_M04a(self):
        '''M04a: unit_price None許可'''
        p = self.create_product(unit_price=None)
        p.full_clean()
        p.save()
        self.assertIsNone(Product.objects.get(pk=p.pk).unit_price)

    def test_M04b(self):
        '''M04b: unit_price 小数3桁（ValidationError）'''
        p = self.create_product(unit_price=123.456)
        with self.assertRaises(ValidationError):
            p.full_clean()

    # --------------------------
    # description
    # --------------------------
    def test_M05(self):
        '''M05: description 正常登録'''
        p = self.create_product(description='説明文テスト')
        p.full_clean()
        p.save()
        self.assertEqual(Product.objects.get(pk=p.pk).description, '説明文テスト')

    def test_M05a(self):
        '''M05a: description 桁数上限（255文字）'''
        p = self.create_product(description='A' * 255)
        p.full_clean()
        p.save()
        self.assertEqual(len(Product.objects.get(pk=p.pk).description), 255)

    def test_M05b(self):
        '''M05b: description 桁数超過（256文字）'''
        p = self.create_product(description='A' * 256)
        with self.assertRaises(ValidationError):
            p.full_clean()

    # --------------------------
    # unique constraint
    # --------------------------
    def test_M06(self):
        '''M06: 同一テナント内の重複商品名（IntegrityError）'''
        Product.objects.create(
            tenant=self.tenant,
            product_name='重複商品',
            unit='個',
            create_user=self.user,
            update_user=self.user
        )
        with self.assertRaises(ValidationError):
            Product.objects.create(
                tenant=self.tenant,
                product_name='重複商品',
                unit='個',
                create_user=self.user,
                update_user=self.user
            )

    def test_M07(self):
        '''M07: 異なるテナントで同名登録許可'''
        other_tenant = Tenant.objects.create(tenant_name='別テナント')
        Product.objects.create(
            tenant=self.tenant,
            product_name='同名商品',
            unit='個',
            create_user=self.user,
            update_user=self.user
        )
        Product.objects.create(
            tenant=other_tenant,
            product_name='同名商品',
            unit='個',
            create_user=self.user,
            update_user=self.user
        )
        self.assertEqual(Product.objects.filter(product_name='同名商品').count(), 2)

    # --------------------------
    # save() & timestamp
    # --------------------------
    def test_M08(self):
        '''M08: save() により full_clean が実行される'''
        p = self.create_product(product_name='saveテスト')
        p.save()
        self.assertIsNotNone(p.pk)
        self.assertLessEqual(abs((p.created_at - timezone.now()).total_seconds()), 5)
        self.assertLessEqual(abs((p.updated_at - timezone.now()).total_seconds()), 5)
